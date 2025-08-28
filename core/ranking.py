# core/ranking.py

from database.db_connect import get_connection
from core.tf_idf import compute_tfidf
from core.similarity import cosine_similarity


def fetch_cleaned_docs():
    """
    Fetch latest job description and all resumes (already cleaned and tokenized).
    Returns:
        job_tokens: List[str]
        resume_data: List[Tuple[str, List[str]]]
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch most recent job description
    cursor.execute("SELECT cleaned_text FROM documents WHERE type = 'job' ORDER BY id DESC LIMIT 1")
    jd = cursor.fetchone()
    if not jd:
        raise Exception("No job description found.")
    job_tokens = jd[0].split()

    # Fetch all resumes
    cursor.execute("SELECT file_name, cleaned_text FROM documents WHERE type = 'resume'")
    resumes = cursor.fetchall()

    resume_data = [(file_name, text.split()) for file_name, text in resumes]

    cursor.close()
    conn.close()

    return job_tokens, resume_data


def rank_resumes(min_score_threshold: float = 0.2):
    """
    Rank all resumes against the job description based on cosine similarity.
    Filters out resumes with similarity score < min_score_threshold.

    Returns:
        List[Tuple[str, float]]: Sorted list of (filename, similarity score)
    """
    job_tokens, resume_data = fetch_cleaned_docs()

    # Combine all docs (JD + resumes) for TF-IDF vectorization
    all_docs = [job_tokens] + [tokens for _, tokens in resume_data]

    tfidf_vectors, all_terms = compute_tfidf(
        all_docs,
        boost_terms=set(job_tokens),
        boost_factor=2.0
    )

    job_vec = tfidf_vectors[0]
    resume_vecs = tfidf_vectors[1:]

    scored = []
    for i, (file_name, _) in enumerate(resume_data):
     score = cosine_similarity(job_vec, resume_vecs[i], all_terms)
     if score >= min_score_threshold:
        scored.append((file_name, round(score, 2)))  

    # Sort by similarity score in descending order
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored
