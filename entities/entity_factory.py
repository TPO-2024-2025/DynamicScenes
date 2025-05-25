"""A registry of all the entity classes."""

from typing import TYPE_CHECKING, Any, cast

from homeassistant.core import HomeAssistant

from ..entity_scenes import EntityScene  # noqa: TID252

if TYPE_CHECKING:
    from .base import Entity


_entity_registry: set[type['Entity']] = set()

def register_entity(cls: type['Entity']) -> None:
    """Register an entity class."""
    # Add to the set
    _entity_registry.add(cls)

def create_entity(
        entity_id: str,
        scene: set[EntityScene],
        hass: HomeAssistant
) -> 'Entity':
    """Create an entity from a state dict.

    Raises a ValueError if no entity class is registered for the entity type OR
                        if the entity state is not found in Home Assistant.
    Raises InvalidAttributeError if the entity class is invalid.
    """
    hass_state = hass.states.get(entity_id)  # Get the entity state
    if hass_state is None:
        raise ValueError(f"Entity with ID '{entity_id}' does not exist in Home Assistant.")

    attributes = cast("dict[str, Any]", hass_state.attributes) # type: ignore[]
    if not attributes:
        raise ValueError(f"Entity with ID '{entity_id}' has no attributes.")

    domain = hass_state.domain

    supported_entities = [
        entity for entity in _entity_registry if entity.supports(domain, entity_id, attributes)
    ]

    if len(supported_entities) == 0:
        raise ValueError(f"No entity class registered for {hass_state.entity_id}")
    if len(supported_entities) > 1:
        raise ValueError(f"Multiple entity classes registered for {hass_state.entity_id}")
    # Create the entity
    return supported_entities[0](entity_id, scene, hass)
