import unittest

from agents.citizen_chat_agent import find_zone

ZONES = [
    {"name": "HSR Layout"},
    {"name": "Koramangala"},
    {"name": "Bellandur"},
    {"name": "BTM Layout"},
    {"name": "Electronic City"},
]


class TestFindZone(unittest.TestCase):
    def test_full_name_match(self):
        z = find_zone("what's the risk in Koramangala right now", ZONES)
        self.assertEqual(z["name"], "Koramangala")

    def test_case_insensitive(self):
        z = find_zone("RISK IN BELLANDUR", ZONES)
        self.assertEqual(z["name"], "Bellandur")

    def test_first_word_fallback_match(self):
        # "hsr" alone should still resolve to "HSR Layout" via the
        # first-word fallback, not just an exact full-name match.
        z = find_zone("nearest hospital to hsr", ZONES)
        self.assertEqual(z["name"], "HSR Layout")

    def test_no_match_returns_none(self):
        z = find_zone("what's the weather like today", ZONES)
        self.assertIsNone(z)

    def test_multi_word_zone_first_word_match(self):
        z = find_zone("evacuation route from electronic", ZONES)
        self.assertEqual(z["name"], "Electronic City")


if __name__ == "__main__":
    unittest.main()
