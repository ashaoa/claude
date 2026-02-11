"""Tests for find_dates_between_periods module."""

import unittest
from datetime import date

from find_dates_between_periods import find_dates_between


class TestFindDatesBetween(unittest.TestCase):
    def test_basic_range(self):
        result = find_dates_between(date(2025, 1, 1), date(2025, 1, 5))
        self.assertEqual(result, [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),
            date(2025, 1, 4),
            date(2025, 1, 5),
        ])

    def test_single_day(self):
        result = find_dates_between(date(2025, 6, 15), date(2025, 6, 15))
        self.assertEqual(result, [date(2025, 6, 15)])

    def test_cross_month_boundary(self):
        result = find_dates_between(date(2025, 1, 30), date(2025, 2, 2))
        self.assertEqual(result, [
            date(2025, 1, 30),
            date(2025, 1, 31),
            date(2025, 2, 1),
            date(2025, 2, 2),
        ])

    def test_cross_year_boundary(self):
        result = find_dates_between(date(2024, 12, 30), date(2025, 1, 2))
        self.assertEqual(result, [
            date(2024, 12, 30),
            date(2024, 12, 31),
            date(2025, 1, 1),
            date(2025, 1, 2),
        ])

    def test_leap_year(self):
        result = find_dates_between(date(2024, 2, 28), date(2024, 3, 1))
        self.assertEqual(result, [
            date(2024, 2, 28),
            date(2024, 2, 29),
            date(2024, 3, 1),
        ])

    def test_invalid_range_raises(self):
        with self.assertRaises(ValueError):
            find_dates_between(date(2025, 2, 1), date(2025, 1, 1))

    def test_result_length(self):
        result = find_dates_between(date(2025, 1, 1), date(2025, 1, 31))
        self.assertEqual(len(result), 31)


if __name__ == "__main__":
    unittest.main()
