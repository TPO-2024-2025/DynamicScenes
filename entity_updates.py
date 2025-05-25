"""Manage updates, so they are in the right order with the right delay."""

import asyncio
from collections.abc import Awaitable, Callable
import logging
import threading

_LOGGER = logging.getLogger(__name__)


class _EntityUpdate:
    """Class that represents an update for an entity."""

    def __init__(self,
                 update_id: str,
                 update_coro: Callable[[], Awaitable[None]],
                 entity_delay: float = 0
    ) -> None:
        self.update_id = update_id
        self.update_coro = update_coro  # The actual update coroutine
        self.entity_delay = entity_delay
        self._task: asyncio.Task[None] | None = None

    # ===== Scheduling and calcelation logic =====

    def schedule(self, delay: float = 0):
        """Schedules a update, that can be canceled."""
        # If there is an existing task, cancel it
        if self._task:
            _LOGGER.debug(
                "ENTITY_UPDATE: Cancelling existing update task for id '%s' "
                "as new task was created with the same id",
                self.update_id,
            )
            self._task.cancel()

        # Create a new task with the specified delay
        _LOGGER.debug(
            "ENTITY_UPDATE: Scheduling update task for id '%s' with delay %s",
            self.update_id,
            delay,
        )
        self._task = asyncio.create_task(self._async_execute_delayed_update(delay))

    def cancel(self):
        """Cancel the update task if it exists."""
        if self._task:
            _LOGGER.debug("ENTITY_UPDATE: Cancelling update task for id '%s'", self.update_id)
            self._task.cancel()
            self._task = None
    def fake_cancel_update(update_id):
        # Lahko samo beležiš klice
        cancelled_calls.append(update_id)

    # ===== Helpers =====

    async def _async_execute_delayed_update(self, delay: float = 0):
        """Execute the update after a delay."""
        try:
            if delay > 0:
                await asyncio.sleep(delay)

            # Execute the actual update
            _LOGGER.debug("ENTITY_UPDATE: Executing update for entity '%s'", self.update_id)
            await self.update_coro()
        except asyncio.CancelledError:
            # Task was cancelled - this is expected behavior
            pass
        finally:
            # Clean up
            self._task = None

# ===== Global state for managing updates =====

_pending_updates: dict[str, _EntityUpdate] = {}  # entity_id -> EntityUpdate
_pending_updates_lock = threading.RLock()  # Lock for thread-safe access to _pending_updates

def schedule_update(
        update_id: str,
        update_coro: Callable[[], Awaitable[None]],
        entity_delay: float = 0
) -> None:
    """Schedule an update for an entity with a optional delay."""
    with _pending_updates_lock:
        # Cancel existing update for this entity
        if update_id in _pending_updates:
            _pending_updates[update_id].cancel()

        # Create new update
        update = _EntityUpdate(update_id, update_coro, entity_delay)
        _pending_updates[update_id] = update

        # Schedule with delay
        update.schedule(update.entity_delay) # for now just use the entity delay

def cancel_update(update_id: str) -> None:
    """Cancel a scheduled update for an entity."""
    with _pending_updates_lock:
        if update_id in _pending_updates:
            _pending_updates[update_id].cancel()
            del _pending_updates[update_id]
            _LOGGER.debug("Cancelled update for id '%s'", update_id)
        else:
            _LOGGER.debug("No scheduled update found for id '%s'", update_id)
