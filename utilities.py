"""Utilities for Dynamic Scenes."""

from datetime import datetime


def to_hh_mm_ss(seconds: int) -> str:
    """Convert the time to a HH:MM:SS string."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def to_seconds(time_str: str) -> int:
    """Parse the time in HH:MM format into seconds since midnight."""
    hours, minutes = map(int, time_str.split(":"))
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError("Hours must be 0-23 and minutes 0-59")
    return hours * 3600 + minutes * 60

def seconds_from_midnight() -> int:
    """Get the current time in seconds since midnight."""
    now = datetime.now().time()
    return now.hour * 3600 + now.minute * 60 + now.second
