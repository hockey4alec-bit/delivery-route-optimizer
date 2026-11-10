import unittest

from delivery_route_optimizer import (
    nearest_neighbor,
    route_distance,
    two_opt,
)


class TestOptimizer(unittest.TestCase):
    def setUp(self):
        # Deliberately asymmetric: A -> B can differ from B -> A.
        self.distances = [
            [0, 2, 9, 10],
            [1, 0, 6, 4],
            [15, 7, 0, 8],
            [6, 3, 12, 0],
        ]

    def assert_valid_route(self, route, number_of_stops):
        self.assertEqual(route[0], 0)
        self.assertEqual(route[-1], 0)
        self.assertEqual(len(route), number_of_stops + 1)
        self.assertEqual(
            sorted(route[:-1]),
            list(range(number_of_stops)),
        )

    def test_route_distance_respects_direction(self):
        route = [0, 1, 3, 2, 0]
        self.assertEqual(
            route_distance(route, self.distances),
            2 + 4 + 12 + 15,
        )

    def test_nearest_neighbor_expected_order(self):
        route = nearest_neighbor(self.distances)
        self.assertEqual(route, [0, 1, 3, 2, 0])

    def test_nearest_neighbor_visits_every_stop_once(self):
        route = nearest_neighbor(self.distances)
        self.assert_valid_route(route, len(self.distances))

    def test_two_opt_preserves_valid_route(self):
        initial = nearest_neighbor(self.distances)
        result = two_opt(initial, self.distances)
        self.assert_valid_route(result, len(self.distances))

    def test_two_opt_does_not_increase_distance(self):
        initial = nearest_neighbor(self.distances)
        result = two_opt(initial, self.distances)

        self.assertLessEqual(
            route_distance(result, self.distances),
            route_distance(initial, self.distances),
        )

    def test_two_opt_improves_known_example(self):
        initial = [0, 1, 3, 2, 0]
        result = two_opt(initial, self.distances)

        self.assertLess(
            route_distance(result, self.distances),
            route_distance(initial, self.distances),
        )

    def test_one_delivery_stop(self):
        distances = [
            [0, 5],
            [7, 0],
        ]

        route = nearest_neighbor(distances)
        result = two_opt(route, distances)

        self.assertEqual(result, [0, 1, 0])
        self.assertEqual(route_distance(result, distances), 12)


if __name__ == "__main__":
    unittest.main()