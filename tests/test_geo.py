import unittest

from utils.geo import haversine_km


class TestHaversine(unittest.TestCase):
    def test_same_point_is_zero(self):
        self.assertAlmostEqual(haversine_km(12.9, 77.6, 12.9, 77.6), 0.0, places=6)

    def test_known_distance_bangalore_to_chennai(self):
        # Bangalore (12.9716 N, 77.5946 E) to Chennai (13.0827 N, 80.2707 E)
        # is approximately 290 km great-circle distance.
        d = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
        self.assertGreater(d, 280)
        self.assertLess(d, 300)

    def test_symmetry(self):
        d1 = haversine_km(12.90, 77.60, 12.93, 77.65)
        d2 = haversine_km(12.93, 77.65, 12.90, 77.60)
        self.assertAlmostEqual(d1, d2, places=9)


if __name__ == "__main__":
    unittest.main()
