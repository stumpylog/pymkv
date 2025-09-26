"""Simplified Timestamp class for mkvmerge with static factory methods."""

import re
from functools import total_ordering
from typing import Final

# Time conversion constants
SECONDS_PER_HOUR: Final[int] = 3600
SECONDS_PER_MINUTE: Final[int] = 60
MINUTES_PER_HOUR: Final[int] = 60
NANOSECONDS_PER_SECOND: Final[int] = 1_000_000_000
NANOSECOND_PRECISION: Final[int] = 9


@total_ordering
class Timestamp:
    """Represents a timestamp for mkvmerge in format HH:MM:SS.nnnnnnnnn"""

    def __init__(self, total_seconds: int, nanoseconds: int = 0) -> None:
        """Create a timestamp from canonical values.

        Args:
            total_seconds: Total seconds (integer part)
            nanoseconds: Nanosecond part (0-999999999)
        """
        if nanoseconds < 0 or nanoseconds >= NANOSECONDS_PER_SECOND:
            raise ValueError(f"Nanoseconds must be 0-{NANOSECONDS_PER_SECOND - 1}, got {nanoseconds}")

        self._total_seconds: int = int(total_seconds)
        self._nanoseconds: int = int(nanoseconds)

    @staticmethod
    def from_string(timestamp_str: str) -> "Timestamp":
        """Create a timestamp from a string like 'HH:MM:SS.nnnnnnnnn'.

        Args:
            timestamp_str: String in format HH:MM:SS.nnn, MM:SS.nnn, etc.

        Returns:
            New Timestamp object
        """
        if not re.match(r"^\d{1,2}(:\d{1,2}){1,2}(\.\d{1,9})?$", timestamp_str):
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")

        parts = timestamp_str.split(":")
        # MM:SS or MM:SS.nnn
        if len(parts) == 2:  # noqa: PLR2004
            hh = "0"
            mm, ss_with_ns = parts
        else:  # HH:MM:SS or HH:MM:SS.nnn
            hh, mm, ss_with_ns = parts

        # Split seconds and nanoseconds
        if "." in ss_with_ns:
            ss, ns = ss_with_ns.split(".")
            # Pad nanoseconds to 9 digits
            nanoseconds = int(ns.ljust(NANOSECOND_PRECISION, "0"))
        else:
            ss = ss_with_ns
            nanoseconds = 0

        total_seconds = int(hh) * SECONDS_PER_HOUR + int(mm) * SECONDS_PER_MINUTE + int(ss)
        return Timestamp(total_seconds, nanoseconds)

    @staticmethod
    def from_seconds(seconds: int | float) -> "Timestamp":
        """Create a timestamp from seconds (int or float).

        Args:
            seconds: Time in seconds

        Returns:
            New Timestamp object
        """
        if isinstance(seconds, float):
            total_seconds = int(seconds)
            nanoseconds = int((seconds - total_seconds) * NANOSECONDS_PER_SECOND)
        else:
            total_seconds = seconds
            nanoseconds = 0

        return Timestamp(total_seconds, nanoseconds)

    @staticmethod
    def from_timestamp(other: "Timestamp") -> "Timestamp":
        """Create a timestamp from another Timestamp (copy constructor).

        Args:
            other: Another Timestamp object

        Returns:
            New Timestamp object (copy)
        """
        return Timestamp(other._total_seconds, other._nanoseconds)  # noqa: SLF001

    @staticmethod
    def from_components(hours: int, minutes: int, seconds: int, nanoseconds: int = 0) -> "Timestamp":
        """Create a timestamp from individual time components.

        Args:
            hours: Hours (0+)
            minutes: Minutes (0-59)
            seconds: Seconds (0-59)
            nanoseconds: Nanoseconds (0-999999999)

        Returns:
            New Timestamp object
        """
        if minutes < 0 or minutes >= MINUTES_PER_HOUR:
            raise ValueError(f"Minutes must be 0-59, got {minutes}")
        if seconds < 0 or seconds >= SECONDS_PER_MINUTE:
            raise ValueError(f"Seconds must be 0-59, got {seconds}")

        total_seconds = hours * SECONDS_PER_HOUR + minutes * SECONDS_PER_MINUTE + seconds
        return Timestamp(total_seconds, nanoseconds)

    def __str__(self) -> str:
        """Format as HH:MM:SS.nnnnnnnnn (strip trailing zeros from nanoseconds)."""
        hours = self._total_seconds // SECONDS_PER_HOUR
        minutes = (self._total_seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE
        seconds = self._total_seconds % SECONDS_PER_MINUTE

        # Format seconds and nanoseconds, strip trailing zeros
        sec_str = f"{seconds:02d}" if self._nanoseconds == 0 else f"{seconds:02d}.{self._nanoseconds:09d}".rstrip("0")

        return f"{hours:02d}:{minutes:02d}:{sec_str}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timestamp):
            raise NotImplementedError
        return self._total_seconds == other._total_seconds and self._nanoseconds == other._nanoseconds

    def __lt__(self, other: "Timestamp") -> bool:
        if self._total_seconds != other._total_seconds:
            return self._total_seconds < other._total_seconds
        return self._nanoseconds < other._nanoseconds

    def __hash__(self) -> int:
        return hash((self._total_seconds, self._nanoseconds))

    def __getitem__(self, index: int) -> int:
        """Get (hours, minutes, seconds, nanoseconds) by index."""
        return (self.hh, self.mm, self.ss, self.nn)[index]

    @property
    def hh(self) -> int:
        return int(self._total_seconds // SECONDS_PER_HOUR)

    @property
    def mm(self) -> int:
        return int((self._total_seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE)

    @property
    def ss(self) -> int:
        return int(self._total_seconds % SECONDS_PER_MINUTE)

    @property
    def nn(self) -> int:
        return self._nanoseconds
