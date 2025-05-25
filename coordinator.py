"""Coordinates events and updates for dynamic scenes."""

import asyncio
import logging

from .config import Config
from .entities import Entity
from .errors import SceneNameError

_LOGGER = logging.getLogger(__name__)


class ServiceCoordinator:
    """Coordinates events and updates for dynamic scenes."""

    def __init__(
            self,
            config: Config,
    ) -> None:
        """Initialize the service coordinator."""
        self._config = config

    # ===== Scenes =====

    def set_scene_active(self, entry_ids: list[str], scene: str) -> None:
        """Set scene of entites to active."""
        _LOGGER.debug(
            "SERVICES_COORDINATOR: Setting scene '%s' to ACTIVE for entities: %s",
            scene,
            entry_ids)

        for entry_id in entry_ids:
            try:
                # Get the entity
                entity: Entity = self._config.get_entity(entry_id)

                # Set scene confition to met
                entity.set_scene_active(scene)
            except KeyError:  # Entity not found
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot set_scene_active: "
                    "Entity with ID '%s' not found in configuration",
                    entry_id,
                )
            except SceneNameError as err:  # Scene name is not valid for this entity
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot set_scene_confition_met: %e", err
                )

    def set_scene_inactive(self, entry_ids: list[str], scene: str) -> None:
        """Set scene of entites to inactive."""
        _LOGGER.debug(
            "SERVICES_COORDINATOR: Setting scene '%s' to INACTIVE for entities: %s",
            scene,
            entry_ids
        )

        for entry_id in entry_ids:
            try:
                # Get the entity
                entity: Entity = self._config.get_entity(entry_id)

                # Set scene confition to inactive
                entity.set_scene_inactive(scene)
            except KeyError:  # Entity not found
                _LOGGER.error(
                    "SERVICES_COORDINATOR: : Cannot set_scene_inactive: "
                    "Entity with ID '%s' not found in configuration",
                    entry_id,
                )
            except SceneNameError as err:  # Scene name is not valid for this entity
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot unset_scene_confition_met: %e", err
                )

    # ===== Custom scenes =====

    def set_custom_active(self, entry_ids: list[str]) -> None:
        """Set the custom scene to active for the given entities."""
        _LOGGER.debug(
            "SERVICES_COORDINATOR: Setting custom to ACTIVE for entities: %s",
            entry_ids
        )

        for entry_id in entry_ids:
            try:
                # Get the entity
                entity: Entity = self._config.get_entity(entry_id)

                # Set the custom scene
                entity.set_custom_active()
            except KeyError:  # Entity not found
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot set_custom_active: "
                    "Entity with ID '%s' not found in configuration",
                    entry_id,
                )

    def set_custom_inactive(self, entry_ids: list[str]) -> None:
        """Set custom scene to inactive for the given entities."""
        _LOGGER.debug(
            "SERVICES_COORDINATOR: Setting custom to INACTIVE for entities: %s",
            entry_ids,
        )

        for entry_id in entry_ids:
            try:
                # Get the entity
                entity: Entity = self._config.get_entity(entry_id)

                # Reset the scene
                entity.set_custom_inactive()
            except KeyError:  # Entity not found
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot set_custom_inactive: "
                    "Entity with ID '%s' not found in configuration",
                    entry_id,
                )

    # ===== Timeshifts =====

    def set_timeshift(self, entry_ids: list[str], timeshift: int) -> None:
        """Set the timeshift of entities."""
        _LOGGER.debug(
            "SERVICES_COORDINATOR: Setting timeshift '%s' for entities: %s",
            timeshift,
            entry_ids,
        )

        for entry_id in entry_ids:
            try:
                # Get the entity
                entity: Entity = self._config.get_entity(entry_id)

                # Set the timeshift
                entity.set_timeshift(timeshift)
            except KeyError:  # Entity not found
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot set_timeshift: "
                    "Entity with ID '%s' not found in configuration",
                    entry_id,
                )

    def shift_timeshift(self, entry_ids: list[str], shift: int) -> None:
        """Shift the timeshift of entities."""
        _LOGGER.debug(
            "SERVICES_COORDINATOR: Shifting timeshift for '%s' for entities: %s",
            shift,
            entry_ids,
        )


        for entry_id in entry_ids:
            try:
                # Get the entity
                entity: Entity = self._config.get_entity(entry_id)

                # Shift the timeshift
                entity.shift_timeshift(shift)
            except KeyError:  # Entity not found
                _LOGGER.error(
                    "SERVICES_COORDINATOR: Cannot shift_timeshift: "
                    "Entity with ID '%s' not found in configuration",
                    entry_id,
                )


class UpdateCoordinator:
    """Coordinates updates for entities in the scenes."""

    def __init__(self, config: Config) -> None:
        """Initialize the update coordinator."""
        self._config = config
        self._task: asyncio.Task[None] | None = None

    def start_updates(self) -> None:
        """Start the update loop for all entities."""
        _LOGGER.info(
            "UPDATE_COORDINATOR: Starting update loop for all entities.",
        )
        self._task = asyncio.create_task(self._async_update_entities())

    def stop_updates(self) -> None:
        """Stop the update loop for all entities."""
        _LOGGER.info(
            "UPDATE_COORDINATOR: Stopping update loop for all entities."
        )
        if self._task:
            self._task.cancel()
            self._task = None

    async def _async_update_entities(self) -> None:
        """Update the entities and schedule the next update."""
        while True:
            try:
                # Update all entities one by one
                _LOGGER.info("UPDATE_COORDINATOR: Updating entities.")
                for entity in self._config.entities:
                    entity.update()

                # Wait for the next update interval
                await asyncio.sleep(self._config.update_interval)
            except asyncio.CancelledError:
                _LOGGER.debug("UPDATE_COORDINATOR: Update loop cancelled.")
                break
            except Exception as e: # HAS TO BE HERE  # noqa: BLE001
                _LOGGER.error(
                    "UPDATE_COORDINATOR: Error during entity update: %s", e
                )
