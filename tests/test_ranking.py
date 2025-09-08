import unittest
from core.ranking import rank_resumes_simple

class TestRanking(unittest.TestCase):
    def test_ordering_by_relevance(self):
        jd = "python flask web development"
        resumes = [
            ("A.txt", "python flask api development"),
            ("B.txt", "excel powerpoint communication"),
        ]

        results = rank_resumes_simple(jd, resumes)

        # shape
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 2)
        self.assertIn("filename", results[0])
        self.assertIn("score", results[0])

        # sorted desc
        scores = [r["score"] for r in results]
        self.assertTrue(all(scores[i] >= scores[i+1] for i in range(len(scores)-1)))

        # A should beat B
        self.assertEqual(results[0]["filename"], "A.txt")

    def test_scores_are_numbers(self):
        jd = "data science machine learning"
        resumes = [
            ("R1.txt", "data analysis machine learning"),
            ("R2.txt", "customer service retail"),
        ]
        results = rank_resumes_simple(jd, resumes)
        for r in results:
            self.assertIsInstance(r["score"], (int, float))

if __name__ == "__main__":
    unittest.main()
