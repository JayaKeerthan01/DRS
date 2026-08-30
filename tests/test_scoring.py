import unittest

from agents.scoring import (
    hospital_capacity_score,
    hospital_suitability,
    rescue_priority_score,
)


class TestHospitalCapacityScore(unittest.TestCase):
    def test_full_capacity_scores_higher_than_empty(self):
        full = hospital_capacity_score(beds_available=100, beds_total=100,
                                        icu_available=10, doctors_available=40)
        empty = hospital_capacity_score(beds_available=0, beds_total=100,
                                         icu_available=0, doctors_available=0)
        self.assertGreater(full, empty)

    def test_zero_total_beds_does_not_divide_by_zero(self):
        # beds_total=0 used to be possible via `/ max(beds_total, 1)`; make
        # sure that guard still holds after the refactor into scoring.py.
        score = hospital_capacity_score(beds_available=0, beds_total=0,
                                         icu_available=0, doctors_available=0)
        self.assertEqual(score, 0)

    def test_icu_and_doctor_contributions_are_capped(self):
        # icu_available/10 and doctors_available/40 are both capped at 1.0
        # so a single hospital with huge ICU/doctor counts can't dominate
        # the score purely on those terms.
        score = hospital_capacity_score(beds_available=0, beds_total=100,
                                         icu_available=999, doctors_available=999)
        self.assertAlmostEqual(score, 0.3 + 0.2, places=6)


class TestHospitalSuitability(unittest.TestCase):
    def test_closer_hospital_scores_higher_at_equal_capacity(self):
        near = hospital_suitability(capacity_score=0.5, distance_km=1)
        far = hospital_suitability(capacity_score=0.5, distance_km=20)
        self.assertGreater(near, far)

    def test_higher_capacity_scores_higher_at_equal_distance(self):
        high_cap = hospital_suitability(capacity_score=0.9, distance_km=5)
        low_cap = hospital_suitability(capacity_score=0.1, distance_km=5)
        self.assertGreater(high_cap, low_cap)


class TestRescuePriorityScore(unittest.TestCase):
    def test_high_risk_outranks_low_risk_at_equal_density(self):
        high = rescue_priority_score("High", density=0.5)
        low = rescue_priority_score("Low", density=0.5)
        self.assertGreater(high, low)

    def test_denser_zone_outranks_sparser_zone_at_equal_risk(self):
        dense = rescue_priority_score("Medium", density=0.95)
        sparse = rescue_priority_score("Medium", density=0.1)
        self.assertGreater(dense, sparse)

    def test_unknown_risk_level_falls_back_to_low_weight(self):
        # Guards the RISK_WEIGHT.get(risk_level, 0.2) fallback — a zone with
        # a typo'd or unexpected risk_level should not silently rank as
        # the highest priority.
        unknown = rescue_priority_score("Unknown", density=0.5)
        low = rescue_priority_score("Low", density=0.5)
        self.assertAlmostEqual(unknown, low, places=9)


if __name__ == "__main__":
    unittest.main()
