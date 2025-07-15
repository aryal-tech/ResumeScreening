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
    conn = get_connection()
    cursor = conn.cursor()

    hashed_text = hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()

    try:
        cursor.execute("""
            INSERT INTO documents (file_name, type, raw_text, cleaned_text, hashed_text)
            VALUES (%s, %s, %s, %s, %s)
        """, (file_name, doc_type, raw_text, cleaned_text, hashed_text))
        conn.commit()
        print(f"{doc_type.capitalize()} document inserted successfully.")
    except mysql.connector.errors.IntegrityError:
        print(f"Duplicate {doc_type} ignored (same hashed_text).")
    finally:
        cursor.close()
        conn.close()
    