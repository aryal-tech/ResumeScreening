import unittest
from core.similarity import cosine_similarity  # correct name

def u(*vecs):
    # helper: union of all keys across input dict-vectors
    s = set()
    for v in vecs: s |= set(v.keys())
    return s

class TestSimilarity(unittest.TestCase):
    def test_identical_vectors(self):
        v = {"java": 1.0, "python": 2.0}
        self.assertAlmostEqual(
            cosine_similarity(v, v, u(v, v)), 1.0, places=6
        )

    def test_orthogonal_vectors(self):
        v1 = {"java": 1.0}
        v2 = {"python": 1.0}
        self.assertAlmostEqual(
            cosine_similarity(v1, v2, u(v1, v2)), 0.0, places=6
        )

    def test_symmetry(self):
        v1 = {"a": 1.0, "b": 2.0}
        v2 = {"a": 2.0, "b": 1.0}
        self.assertAlmostEqual(
            cosine_similarity(v1, v2, u(v1, v2)),
            cosine_similarity(v2, v1, u(v1, v2)),
            places=6
        )

if __name__ == "__main__":
    unittest.main()
