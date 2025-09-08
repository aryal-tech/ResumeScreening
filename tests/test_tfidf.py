import unittest

# Adjust these imports if your names/locations differ
from core.tf_idf import compute_idf

class TestTFIDF(unittest.TestCase):
    def test_idf_monotonicity(self):
        # "skillx" appears in ONLY 1 doc; "commontoken" appears in ALL docs
        docs = [
            ["commontoken", "skillx"],
            ["commontoken"],
            ["commontoken"],
        ]

        idf = compute_idf(docs)
        self.assertIn("commontoken", idf)
        self.assertIn("skillx", idf)

        # Fewer docs -> higher IDF
        self.assertGreater(idf["skillx"], idf["commontoken"])

    def test_idf_non_negative(self):
        # Typical smoothed IDF implementations are >= 0
        docs = [["a"], ["a", "b"], ["a", "b", "c"]]
        idf = compute_idf(docs)
        for term, value in idf.items():
            self.assertGreaterEqual(value, 0.0, f"IDF for {term} should be >= 0")

if __name__ == "__main__":
    unittest.main()
