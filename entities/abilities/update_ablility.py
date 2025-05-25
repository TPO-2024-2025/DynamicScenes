"""Ability to update an entity's attributes."""

from collections.abc import Awaitable, Callable
import logging
import threading

from homeassistant.core import Context

from ...attributes import Attr  # noqa: TID252
from ...entity_updates import cancel_update, schedule_update  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class UpdateAbility:
    """Ability to update an entity's attributes."""

    def __init__(
        self,
        entity_id: str,
        create_context_method: Callable[[], Context],
        update_method: Callable[[dict[type[Attr], Attr], Callable[[], Context]], Awaitable[None]],
    )-> None:
        """Initialize the update ability."""
        # Local variables
        self.entity_id: str = entity_id # For logging
        self._anounce_update_method = create_context_method
        self._update_method = update_method

        self._update_lock = threading.RLock()

        # Stores previous update so we dont update the same attributes again
        self._prev_update_ids: set[str] = set()

    # ===== Update method =====

    def schedule_update(
            self,
            wanted_state: dict[type[Attr], Attr],
            update_id: str,
            entity_delay: float = 0
    ) -> None:
        """Schedule an entity update."""
        with self._update_lock:
            self._prev_update_ids.add(update_id)

            # Schedule the update
            _LOGGER.info(
                "UPDATE_ABILITY: Scheduling update of '%s' with id '%s' and delay %s",
                self.entity_id,
                update_id,
                entity_delay
            )
            schedule_update(
                update_id,
                lambda: self._update_method(
                    wanted_state,
                    self._anounce_update_method,
                ),
                entity_delay,
            )

    def cancel_updates(self) -> None:
        """Cancel all scheduled updates."""
        with self._update_lock:
            # Cancel all previous updates
            for update_id in self._prev_update_ids:
                _LOGGER.info("UPDATE_ABILITY: Cancelling update of with id '%s'", update_id)
                cancel_update(update_id)
