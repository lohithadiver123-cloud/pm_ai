import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.categorization import categorize, detect_sentiment
from services.preprocessing import normalize


class Milestone1Validation(unittest.TestCase):
    def test_normalize_removes_noise(self):
        text = "!!! The server is super slow and crashes often!!!"
        result = normalize(text)
        self.assertIn("server", result)
        self.assertIn("slow", result)
        self.assertIn("crashes", result)
        self.assertNotIn("!!!", " ".join(result))

    def test_categorize_bug_report(self):
        text = "The login screen crashes every time after entering password."
        self.assertEqual(categorize(text), "bug_report")

    def test_categorize_feature_request(self):
        text = "It would be great to have dark mode support for the dashboard."
        self.assertEqual(categorize(text), "feature_request")

    def test_detect_sentiment_positive(self):
        self.assertEqual(detect_sentiment("This feature is excellent and really helpful."), "positive")

    def test_detect_sentiment_negative(self):
        self.assertEqual(detect_sentiment("The app is slow and broken."), "negative")


if __name__ == "__main__":
    unittest.main()
