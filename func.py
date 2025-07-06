import pymysql
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import ollama
from sentence_transformers import SentenceTransformer, util
from datetime import datetime, time

# Step 2: Connect to MySQL
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="toth",
    port=3306
)
cur = conn.cursor()


def qeury_database(query, k, roomId, yearId, subjectId):

    if k is None:
        k = 5

    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    # Step 1: Encode query
    query_embedding = np.array(embedder.encode(query)).reshape(1, -1)

    # Step 3: Fetch filtered documents and their embeddings
    where_conditions = []
    params = []

    if roomId is not None:
        where_conditions.append("student_room = %s")
        params.append(roomId)

    if yearId is not None:
        where_conditions.append("student_year = %s")
        params.append(yearId)

    if subjectId is not None:
        where_conditions.append("teacher_subject = %s")
        params.append(subjectId)

    base_query = "SELECT content, embedding, created_at, time_of_record, teacher_name, teacher_subject, student_year, student_room FROM documents"

    if where_conditions:
        query_sql = base_query + " WHERE " + " AND ".join(where_conditions)
        cur.execute(query_sql, params)
    else:
        cur.execute(base_query)

    rows = cur.fetchall()

    results = []

    for row in rows:
        content, embedding_str, created_at, time_of_record, teacher_name, teacher_subject, student_year, student_room = row

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

    # Step 4: Sort results by similarity score (descending)
    results.sort(key=lambda x: x[0], reverse=True)

    # Step 5: Return top k results
    return results[:k]


def gen_response(query, k, roomId, yearId, subjectId):
    retrived_docs = qeury_database(query, k, roomId, yearId, subjectId)
    
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



cur = conn.cursor()

embedder = SentenceTransformer('all-MiniLM-L6-v2')


def add_document(doc_data):
    from datetime import datetime, time

    # Parse string datetime to datetime object
    if isinstance(doc_data['time_summit'], str):
        # Parse ISO format string to datetime object
        time_summit = datetime.fromisoformat(
            doc_data['time_summit'].replace('Z', '+00:00'))
    else:
        time_summit = doc_data['time_summit']

    # Parse string time to time object
    if isinstance(doc_data['time_of_record'], str):
        # Parse time string (HH:MM:SS format)
        time_parts = doc_data['time_of_record'].split(':')
        time_of_record = time(int(time_parts[0]), int(time_parts[1]), int(
            time_parts[2]) if len(time_parts) > 2 else 0)
    else:
        time_of_record = doc_data['time_of_record']

    # Step 1: Build context-rich text to embed
    context_text = (
        f"เนื้อหา: {doc_data['content']}\n"
        f"อาจารย์: {doc_data['teacher_name']} ({doc_data['teacher_subject']})\n"
        f"วันที่สอน: {time_summit.strftime('%Y-%m-%d')}\n"
        f"เวลาที่บันทึก: {time_of_record.strftime('%H:%M')}\n"
        f"ชั้นปี: ปี {doc_data['student_year']}, ห้อง {doc_data['student_room']}"
    )

    # Step 2: Create embedding from this full context
    embedding = embedder.encode(context_text).tolist()
    embedding_json = json.dumps(embedding)

    # Step 3: Save only original fields (use the parsed datetime objects)
    cur.execute(
        """
        INSERT INTO `documents` 
        (`content`, `embedding`, `created_at`, `time_of_record`, `teacher_name`, `teacher_subject`, `student_year`, `student_room`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            doc_data["content"],
            embedding_json,
            time_summit.date(),  # Convert to date for MySQL
            time_of_record,
            doc_data["teacher_name"],
            doc_data["teacher_subject"],
            doc_data["student_year"],
            doc_data["student_room"]
        )
    )
    conn.commit()
    
    return "Document added successfully"
