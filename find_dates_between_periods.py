"""Find all dates between two given dates."""

from datetime import date, timedelta


def find_dates_between(start_date: date, end_date: date) -> list[date]:
    """Return a list of all dates from start_date to end_date (inclusive).

    Args:
        start_date: The beginning of the period.
        end_date: The end of the period.

    Returns:
        A list of date objects from start_date to end_date inclusive.

    Raises:
        ValueError: If start_date is after end_date.
    """
    if start_date > end_date:
        raise ValueError(
            f"start_date ({start_date}) must not be after end_date ({end_date})"
        )

    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


if __name__ == "__main__":
    start = date(2025, 1, 1)
    end = date(2025, 1, 10)

    print(f"Dates between {start} and {end}:")
    for d in find_dates_between(start, end):
        print(f"  {d}")
