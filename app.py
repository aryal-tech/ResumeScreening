from flask import Flask, render_template, request
from pathlib import Path
import hashlib

from core.extract import extract_text
from core.preprocess import preprocess_text
from database.db_connect import get_connection, insert_document

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
RESUMES_FOLDER = UPLOAD_FOLDER / "resumes"
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESUMES_FOLDER.mkdir(parents=True, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []

    if request.method == 'POST':
        # Save Job Description
        jd_file = request.files['jd_file']
        jd_path = UPLOAD_FOLDER / "job_description.pdf"
        jd_file.save(jd_path)

        # Extract, clean, and insert JD into DB
        jd_text = extract_text(jd_path)
        jd_cleaned = preprocess_text(jd_text)
        insert_document("job_description.pdf", "job", jd_text, jd_cleaned)

        # Process Resumes
        resume_files = request.files.getlist('resume_files')
        seen_hashes = {}  # Map hash → filename in current batch

        for resume_file in resume_files:
            filename = resume_file.filename
            resume_path = RESUMES_FOLDER / filename
            resume_file.save(resume_path)

            raw_text = extract_text(resume_path)
            cleaned_text = preprocess_text(raw_text)
            hashed_text = hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()

            # Check if resume already seen in this batch
            if hashed_text in seen_hashes:
                status = f"Duplicate resume detected (same as {seen_hashes[hashed_text]} in this batch)."
            else:
                # Check if resume already exists in DB
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM documents WHERE hashed_text = %s AND type='resume'", 
                    (hashed_text,)
                )
                duplicate_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                if duplicate_count == 0:
                    insert_document(filename, "resume", raw_text, cleaned_text)
                    status = "New resume processed."
                else:
                    status = "Duplicate resume detected (already in database)."

                # Save in seen_hashes whether duplicate or not
                seen_hashes[hashed_text] = filename

            # Add result to display on UI
            results.append({
                'name': filename,
                'raw': raw_text[:500],
                'cleaned': cleaned_text[:500],
                'hash': hashed_text,
                'status': status
            })

    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
