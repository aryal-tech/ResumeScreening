# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, hashlib
from tempfile import TemporaryDirectory

# ==== imports (add extract_exact_section) ====
from core.extract import extract_text, extract_email, extract_exact_section
from core.preprocess import preprocess_text
from core.tf_idf import compute_tfidf
from core.similarity import cosine_similarity
from database.db_connect import (
    get_connection,
    insert_document,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# ---------------- Utilities ----------------
def is_pdf_upload(file_storage) -> bool:
    """
    Check the '%PDF' magic bytes without consuming the upload stream.
    Returns True if it looks like a real PDF.
    """
    if not file_storage:
        return False
    head = file_storage.stream.read(5)  # b'%PDF-'
    file_storage.stream.seek(0)
    return bool(head) and head.startswith(b"%PDF")

# ---------------- Auth helpers (unchanged) ----------------
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapper

def find_user_by_email(email: str):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, company_name, email, password_hash FROM users WHERE email=%s",
            (email,)
        )
        return cur.fetchone()
    finally:
        conn.close()

def create_user(company_name: str, email: str, password: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (company_name, email, password_hash) VALUES (%s, %s, %s)",
            (company_name, email, generate_password_hash(password))
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

# ---------------- Routes ----------------
@app.route("/")
def home():
    last_results = session.get("last_results", [])
    is_logged_in = bool(session.get("user_id"))
    return render_template("home.html", is_logged_in=is_logged_in, last_results=last_results)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password", "error")
            return render_template("login.html"), 401
        session["user_id"] = user["id"]
        session["email"] = user["email"]
        session["company_name"] = user["company_name"]
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not company_name or not email or not password:
            flash("All fields are required", "error")
            return render_template("register.html"), 400
        if find_user_by_email(email):
            flash("Email already registered", "error")
            return render_template("register.html"), 400

        uid = create_user(company_name, email, password)
        session["user_id"] = uid
        session["email"] = email
        session["company_name"] = company_name
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/actual_calculation", methods=["GET"])
@login_required
def actual_calculation():
    return render_template("actual_calculation.html")

# ===== JD headings to boost at 1.5× =====
JD_HEADINGS_FOR_BOOST = [
    "Responsibilities", "Duties", "Role Overview",
    "Requirements", "Must-Have Skills", "Qualifications",
    "Preferred Skills", "Good to Have", "Bonus Points For",
    "Who You Are", "Ideal Candidate",
    "What We Offer", "Benefits", "Perks",
]

def collect_jd_priority_terms(jd_raw_text: str):
    """Grab content under the specified JD headings and return preprocessed tokens."""
    picked_sections = []
    for h in JD_HEADINGS_FOR_BOOST:
        sec = extract_exact_section(jd_raw_text, h)
        if sec:
            picked_sections.append(sec)
    if not picked_sections:
        return set()
    priority_clean = preprocess_text("\n".join(picked_sections))
    return set(priority_clean.split())

@app.route("/process", methods=["POST"])
@login_required
def process():
    """
    Per-run policy:
      - Detect duplicates only within THIS run (no 'Already in DB' labels).
      - Compute similarity once for the first copy; reuse for duplicates.
      - Similarity is 0..1 (rounded to 2 decimals).
    """
    results, errors = [], []

    with TemporaryDirectory() as _:
        # --- JD: presence + signature check ---
        jd_file = request.files.get("jd_file")
        if not jd_file:
            flash("Job description file missing.", "error")
            return redirect(url_for("actual_calculation"))

        if not is_pdf_upload(jd_file):
            flash("Uploaded job description is not a valid PDF.", "error")
            return redirect(url_for("actual_calculation"))

        jd_bytes = jd_file.read()
        jd_file.stream.seek(0)  # not strictly needed after read, but harmless
        jd_text = extract_text(jd_bytes)
        jd_cleaned = preprocess_text(jd_text)
        insert_document("job_description.pdf", "job", jd_text, jd_cleaned)

        jd_tokens = jd_cleaned.split()
        jd_priority_terms = collect_jd_priority_terms(jd_text)

        # --- Resumes (per-run de-dupe) ---
        resume_files = request.files.getlist("resume_files")
        if not resume_files:
            flash("Please upload at least one resume PDF.", "error")
            return redirect(url_for("actual_calculation"))

        seen_hashes_run = {}   # hash -> first filename
        unique_items = []      # to score once

        for rf in resume_files:
            filename = (rf.filename or "Unknown").strip()

            if not is_pdf_upload(rf):
                errors.append(f"'{filename}' is not a valid PDF and was skipped.")
                continue

            file_bytes = rf.read()
            rf.stream.seek(0)

            raw_text = extract_text(file_bytes)
            cleaned_text = preprocess_text(raw_text)
            raw_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            email = extract_email(raw_text)

            # In-run duplicate check
            if raw_hash in seen_hashes_run:
                results.append({
                    "name": filename,
                    "email": email,
                    "duplicate": f"Duplicate of {seen_hashes_run[raw_hash]}",
                    "score": 0.0,          # will reuse first copy's score
                    "raw_hash": raw_hash
                })
                continue

            # First time in this run
            seen_hashes_run[raw_hash] = filename
            insert_document(filename, "resume", raw_text, cleaned_text)  # optional persistence

            results.append({
                "name": filename,
                "email": email,
                "duplicate": "—",        # run-only policy, no DB-based label
                "score": 0.0,
                "raw_hash": raw_hash
            })
            unique_items.append({
                "filename": filename,
                "raw_hash": raw_hash,
                "tokens": cleaned_text.split()
            })

        # --- In-memory scoring for THIS RUN ONLY ---
        if unique_items:
            all_docs = [jd_tokens] + [u["tokens"] for u in unique_items]

            # Boost only JD-priority terms at 1.5×
            tfidf_vectors, all_terms = compute_tfidf(
                all_docs,
                boost_terms=jd_priority_terms,
                boost_factor=1.5
            )
            job_vec = tfidf_vectors[0]
            resume_vecs = tfidf_vectors[1:]

            # Map hash -> score (0..1)
            hash_to_score = {}
            for i, u in enumerate(unique_items):
                s = cosine_similarity(job_vec, resume_vecs[i], all_terms)
                hash_to_score[u["raw_hash"]] = round(float(s), 2)

            # Assign scores; duplicates reuse first copy's score
            for row in results:
                row["score"] = hash_to_score.get(row["raw_hash"], 0.0)

        # Sort & serial
        results.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(results, start=1):
            r["sn"] = i
            r.pop("raw_hash", None)

        session["last_results"] = results
        session["last_errors"] = errors
        return redirect(url_for("results"))

@app.route("/results")
@login_required
def results():
    # filtering via ?min=0.3 etc (defaults to no filter)
    try:
        selected_min = float(request.args.get("min", "0"))
    except ValueError:
        selected_min = 0.0
    all_rows = session.get("last_results", [])
    filtered = [r for r in all_rows if r.get("score", 0.0) >= selected_min]
    return render_template(
        "results.html",
        results=filtered,
        errors=session.get("last_errors", []),
        selected_min=selected_min
    )

if __name__ == "__main__":
    app.run(debug=True)
