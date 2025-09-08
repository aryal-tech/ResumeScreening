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


# ------- TEST-FRIENDLY WRAPPER -------

from typing import List, Dict, Tuple
import math

def _tf(tokens: List[str]) -> Dict[str, float]:
    if not tokens:
        return {}
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    n = float(len(tokens))
    return {t: c / n for t, c in counts.items()}

def _idf(all_docs: List[List[str]]) -> Dict[str, float]:
    N = len(all_docs)
    terms = set(t for doc in all_docs for t in doc)
    idf = {}
    for term in terms:
        containing = sum(1 for doc in all_docs if term in doc)
        # smoothed IDF (>=0)
        idf[term] = math.log((N + 1) / (containing + 1)) + 1
    return idf

def _tfidf(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = _tf(tokens)
    return {t: tf.get(t, 0.0) * idf.get(t, 0.0) for t in idf.keys()}

def _cosine(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    terms = set(v1.keys()) | set(v2.keys())
    dot = sum(v1.get(t, 0.0) * v2.get(t, 0.0) for t in terms)
    n1 = math.sqrt(sum((v1.get(t, 0.0))**2 for t in terms))
    n2 = math.sqrt(sum((v2.get(t, 0.0))**2 for t in terms))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)

def rank_resumes_simple(jd_text: str, resumes: List[Tuple[str, str]]) -> List[Dict]:
    """
    Minimal, deterministic ranking path for unit tests.

    Args:
        jd_text: raw JD text
        resumes: list of (filename, raw_text)

    Returns:
        List of dicts sorted by score desc: [{"filename": str, "score": float}, ...]
    """
    # ultra-simple tokenization (space split) to avoid depending on app preprocess
    jd_tokens = jd_text.lower().split()
    resume_tokens = [(fn, txt.lower().split()) for fn, txt in resumes]

    # Build IDF over JD + all resumes for a consistent space
    corpus = [jd_tokens] + [toks for _, toks in resume_tokens]
    idf = _idf(corpus)
    jd_vec = _tfidf(jd_tokens, idf)

    scored = []
    for fn, toks in resume_tokens:
        r_vec = _tfidf(toks, idf)
        score = _cosine(jd_vec, r_vec)
        scored.append({"filename": fn, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
