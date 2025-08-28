import mysql.connector
import hashlib

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="resume_screener"
    )

def insert_document(file_name, doc_type, raw_text, cleaned_text):
    hashed_text = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

    # Check if document with this hash already exists
    if document_exists(hashed_text):
        print(f"Document '{file_name}' already exists in DB. Skipping insert.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO documents (file_name, type, raw_text, cleaned_text, hashed_text)
            VALUES (%s, %s, %s, %s, %s)
        """, (file_name, doc_type, raw_text, cleaned_text, hashed_text))
        conn.commit()
        print(f"{doc_type.capitalize()} document '{file_name}' inserted successfully.")
    except mysql.connector.Error as err:
        print(f"Error inserting document '{file_name}':", err)
    finally:
        cursor.close()
        conn.close()

def document_exists(hashed_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM documents WHERE hashed_text = %s", (hashed_text,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def get_document_by_hash(hashed_text):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT file_name, type, raw_text, cleaned_text, hashed_text
        FROM documents
        WHERE hashed_text = %s
    """, (hashed_text,))
    doc = cursor.fetchone()
    conn.close()
    return doc
