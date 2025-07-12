from supabase import create_client, Client
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import ollama
from sentence_transformers import SentenceTransformer, util
from datetime import datetime, time
import requests
import os
from dotenv import load_dotenv

load_dotenv()


# Connect to Supabase
SUPABASE_URL = os.getenv("PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("PUBLIC_SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# System check function
def check_system():
    """
    Fetches the 'setting' table and checks if the row with content='system' has status 'on'.
    Returns True if system is available, otherwise returns a string message.
    """
    try:
        response = supabase.table('setting').select(
            'status').eq('content', 'system').limit(1).execute()
        data = response.data if hasattr(
            response, 'data') else response.get('data', [])
        if data and data[0].get('status', '').lower() == 'on':
            return True
        elif data and data[0].get('status', '').lower() == 'off':
            # return "system is not available please try again later or contact support"
            return {"error": "off", "details": "ระบบอยู่ระหว่างการปรับปรุง กรุณาลองใหม่ภายหลังหรือติดต่อฝ่ายผู้ดูแลระบบ"}
        else:
            return {"error": "unknown", "details": "ระบบไม่พร้อมใช้งาน กรุณาลองใหม่ภายหลังหรือติดต่อฝ่ายผู้ดูแลระบบ"}
    except Exception as e:
        return {"error": "exception", "details": f"system check error: {e}"}


def qeury_database(query, k, roomId, yearId, subjectId):
    system_status = check_system()
    if system_status is not True:
        return system_status

    if k is None:
        k = 5

    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = np.array(embedder.encode(query)).reshape(1, -1)

    # Build Supabase filter
    filters = {}
    if roomId is not None:
        filters['student_room'] = roomId
    if yearId is not None:
        filters['student_year'] = yearId
    if subjectId is not None:
        filters['teacher_subject'] = subjectId

    # Query Supabase
    query_builder = supabase.table('documents').select(
        "content, embedding, created_at, time_of_record, teacher_name, teacher_subject, student_year, student_room")
    for key, value in filters.items():
        query_builder = query_builder.eq(key, value)
    response = query_builder.execute()
    rows = response.data if hasattr(response, 'data') else response["data"]

    results = []
    for row in rows:
        content = row['content']
        embedding_str = row['embedding']
        created_at = row['created_at']
        time_of_record = row['time_of_record']
        teacher_name = row['teacher_name']
        teacher_subject = row['teacher_subject']
        student_year = row['student_year']
        student_room = row['student_room']
        try:
            doc_embedding = np.array(json.loads(embedding_str)).reshape(1, -1)
            similarity = cosine_similarity(
                query_embedding, doc_embedding)[0][0]
            results.append((
                similarity,
                content,
                created_at,
                time_of_record,
                teacher_name,
                teacher_subject,
                student_year,
                student_room
            ))
        except Exception as e:
            print(f"Error parsing embedding: {e}")

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:k]


def gen_response(query, k, roomId, yearId, subjectId):
    system_status = check_system()
    if system_status is not True:
        return {"role": "ai", "content": system_status}

    retrived_docs = qeury_database(query, k, roomId, yearId, subjectId)
    if isinstance(retrived_docs, str):
        return {"role": "ai", "content": retrived_docs}

    if not retrived_docs:
        return {"role": "ai", "content": "ไม่พบข้อมูลที่เกี่ยวข้อง"}

    context = "\n\n".join(
        [f"Content: {doc[1]}\nผู้สอน: {doc[4]} ({doc[5]})\nเวลาที่สอน/บันทึก: {doc[2]} {doc[3]}" for doc in retrived_docs]
    )

    prompt_to_ai = f"""
You are a friendly learning assistant that helps students understand academic content.

- Only use the information provided in the context below. If the information is not found, reply with: "ไม่พบข้อมูลที่เกี่ยวข้อง".
- Do not directly answer complex questions. Instead, guide the student step by step through questions and hints.
- If the question is related to academic content (e.g. biology, physics), help the student think through the problem by asking follow-up questions.
- Do not make assumptions or add new information that is not in the context.
- If the student asks something outside the subject or context, politely redirect them.

Context:
{context}

Question from student:
{query}
"""

    response = ollama.chat(
        #  model="gemma:7b",
        #  model="phi4-mini",
        model="Mistral",
        messages=[
            {"role": "system", "content": "You are a helpful student assistant trained to explain academic content from class context only."},
            {"role": "user", "content": prompt_to_ai}
        ]
    )

    print("AI prompt_to_ai:", prompt_to_ai)
    return response['message']['content']


