# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import make_response
import os, hashlib
from tempfile import TemporaryDirectory

# ==== imports (add extract_linkedin, extract_phone) ====
from core.extract import extract_text, extract_email, extract_exact_section, extract_linkedin, extract_phone
from core.preprocess import preprocess_text
from core.tf_idf import compute_tfidf
from core.similarity import cosine_similarity
from database.db_connect import (
    get_connection,
    insert_document,
    get_document_by_filename,   # NEW
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
            # Return non-cached blank form on error
            resp = make_response(render_template("register.html"), 400)
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            return resp

        # PASSWORD RULE (server-side): ≥8 chars, ≥1 uppercase, ≥1 special
        import re
        if not re.match(r"^(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$", password):
            flash("Password must be ≥8 chars and include an uppercase and a special character.", "error")
            resp = make_response(render_template("register.html"), 400)
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            return resp

        if find_user_by_email(email):
            flash("Email already registered", "error")
            resp = make_response(render_template("register.html"), 400)
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            return resp

        uid = create_user(company_name, email, password)
        session["user_id"] = uid
        session["email"] = email
        session["company_name"] = company_name
        return redirect(url_for("home"))

    # GET: serve a fresh, non-cached blank form
    resp = make_response(render_template("register.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


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
      - Detect duplicates only within THIS run.
      - Do not compute similarity for duplicates (display '—').
      - Block if the same PDF is uploaded as both JD and Resume.
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
        jd_file.stream.seek(0)
        jd_text = extract_text(jd_bytes)
        jd_cleaned = preprocess_text(jd_text)
        insert_document("job_description.pdf", "job", jd_text, jd_cleaned)

        jd_tokens = jd_cleaned.split()
        jd_priority_terms = collect_jd_priority_terms(jd_text)
        jd_hash = hashlib.sha256(jd_text.encode("utf-8")).hexdigest()

        # --- Resumes (per-run de-dupe) ---
        resume_files = request.files.getlist("resume_files")
        if not resume_files:
            flash("Please upload at least one resume PDF.", "error")
            return redirect(url_for("actual_calculation"))

        seen_hashes_run = {}   # hash -> first filename
        uniques = []           # to score once

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

            # (2) Block JD==Resume same PDF
            if raw_hash == jd_hash:
                errors.append(f"'{filename}' was skipped because it is the SAME PDF as the uploaded JD.")
                continue

            # In-run duplicate check
            if raw_hash in seen_hashes_run:
                # (3) mark duplicate; DO NOT score
                results.append({
                    "name": filename,
                    "email": email,
                    "duplicate": f"Duplicate of {seen_hashes_run[raw_hash]}",
                    "score": None,         # <- not computed
                    "raw_hash": raw_hash,
                })
                continue

            # First time in this run
            seen_hashes_run[raw_hash] = filename
            insert_document(filename, "resume", raw_text, cleaned_text)  # optional persistence

            results.append({
                "name": filename,
                "email": email,
                "duplicate": "—",
                "score": None,            # filled later
                "raw_hash": raw_hash,
            })
            uniques.append({
                "filename": filename,
                "raw_hash": raw_hash,
                "tokens": cleaned_text.split(),
            })

                # --- In-memory scoring for THIS RUN ONLY ---
        if uniques:
            all_docs = [jd_tokens] + [u["tokens"] for u in uniques]
            tfidf_vectors, all_terms = compute_tfidf(
                all_docs,
                boost_terms=jd_priority_terms,
                boost_factor=1.5
            )
            job_vec = tfidf_vectors[0]
            resume_vecs = tfidf_vectors[1:]

            hash_to_score = {}
            for i, u in enumerate(uniques):
                s = cosine_similarity(job_vec, resume_vecs[i], all_terms)
                hash_to_score[u["raw_hash"]] = round(float(s), 2)

            # assign scores to non-duplicates
            for row in results:
                if row.get("duplicate") == "—":
                    row["score"] = hash_to_score.get(row["raw_hash"], None)

        # === IMPORTANT: rank by similarity (desc), duplicates last ===
        def sort_key(r):
            # scored rows first (flag 0), duplicates (None) later (flag 1)
            is_dup_flag = 0 if r.get("score") is not None else 1
            score = r.get("score") if r.get("score") is not None else -1.0
            return (is_dup_flag, -score)

        results.sort(key=sort_key)

        # S.N reflects ranked order
        for i, r in enumerate(results, start=1):
            r["sn"] = i
            r.pop("raw_hash", None)

        session["last_results"] = results
        session["last_errors"] = errors
        return redirect(url_for("results"))


@app.route("/results")
@login_required
def results():
    # ?top=10 -> show first N rows by S.N (S.N preserves upload order)
    try:
        selected_top = int(request.args.get("top", "10"))
    except ValueError:
        selected_top = 10

    all_rows = session.get("last_results", [])
    # Already in S.N order (from /process). Just slice:
    trimmed = all_rows[:max(0, selected_top)]

    return render_template(
        "results.html",
        results=trimmed,
        errors=session.get("last_errors", []),
        selected_top=selected_top
    )


# --------- (1) Resume Detail API (for modal) ---------
@app.get("/api/resume_detail")
@login_required
def api_resume_detail():
    filename = (request.args.get("file") or "").strip()
    if not filename:
        return jsonify({"ok": False, "error": "Missing 'file' parameter"}), 400

    doc = get_document_by_filename(filename, "resume")
    if not doc:
        return jsonify({"ok": False, "error": "Resume not found"}), 404

    raw_text = doc["raw_text"] or ""
    info = {
        "email": extract_email(raw_text) or "",
        "phone": extract_phone(raw_text) or "",
        "linkedin": extract_linkedin(raw_text) or "",
    }

    return jsonify({
        "ok": True,
        "filename": filename,
        "email": info["email"],
        "phone": info["phone"],
        "linkedin": info["linkedin"],
        "text": raw_text
    })

if __name__ == "__main__":
    app.run(debug=True)
