"""Base ENTITIES class."""

from abc import ABC, abstractmethod
from collections.abc import Callable
import logging
import threading
from typing import Any

from homeassistant.core import Context, HomeAssistant

from ..attributes import Attr  # noqa: TID252
from ..attributes.types import State  # noqa: TID252
from ..entity_scenes import EntityScene  # noqa: TID252  # noqa: TID252
from ..errors import InputValidationError  # noqa: TID252
from ..utilities import to_hh_mm_ss  # noqa: TID252
from .abilities import SceneAbility, StateAbility, TimeshiftAbility, UpdateAbility
from .entity_factory import register_entity

_LOGGER = logging.getLogger(__name__)


class Entity(ABC):
    """Base class for all entities."""

    # ===== Initialization and validation =====

    def _validate_entity(self) -> None:
        """Check if the entity ID is a valid entity in HASS.

        Throws a InputValidationError if the entity ID is not valid.
        """
        # Check if the entity ID is a valid entity in HASS
        if not self._hass.states.get(self._entity_id):
            raise InputValidationError(
                f"Entity {self._entity_id} is not a valid entity in HASS."
            )

    def __init__(
        self, entity_id: str, scene: set[EntityScene], hass: HomeAssistant
    ) -> None:
        """Initialize the entity.

        Throws InputValidationError if entity / the scene is not valid for this entity.
        """
        self._hass = hass

        self._entity_id = entity_id
        self._validate_entity()  # Throws InputValidationError if the entity ID is not valid

        self._valid = True  # Entity will accept updates as long as it is valid.
        self._validity_lock = threading.RLock()

        # Set up the abilities
        try:
            self._scene_ability = SceneAbility(
                entity_id,
                scene,
                self.SUPPORTED_ATTRIBUTES,
                self.__on_scene_change_callback,
            )
            self._timeshift_ability = TimeshiftAbility(
                entity_id,
                self.__on_timeshift_change_callback,
            )
            self._state_ability = StateAbility(
                hass,
                entity_id,
                self._translate_state,
                self.__on_external_state_change_callback,
            )
            self._update_ability = UpdateAbility(
                entity_id,
                self._state_ability.create_context,
                self._set_entity_state,
            )
        except InputValidationError as err:
            raise InputValidationError(f"{self._entity_id}: {err}") from err

    def __init_subclass__(cls) -> None:
        """Initialize the subclass.

        This method is called when the class is created.
        It checks if the constants are defined and registers the class in the registry.

        Raises NotImplementedError if the constants are not defined.
        """
        super().__init_subclass__()
        # Check if the constants are defined
        if not all(hasattr(cls, attr) for attr in ["SUPPORTED_ATTRIBUTES", "DOMAIN"]):
            raise NotImplementedError(
                f"Missing one of the required constants in {cls.__name__}"
            )

        # Register the class in the registry
        _LOGGER.debug("ENTITY: Registering entity class %s", cls.__name__)
        register_entity(cls)

    # ===== Properties =====

    SUPPORTED_ATTRIBUTES: set[
        type[Attr]
    ]  # Used to check if the scene is valid for this entity

    DOMAIN: str  # Used in subclasses to avoid typing errors

    @property
    def entity_id(self) -> str:
        """Get the entity ID."""
        return self._entity_id

    # ===== Entity creation / destruction methods =====

    @classmethod
    @abstractmethod
    def supports(
        cls, domain: str, entity_id: str, attributes: dict[str, Any]
    ) -> bool:  # Override
        """Check if this entity class supports the given entity based on its attributes.

        This method is used to check if the entity class can handle the entity.
        """

    def invalidate(self) -> None:
        """Invalidate the entity (cancel updates and stop new ones from being scheduled)."""
        _LOGGER.info("ENTITY: Invalidating entity %s", self._entity_id)
        with self._validity_lock:
            if not self._valid:
                _LOGGER.warning(
                    "ENTITY: Entity '%s' is already invalid, skipping invalidation.",
                    self._entity_id,
                )
                return
            self._valid = False
        # Cancel all updates
        self._update_ability.cancel_updates()

    # ===== Fasade property getters =====

    # Timeshift ability
    def _get_time(self) -> int:
        """Get the current timeshift of the entity."""
        return self._timeshift_ability.time

    # Scene ability
    def _get_wanted_state(self, time: int | None = None) -> dict[type[Attr], Attr]:
        """Get the wanted state of the entity at the specified time."""
        # If time is None, use the current time
        if time is None:
            time = self._get_time()

        # Get the scene and calculate the wanted state
        cur_scene = self._scene_ability.current_scene
        return cur_scene.get_attrs_at_time(time)

    # State ability
    def _get_current_state(self) -> dict[type[Attr], Attr]:
        """Get the current state of the entity from Home Assistant."""
        return self._state_ability.current_state

    # ===== Fasade methods =====

    # Scene ability
    def set_scene_active(self, scene_name: str) -> None:
        """Set a scene to active state.

        If the scene has the highest priority,it will be set as current scene,
        and the on_scene_change method will be called.

        Raises SceneNameError if the scene does not exist for this entity.
        """
        _LOGGER.debug(
            "ENTITY: Setting scene '%s' to active for entity %s",
            scene_name,
            self._entity_id,
        )
        self._scene_ability.set_scene_active(scene_name)

    def set_scene_inactive(self, scene_name: str) -> None:
        """Set a scene to inactive state.

        If the scene is the current scene, the next highest priority scene will be set as current,
        and the on_scene_change method will be called.
        """
        _LOGGER.debug(
            "ENTITY: Setting scene '%s' to inactive for entity %s",
            scene_name,
            self._entity_id,
        )
        self._scene_ability.set_scene_inactive(scene_name)

    def set_custom_active(self) -> None:
        """Set the custom scene to active."""
        self._set_custom_active()

    def _set_custom_active(self, state: dict[type[Attr], Attr] | None = None) -> None:
        """Set the custom scene to active with the given state values.

        Should be called whenever the custom should be set to active.
        """
        if state is None:
            state = self._get_current_state()
        _LOGGER.debug(
            "ENTITY: Setting custom scene to active for entity '%s' with state: %s",
            self._entity_id,
            state,
        )
        self._scene_ability.set_custom_active(state)

    def set_custom_inactive(self) -> None:
        """Set the custom scene to inactive."""
        _LOGGER.debug(
            "ENTITY: Setting custom scene to inactive for entity %s", self._entity_id
        )
        self._scene_ability.set_custom_inactive()

    # Timeshift ability
    def set_timeshift(self, timeshift: int) -> None:
        """Set the timeshift of the entity.

        This will call the on_timeshift_change method.
        """
        _LOGGER.debug(
            "ENTITY: Setting timeshift '%s' for entity %s", timeshift, self._entity_id
        )
        self._timeshift_ability.set(timeshift)

    def shift_timeshift(self, shift: int) -> None:
        """Shift the timeshift of the entity.

        This will call the on_timeshift_change method.
        """
        _LOGGER.debug(
            "ENTITY: Shifting timeshift '%s' for entity %s", shift, self._entity_id
        )
        self._timeshift_ability.shift(shift)

    # Update ability
    def update(self) -> None:
        """Trigger an update of the entity manually.

        This method is used to make the entity update periodically.
        """
        self._update()

    def _update(
        self,
        time: int | None = None,
        wanted_state: dict[type[Attr], Attr] | None = None,
    ) -> None:
        """Update the entity with the given state and time.

        Should be called whenever the entity needs to be updated.
        """
        # Dont go ask for data we already have
        if time is None:
            time = self._get_time()
        if wanted_state is None:
            wanted_state = self._get_wanted_state(time)

        # Check if the entity is valid
        with self._validity_lock:
            if not self._valid:
                _LOGGER.warning(
                    "ENTITY: Entity '%s' is invalid, skipping update.", self._entity_id
                )
                return

        # Check if the entity needs updating
        if not self._state_ability.has_changed(wanted_state):
            _LOGGER.debug(
                "ENTITY: Entity '%s' does not need updating, "
                "current state is already wanted state.",
                self._entity_id,
            )
            return

        # Update the entity with the new state
        _LOGGER.debug(
            "ENTITY: Updating entity '%s' with wanted state: %s at time: %s",
            self._entity_id,
            wanted_state,
            to_hh_mm_ss(time),
        )
        self._update_ability.schedule_update(
            wanted_state,
            self._entity_id,
            0,  # TODO: Add entity delay attribute support
        )

    # ===== Fasade Helpers =====

    # Scene ability
    def __on_scene_change_callback(self, scene: EntityScene) -> None:
        """Called when the scene changes."""  # noqa: D401
        wanted_state = scene.get_attrs_at_time(self._get_time())
        # Update the entity with the new state
        self._update(wanted_state=wanted_state)

    # Timeshift ability
    def __on_timeshift_change_callback(self, time: int) -> None:
        """Called when the timeshift changes."""  # noqa: D401
        # Update the entity with the new state
        self._update(time=time)

    # State ability
    def _translate_state(  # Override if needed
        self, ha_state: str, ha_attributes: dict[str, Any]
    ) -> dict[type[Attr], Attr]:
        """Convert full Home Assistant state to a dict of Attrs important to this entity.

        This method is used to convert HA state to the internal state representation.
        Subclasses should ovreride this if they have a specific way of converting the state
        aka. rgbww lights that have color mode and temp mode...

        Raises KeyError if the attribute is not in the HA state.
        """
        state: dict[type[Attr], Attr] = {}

        for attr_type in self.SUPPORTED_ATTRIBUTES:
            if issubclass(attr_type, State):
                # If the attribute is a State, we can just use the state value
                state[attr_type] = attr_type(value=ha_state)
            elif attr_type.HASS_NAME in ha_attributes:
                # Create the attribute with its value
                state[attr_type] = attr_type(value=ha_attributes[attr_type.HASS_NAME])
            else:
                raise KeyError(
                    f"Entity {self._entity_id} does not have attribute {attr_type} in its state."
                )

        return state

    def __on_external_state_change_callback(
        self, state: dict[type[Attr], Attr]
    ) -> None:
        """When the external state changes.

        This method is used to put the entity into custom scene.
        """

        # Put the entity into custom scene
        self._scene_ability.set_custom_active(state)

    # Update abiliry
    @abstractmethod
    async def _set_entity_state(
        self, state: dict[type[Attr], Attr], context_creation_func: Callable[[], Context]
    ) -> None:  # Override
        """Update the entity with the given state.

        This method should call the appropreate Home Assistant service to update the entity state.
        """
