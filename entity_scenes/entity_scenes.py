"""A scene of all attributes of an entity."""

import bisect

from ..attributes import Attr  # noqa: TID252
from ..constants import MAX_PRIORITY, SCENE  # noqa: TID252
from ..errors import InputValidationError  # noqa: TID252


class AttrScene:
    """Class to represent a scene for one attribute of one entity."""

    # ===== Initialization and validation =====

    @staticmethod
    def _validate_attr_scene(attr_scene: list[Attr]) -> None:
        """Validate all stuff in attr_scene, so this class can funciton propperly.

        Raises InputValidationError if the scene is not valid.
        """
        # At least one attribute
        if len(attr_scene) == 0:
            raise InputValidationError(
                "Attribute scene must have at least one attribute."
            )

        for i, attr in enumerate(attr_scene):
            # Times are in ascelerating order
            if i != 0 and attr_scene[i - 1].time >= attr.time:
                raise InputValidationError(
                    f"Time {attr.time} for attribute {attr} is lower then previous time."
                )

            # All attributes are of the same type
            if not isinstance(attr, attr_scene[0].__class__):
                raise InputValidationError(
                    f"Attribute {attr} is not of the same type as first attribute."
                )

    def __init__(self, attr_scene: list[Attr] | None = None) -> None:
        """Initialize the attributes scene."""
        self._attr_scene = attr_scene if attr_scene is not None else []
        self._times = [attr.time for attr in self._attr_scene]
        # Validate the attributes scene
        self._validate_attr_scene(self._attr_scene)

    # ===== Properties =====

    @property
    def type(self) -> type[Attr]:
        """Get the type of attributes in this attr scene."""
        return type(self._attr_scene[0])  # Validated that all the same type

    # ===== Getting attributes at times =====

    def get_attr_at_time(self, time: int) -> Attr:
        """Get the value of an attribute at a specific time."""
        # attr_scene has at least one attribute, and is formatted correctly
        idx = bisect.bisect_right(self._times, time)  # Rerturns index of next time!
        attr_scene = self._attr_scene

        if idx == 0 or idx == len(attr_scene):
            # Time is between the last and first attribute
            prev_attr = attr_scene[-1]  # Before midnight
            next_attr = attr_scene[0]  # After midnight
        else:
            # Time is between two attributes
            prev_attr = attr_scene[idx - 1]
            next_attr = attr_scene[idx]

        # Interpolate the new Attr
        return prev_attr.interpolate(
            next_attr, time
        )  # Ignore this raise as it is impossible.

    # ===== Helpers =====

    def __eq__(self, other: object) -> bool:
        """Check if this attribute scene is equal to another."""
        # Same type
        if not isinstance(other, type(self)):
            return False
        # Same lenght of scene
        if len(self._attr_scene) != len(other._attr_scene):
            return False
        for i, attr in enumerate(self._attr_scene):
            # Same attribute at the same index
            if not attr == other._attr_scene[i]:
                return False
        return True

    def __hash__(self) -> int:
        """Return a hash of the attribute scene."""
        return hash(tuple(self._attr_scene))

    def __repr__(self) -> str:
        """Return a string representation of the attribute scene."""
        return (
            "<ATTR_SCENE(" + ", ".join([repr(attr) for attr in self._attr_scene]) + ")>"
        )


class EntityScene:
    """A scene of all attributes of an entity."""

    # ===== Initialization and validation =====

    @staticmethod
    def _validate_priority(name: str, priority: int) -> None:
        """Validate the priority of this scene.

        Throws a InputValidationError if the priority is not valid.
        """
        # If this is the custom scene, it must have priority MAX_PRIORITY
        if name == SCENE.CUSTOM and priority != MAX_PRIORITY:
            raise InputValidationError(
                f"Custom scene must have priority {MAX_PRIORITY}, not {priority}."
            )
        if name != SCENE.CUSTOM and not 0 <= priority <= MAX_PRIORITY:
            raise InputValidationError(
                f"Priority {priority} is not in range 0-{MAX_PRIORITY - 1}."
            )

    @staticmethod
    def _validate_scene(scene: set[AttrScene]) -> None:
        """Validate the scene of this entity.

        Throws a InputValidationError if the scene is not valid.
        """
        # At least one attribute
        if len(scene) == 0:
            raise InputValidationError("Scene must have at least one attribute.")

        # No AttrScene has the same type as another
        for i, attr_scene_1 in enumerate(scene):
            for j, attr_scene_2 in enumerate(scene):
                if i != j and not isinstance(attr_scene_1, type(attr_scene_2)):
                    raise InputValidationError(
                        f"Attribute {attr_scene_1} is the same as {attr_scene_2}."
                    )

    def __init__(self, name: str, priority: int, scene: set[AttrScene]) -> None:
        """Initialize the entitys scene."""
        # Set and validate
        self._name = name
        self._priority = priority

        # Validate the scene
        try:
            self._validate_priority(self._name, self._priority)
            self._validate_scene(scene)
        except InputValidationError as err:
            raise InputValidationError(
                f"{self._name} (p={self._priority}, s={scene}): {err}"
            ) from err

        # Make dict, keys are attr types
        self._scene = {attr_scene.type: attr_scene for attr_scene in scene}

    # ===== Properties =====

    @property
    def name(self) -> str:
        """Get the name of the scene."""
        return self._name

    @property
    def priority(self) -> int:
        """Get the priority of the scene."""
        return self._priority

    @property
    def attributes(self) -> set[type[Attr]]:
        """Get the attributes of this scene.

        Returns a set of attribute types.
        """
        return set(self._scene.keys())

    # ===== Getting attributes at times =====

    def get_attrs_at_time(self, time: int) -> dict[type[Attr], Attr]:
        """Get the value of this scenes attributes at a specific time.

        Returns a dict of attribute types and their values at the given time.
        """
        # attr_scene has at least one attribute, and is formatted correctly
        attrs: dict[type[Attr], Attr] = {}
        for attr_type, attr_scene in self._scene.items():
            attrs[attr_type] = attr_scene.get_attr_at_time(time)
        return attrs

    # ===== Other =====
    def __eq__(self, other: object) -> bool:
        """Check if this entity scene is equal to another."""
        # Same type
        if not isinstance(other, type(self)):
            return False
        # Same name and priority
        if self._name != other._name or self._priority != other._priority:
            return False
        # Same lenght of attribute scenes
        if len(self._scene) != len(other._scene):
            return False
        # Same attribute scenes
        for attr_type, attr_scene in self._scene.items():
            if (
                attr_type not in other._scene
                or not attr_scene == other._scene[attr_type]
            ):
                return False
        return True

    def __hash__(self) -> int:
        """Return a hash of the entity scene."""
        return hash((self._name, self._priority, frozenset(self._scene.items())))

    def __repr__(self) -> str:
        """Return a string representation of the entity scene."""
        return f"<ENTITY_SCENE({self._name}, {self._priority}, scene={self._scene})>"
