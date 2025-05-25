"""A registry of all the attribute classes."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import Attr

_attr_registry: dict[str, type['Attr']] = {}

def register_attr(cls: type['Attr']) -> None:
    """Register an attribute class."""
    _attr_registry[cls.YAML_NAME] = cls

def create_attr(yaml_name: str, value: Any = None, time: int | None = None) -> 'Attr':
    """Create a scene attribute.

    Raises a ValueError if the attribute is not registered.
    Raises InvalidAttributeError if the attribute class is invalid.
    """
    # Get the attribute class from the registry
    if yaml_name not in _attr_registry:
        raise ValueError(f"{yaml_name} is not registered in the attribute registry.")
    attr_class = _attr_registry[yaml_name]

    # Create an instance of the attribute class
    return attr_class(value, time)
