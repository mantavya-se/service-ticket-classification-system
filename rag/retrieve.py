from sentence_transformers import SentenceTransformer
import psycopg2
import os
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()

MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

def vectorize(test: str):
    return model.encode(test, normalize_embeddings=True)

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def retrieve(text: str, limit: int = 3):
    embedding = vectorize(text)

    cur = None 
    conn = None

    try:
        conn = get_connection()
        register_vector(conn)
        cur = conn.cursor()

        cur.execute("""
        SELECT 
            file_name, 
            category, 
            subcategory, 
            section,
            chunk_text,
            embedding <=> %s AS distance
        FROM knowledge_vdb
        ORDER BY distance
        LIMIT %s;
        """, (embedding, limit))

        rows = cur.fetchall()

        return [
            {
                "file_name": row[0],
                "category": row[1],
                "subcategory": row[2],
                "section": row[3],
                "chunk_text": row[4],
                "distance": float(row[5]),
                "similarity": float(1 - row[5]),
            }
            for row in rows
        ]

    except Exception:
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()