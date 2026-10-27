"""Day 2: study tracker — conditions, loops and functions."""

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAILY_TARGET = 5.0
WEEKLY_TARGET = DAILY_TARGET * len(DAYS)


def total_hours(hours: list[float]) -> float:
    """Return the sum of all hours (accumulator pattern)."""
    total = 0.0
    for h in hours:
        total += h
    return total


def best_day(hours: list[float], days: list[str] = DAYS) -> tuple[str, float]:
    """Return (day name, hours) for the day with the most hours; first wins ties."""
    best_index = 0
    for i, h in enumerate(hours):
        if h > hours[best_index]:
            best_index = i
    return days[best_index], hours[best_index]


def status(total: float, target: float = WEEKLY_TARGET) -> str:
    """Return a status label for a weekly total; strictest check first."""
    if total >= target:
        return "On track"
    elif total >= target * 0.7:
        return "Slightly behind"
    elif total > 0:
        return "Behind - plan a catch-up block"
    else:
        return "Not started"


def ask_hours(day: str) -> float:
    """Ask for hours studied on a day until a number between 0 and 24 is entered."""
    while True:
        raw = input(f"Hours studied on {day}: ").strip()
        if raw.replace(".", "", 1).isdigit() and 0 <= float(raw) <= 24:
            return float(raw)
        print("  Please enter a number between 0 and 24.")


def daily_summary(hours: list[float], days: list[str] = DAYS) -> list[str]:
    """Return one formatted line per day, marking days that hit the target."""
    lines = []
    for day, h in zip(days, hours):
        mark = "OK" if h >= DAILY_TARGET else "--"
        lines.append(f"{day}: {h:4.1f} h  {mark}")
    return lines


if __name__ == "__main__":
    week = [ask_hours(day) for day in DAYS]

    total = total_hours(week)
    day, most = best_day(week)

    print("\n=== 7-day summary ===")
    for line in daily_summary(week):
        print(line)
    print(f"Total:    {total:.1f} / {WEEKLY_TARGET:.0f} h")
    print(f"Best day: {day} ({most:.1f} h)")
    print(f"Status:   {status(total)}")
