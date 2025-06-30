import pymysql
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import ollama
from sentence_transformers import SentenceTransformer, util


def qeury_database(query, k):

    if k is None:
        k = 5

    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    # Step 1: Encode query
    query_embedding = np.array(embedder.encode(query)).reshape(1, -1)

    # Step 2: Connect to MySQL
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="toth",
        port=3306
    )
    cur = conn.cursor()

    # Step 3: Fetch all documents and their embeddings
    cur.execute("SELECT content, embedding, created_at, time_of_record, teacher_name, teacher_subject, student_year, student_room FROM documents")
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


def gen_response(prompt, k):

    retrived_docs = qeury_database(prompt, k)

    context = "\n".join(
        [f"Content: {doc[1]}\nผู้สอน: {doc[4]} ({doc[5]})\nเวลาที่สอน/บันทึก: {doc[2]} {doc[3]}" for doc in retrived_docs])

    prompt_to_ai = f"""Use the following context to answer the question.\nContext : {context}\n\nQuestion : {prompt}"""

    response = ollama.chat(
        model="phi4-mini",
        messages=[
            {"role": "system", "content": "You are a student assistant who will summerize context from reccording class and answer shortly for less complicated."},
            {"role": "user", "content": prompt_to_ai}
        ]
    )

    print("context:", context)
    return response['message']['content']