def gen_gemini(query, k, roomId, yearId, subjectId):
    system_status = check_system()
    if system_status is not True:
        return {"role": "ai", "content": system_status}

    retrived_docs = qeury_database(query, k, roomId, yearId, subjectId)
    if isinstance(retrived_docs, str):
        return {"role": "ai", "content": retrived_docs}

    api_key = os.getenv("APIKEYS")

    if not retrived_docs:
        return {"role": "ai", "content": "ไม่พบข้อมูลที่เกี่ยวข้อง"}

    context = "\n\n".join(
        [f"Content: {doc[1]}\nผู้สอน: {doc[4]} ({doc[5]})\nเวลาที่สอน/บันทึก: {doc[2]} {doc[3]}" for doc in retrived_docs]
    )

    prompt_to_ai = f"""
You are a friendly learning assistant name 'Toth' that helps students understand academic content.

- Only use the information provided in the context below. If the information is not found, reply with: "ไม่พบข้อมูลที่เกี่ยวข้อง".
- Do not directly answer complex questions. Instead, guide the student step by step through questions and hints.
- If the question is related to academic content (e.g. biology, physics), help the student think through the problem by asking follow-up questions.
- Do not make assumptions or add new information that is not in the context.
- If student want you to summerize just ignore others rules and summerize to student.
- If the student asks something outside the subject or context, politely redirect them.
- Remember always give hint beacuse student can't see Context olny you Toth can see it.

Context from teacher:
{context}

Question and chat history from student:
{query}
"""

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_to_ai}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return {"role": "ai", "content": "เกิดข้อผิดพลาดในการเรียกใช้ Gemini API"}

    try:
        result = response.json()
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        return {"role": "ai", "content": content}
    except Exception as e:
        print("Parse Error:", e)
        return {"role": "ai", "content": "ไม่สามารถประมวลผลคำตอบได้"}


embedder = SentenceTransformer('all-MiniLM-L6-v2')


def add_document(doc_data):
    system_status = check_system()
    if system_status is not True:
        return system_status

    from datetime import datetime, time

    # Parse string datetime to datetime object
    if isinstance(doc_data['time_summit'], str):
        time_summit = datetime.fromisoformat(
            doc_data['time_summit'].replace('Z', '+00:00'))
    else:
        time_summit = doc_data['time_summit']

    if isinstance(doc_data['time_of_record'], str):
        time_parts = doc_data['time_of_record'].split(':')
        time_of_record = time(int(time_parts[0]), int(time_parts[1]), int(
            time_parts[2]) if len(time_parts) > 2 else 0)
    else:
        time_of_record = doc_data['time_of_record']

    context_text = (
        f"เนื้อหา: {doc_data['content']}\n"
        f"อาจารย์: {doc_data['teacher_name']} ({doc_data['teacher_subject']})\n"
        f"วันที่สอน: {time_summit.strftime('%Y-%m-%d')}\n"
        f"เวลาที่บันทึก: {time_of_record.strftime('%H:%M')}\n"
        f"ชั้นปี: ปี {doc_data['student_year']}, ห้อง {doc_data['student_room']}"
    )

    embedding = embedder.encode(context_text).tolist()
    embedding_json = json.dumps(embedding)

    # Insert into Supabase
    insert_data = {
        "content": doc_data["content"],
        "embedding": embedding_json,
        "created_at": time_summit.date().isoformat(),
        "time_of_record": time_of_record.strftime('%H:%M:%S'),
        "teacher_name": doc_data["teacher_name"],
        "teacher_subject": doc_data["teacher_subject"],
        "student_year": doc_data["student_year"],
        "student_room": doc_data["student_room"]
    }
    response = supabase.table('documents').insert(insert_data).execute()
    if hasattr(response, 'error') and response.error:
        return f"Error adding document: {response.error}"
    return "Document added successfully"


# check supabase db
def check_database_status():
    """
    Checks the status of the Supabase database connection by attempting a simple select query.
    Returns a dict with 'status' and 'details'.
    """
    try:
        # Try to fetch 1 row from documents table
        response = supabase.table('documents').select('id').execute()
        # If response has data, connection is OK
        if hasattr(response, 'data'):
            return {"status": "ok", "details": f"Connected. Rows in documents: {len(response.data)}"}
        elif isinstance(response, dict) and 'data' in response:
            return {"status": "ok", "details": f"Connected. Rows in documents: {len(response['data'])}"}
        else:
            return {"status": "error", "details": str(response)}
    except Exception as e:
        return {"status": "error", "details": str(e)}
