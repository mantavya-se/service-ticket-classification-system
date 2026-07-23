import psycopg2
import os
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from rag.build_chunks import build_embeddings

load_dotenv()

chunks = build_embeddings()

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_vdb (
        id SERIAL PRIMARY KEY,
        chunk_id TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT,
        title TEXT,
        category TEXT,
        subcategory TEXT,
        section TEXT,
        chunk_index INTEGER,
        chunk_text TEXT NOT NULL,
        embedding vector(384)
    )
    """)

    for row in chunks:
        cur.execute("""
        INSERT INTO knowledge_vdb(
            chunk_id, file_name, file_path,
            title, category, subcategory,
            section, chunk_index, chunk_text,
            embedding
        )
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id) DO UPDATE SET
            file_name = EXCLUDED.file_name,
            file_path = EXCLUDED.file_path,
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            subcategory = EXCLUDED.subcategory,
            section = EXCLUDED.section,
            chunk_index = EXCLUDED.chunk_index,
            chunk_text = EXCLUDED.chunk_text,
            embedding = EXCLUDED.embedding;
        """, (
            row["chunk_id"],
            row["file_name"],
            str(row["file_path"]),
            row["title"],
            row["category"],
            row["subcategory"],
            row["section"],
            int(row["chunk_index"]),
            row["chunk_text"],
            row["embedding"]
        ))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        subcategory TEXT NOT NULL,
        priority TEXT NOT NULL
            CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
        description TEXT,
        predicted_category TEXT NOT NULL,
        predicted_confidence DOUBLE PRECISION,
        confirmed_category TEXT,
        source TEXT NOT NULL DEFAULT 'Production',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMPTZ,
        used_for_training BOOLEAN DEFAULT FALSE
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

except Exception as e:
    print("Connection Failed:")
    print(e)