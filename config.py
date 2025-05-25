"""Config for dynamic scenes."""

import logging
from pathlib import Path
import threading
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .constants import ENTRYDATA
from .data_loader import async_load_entities

if TYPE_CHECKING:
    from .entities import Entity

_LOGGER = logging.getLogger(__name__)


class Config:
    """Configuration for the dynamic scenes integration."""

    def __init__(
        self, entry: ConfigEntry, integration_dir: Path, hass: HomeAssistant
    ) -> None:
        """Initialize the configuration."""
        self._entry_id = entry.entry_id
        self._hass = hass
        self._integration_dir = integration_dir
        self._rerun_interval = entry.data.get(ENTRYDATA.UPDATE_INTERVAL, 30)

        self._entities_lock = threading.RLock()
        self._entities: dict[str, Entity] | None = None

    def __del__(self) -> None:
        """Clean up the configuration."""
        if self._entities is not None:
            for entity in self._entities.values():
                entity.invalidate()

    # ===== Properties basically =====

    # Entry id
    @property
    def entry_id(self) -> str:
        """Get the entry ID."""
        return self._entry_id

    # Home Assistant instance
    @property
    def hass(self) -> HomeAssistant:
        """Get the Home Assistant instance."""
        return self._hass

    # Rerun interval
    @property
    def update_interval(self) -> int:
        """Get the rerun interval in seconds."""
        return self._rerun_interval

    # Entity
    @property
    def entities(self) -> set["Entity"]:
        """Get the entities.

        Raises ValueError if entities have not been loaded yet.
        """
        if self._entities is None:
            raise ValueError("Entities have not been loaded yet.")

        with self._entities_lock:
            return set(self._entities.values())

    def get_entity(self, entity_id: str) -> "Entity":
        """Get an entity by its ID.

        Raises KeyError if the entity does not exist / isnt loaded.
        Raises ValueError if entities have not been loaded yet.
        """
        if self._entities is None:
            raise ValueError("Entities have not been loaded yet.")

        with self._entities_lock:
            return self._entities[entity_id]  # Raises KeyError if entity_id not found

    async def async_load_entities(self) -> None:
        """Reload the entities from the file."""
        _LOGGER.info("CONFIG: Loading entities from file: %s", self._integration_dir)
        if self._entities is not None:
            for entity in self._entities.values():
                entity.invalidate()
        entities = await async_load_entities(self._integration_dir, self._hass)
        self._entities = entities
