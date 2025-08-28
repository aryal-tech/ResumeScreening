# core/similarity.py

import math
from typing import Dict, Set
def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float], all_terms: Set[str]) -> float:
    dot_product = sum(vec1.get(term, 0.0) * vec2.get(term, 0.0) for term in all_terms)
    norm1 = math.sqrt(sum(vec1.get(term, 0.0) ** 2 for term in all_terms))
    norm2 = math.sqrt(sum(vec2.get(term, 0.0) ** 2 for term in all_terms))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)  # value is already between 0 and 1

