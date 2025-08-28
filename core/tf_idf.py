# core/tf_idf.py

import math
from collections import Counter

MAX_FEATURES = 2000

def compute_tf(tokens):
    """Compute term frequency for a list of tokens."""
    tf = {}
    total_terms = len(tokens)
    counts = Counter(tokens)

    for term, count in counts.items():
        tf[term] = count / total_terms
    return tf

def compute_idf(all_docs):
    """Compute inverse document frequency (smoothed)."""
    N = len(all_docs)
    idf = {}
    all_terms = set(term for doc in all_docs for term in doc)

    for term in all_terms:
        containing_docs = sum(1 for doc in all_docs if term in doc)
        idf[term] = math.log((N + 1) / (containing_docs + 1)) + 1
    return idf

def compute_tfidf(all_docs, boost_terms=None, boost_factor=2.0):
    """
    Compute TF-IDF vectors with optional boosting for job-description terms in resumes.

    Args:
        all_docs (List[List[str]]): List of tokenized documents (JD is at index 0)
        boost_terms (Set[str]): Terms from JD to boost in resumes
        boost_factor (float): Boost multiplier

    Returns:
        List[Dict[str, float]], Set[str]: TF-IDF vectors, selected top-k terms
    """
    idf = compute_idf(all_docs)
    tfidf_vectors = []

    # Collect all TF-IDF scores across all documents for feature limiting
    all_scores = {}

    for i, doc in enumerate(all_docs):
        tf = compute_tf(doc)
        tfidf = {}
        for term in tf:
            weight = tf[term] * idf[term]
            if boost_terms and i != 0 and term in boost_terms:
                weight *= boost_factor
            tfidf[term] = weight

            # Track term importance globally for feature pruning
            if term not in all_scores:
                all_scores[term] = 0
            all_scores[term] += weight
        tfidf_vectors.append(tfidf)

    # Keep only top MAX_FEATURES by global score
    top_terms = set(sorted(all_scores, key=all_scores.get, reverse=True)[:MAX_FEATURES])

    # Filter TF-IDF vectors to include only top terms
    filtered_vectors = []
    for tfidf in tfidf_vectors:
        filtered = {term: score for term, score in tfidf.items() if term in top_terms}
        filtered_vectors.append(filtered)

    return filtered_vectors, top_terms
