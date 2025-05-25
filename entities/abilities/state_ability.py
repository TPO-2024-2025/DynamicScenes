"""Ability to get and use ha state of an entity."""

from collections.abc import Callable
from datetime import datetime
import logging
import threading
from typing import Any

from homeassistant.core import Context, Event, EventStateChangedData, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from ...attributes.base import Attr  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class StateAbility:
    """Ability to get and use Home Assistant state of an entity."""

    # ===== Initalization and delition =====

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str,
        translate_state_method: Callable[[str, dict[str, Any]], dict[type[Attr], Attr]],
        external_state_change_callback: Callable[[dict[type[Attr], Attr]], None],
    ) -> None:
        """Initialize the state ability."""
        # Initialize local variables
        self._hass = hass
        self._translate_state_method = translate_state_method
        self._external_state_change_callback = external_state_change_callback

        self._entity_id = entity_id  # Entity exists.

        # Contexts created by this ability
        self._announced_state_changes_lock = threading.RLock()
        self._created_contexts: dict[str, datetime] = {}

        # This entity state
        self._context_lock = threading.RLock()
        self._current_state: dict[type[Attr], Attr] = self.__get_state()

        # Set up the state listener
        self._unsub_state_listener = async_track_state_change_event(
            hass, [entity_id], self._handle_state_change_event
        )

    def __del__(self) -> None:
        """Clean up the state ability."""
        self._unsub_state_listener()
        _LOGGER.debug(
            "STATE_ABILITY: Unsubscribed from state change events for entity '%s'",
            self._entity_id,
        )

    # ===== Properties =====

    @property
    def current_state(self) -> dict[type[Attr], Attr]:
        """Get the current state of the entity."""
        with self._context_lock:
            return self._current_state

    # ===== HASS State updates =====

    def _handle_state_change_event(self, event: Event[EventStateChangedData]) -> None:
        """Handle hass state change event."""
        # Check some stuff..
        if event.data["new_state"] is None:
            _LOGGER.warning(
                "STATE_ABILITY: Entity '%s's new state is None",
                event.data["entity_id"],
            )
            return
        if event.data["old_state"] is None:
            _LOGGER.warning(
                "STATE_ABILITY: Entity '%s's old state is None",
                event.data["entity_id"],
            )
            return

        new_state = event.data["new_state"]

        # Translate the state
        translated_state = self._translate_state_method(
            new_state.state,
            new_state.attributes,  # type: ignore[]
        )
        # Update the current state
        with self._context_lock and self._announced_state_changes_lock:
            # Check if the state has changed
            if not self.has_changed(translated_state):
                _LOGGER.debug(
                    "STATE_ABILITY: State of '%s' has not changed, ignoring state change event.",
                    self._entity_id,
                )
                return  # No change, nothing to do

            # Has changed: Update the current state
            self._current_state = translated_state

            context = new_state.context

            # Check if the state change was internal
            if self._check_context(context.id):
                _LOGGER.debug(
                    "STATE_ABILITY: State changed for '%s' due to INTERNAL event. New state: %s",
                    self._entity_id,
                    self._current_state,
                )
                return  # Ignore internal state changes

            # State has changed.
            _LOGGER.info(
                "STATE_ABILITY: State changed for '%s' due to EXTERNAL event. New state: %s",
                self._entity_id,
                self._current_state,
            )
            self._external_state_change_callback(self._current_state)

    # ===== Methods =====

    def has_changed(self, new_state: dict[type[Attr], Attr]) -> bool:
        """Check if the state is different from the current hass state."""
        with self._context_lock:
            # Compare the new state with the current state
            for key, value in new_state.items():
                if (
                    key not in self._current_state
                    or self._current_state[key].value != value.value
                ):
                    _LOGGER.debug(
                        "STATE_ABILITY: State of '%s' has changed for key: %s. "
                        "Current value: %s -> New value: %s;.",
                        self._entity_id,
                        key,
                        self._current_state.get(key),
                        value,
                    )
                    return True
        return False

    # Anouncing state changes
    def create_context(self) -> Context:
        """Create a context for an internal state change."""
        with self._context_lock:
            context = Context()
            self._created_contexts[context.id] = datetime.now()
            return context

    def _check_context(self, context_id: str) -> bool:
        """Check if the context was created by this ability."""
        with self._context_lock:
            if context_id in self._created_contexts:
                self._created_contexts.pop(context_id)
                # Clear old contexts if they exceed the limit
                if len(self._created_contexts) > 100:
                    self._clear_old_contexts()
                return True

            # Clear contexts.
            self._clear_old_contexts()
            return False

    def _clear_old_contexts(self) -> None:
        """Clear old contexts that are older than 1 minute."""
        with self._context_lock:
            now = datetime.now()
            self._created_contexts = {
                context_id: created_time
                for context_id, created_time in self._created_contexts.items()
                if (now - created_time).total_seconds() < 10
            }
            _LOGGER.debug(
                "STATE_ABILITY: Cleared old contexts, remaining: %d",
                len(self._created_contexts),
            )

    # ===== Helpers =====

    def __get_state(self) -> dict[type[Attr], Attr]:
        """Get the current state of the entity from Home Assistant."""
        state = self._hass.states.get(self._entity_id)
        if not state:
            _LOGGER.warning(
                "STATE_ABILITY: Entity '%s' not found in Home Assistant",
                self._entity_id,
            )
            return {}

        # Extract relevant attributes
        return self._translate_state_method(state.state, state.attributes)  # type: ignore[]
