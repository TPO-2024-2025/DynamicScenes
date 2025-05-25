"""Ability to shift the time of a scene."""

from collections.abc import Callable
import logging
import threading

from ...utilities import seconds_from_midnight  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class TimeshiftAbility:
    """Class that gives entities timeshifting ability."""

    def __init__(
        self, entity_id: str, on_timeshift_change_callback: Callable[[int], None]
    ) -> None:
        """Initialize the timeshift."""
        # Local variables
        self.entity_id: str = entity_id  # For logging

        # Set the timeshift to 0
        self._timeshift: int = 0
        self._timeshift_lock = threading.RLock()

        # Set the callback
        self._on_timeshift_change = on_timeshift_change_callback

    # ===== Properties =====

    @property
    def time(self) -> int:
        """Get the current timeshift in seconds."""
        with self._timeshift_lock:
            # Return time in seconds shifted by the timeshift
            shifted_time = seconds_from_midnight() + self._timeshift
            return shifted_time % (24 * 3600) # Ensure it wraps around a day

    # ===== Timeshift management =====

    def set(self, timeshift: int) -> None:
        """Set the timeshift to a specific value in seconds."""
        with self._timeshift_lock:
            self._timeshift = self._correct_for_12h(timeshift)
            self._on_timeshift_change(self._timeshift)
        _LOGGER.info(
            "TIMESHIFTS_ABILITY: Timeshift of '%s' set to: %s",
            self.entity_id,
            self._timeshift,
        )

    def shift(self, shift: int) -> None:
        """Adjust the timeshift by a relative amount in seconds."""
        # Make sure the timeshift is in the range -12h to +12h
        _LOGGER.debug(
            "TIMESHIFTS_ABILITY: Old timeshift of '%s' was: %s",
            self.entity_id,
            self._timeshift,
        )
        with self._timeshift_lock:
            self._timeshift = self._correct_for_12h(self._timeshift + shift)
            self._on_timeshift_change(self._timeshift)
        _LOGGER.info(
            "TIMESHIFTS_ABILITY: Timeshift of '%s' shifted to: %s",
            self.entity_id,
            self._timeshift,
        )

    # ===== Helpers =====

    @staticmethod
    def _correct_for_12h(timeshift: int) -> int:
        """Correct the timeshift so it is in the -12h to +12h range."""
        # Make sure the time is in the range -12h to +12h
        return ((timeshift + 12 * 3600) % (24 * 3600)) - 12 * 3600
