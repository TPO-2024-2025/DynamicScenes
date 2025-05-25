"""Loading of the scenes, entities, order..."""

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .attributes import Attr, create_attr
from .constants import FILEPATH, YAMLDATA as YD
from .entities import Entity, create_entity
from .entity_scenes import AttrScene, EntityScene
from .errors import InputValidationError
from .utilities import to_seconds

_LOGGER = logging.getLogger(__name__)


async def _async_load_yaml(hass: HomeAssistant, file_path: Path) -> dict[str, Any]:
    """Load a YAML file and return its content as a dictionary.

    Raises FileNotFoundError if the file does not exist.
    Raises yaml.YAMLError if the file is not a valid YAML file.
    """
    try:

        def _read_file() -> dict[str, Any]:
            with file_path.open("r", encoding="utf-8") as file:
                return yaml.safe_load(file) or {}

        return await hass.async_add_executor_job(_read_file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File '{file_path}' not found.") from e
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file '{file_path}': {e}") from e

# ===== Entity loading =====

# Schema for validating scene configurations
ENTITY_ATTRIBUTES_SCHEMA = vol.Schema(
    {
        vol.Required(YD.ENTITIES): cv.ensure_list(cv.entity_id),
        # Lights
        vol.Optional(YD.ATTR.BRIGHTNESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(YD.ATTR.COLOR_TEMP): vol.All(
            vol.Coerce(int), vol.Range(min=153, max=500)
        ),
        vol.Optional(YD.ATTR.COLOR_MODE): cv.string,
        vol.Optional(YD.ATTR.XY_BRIGHTNESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(YD.ATTR.XY_COLOR): vol.All(
            vol.Length(min=2, max=2),
            [vol.All(vol.Coerce(float), vol.Range(min=0, max=1))],
        ),
    }
)

TIME_ENTRIES_SCHEMA = vol.Schema([ENTITY_ATTRIBUTES_SCHEMA])

SCENE_SCHEMA = vol.Schema(
    {
        vol.Required(YD.PRIORITY): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
        vol.Required(YD.TIMES): {
            str: TIME_ENTRIES_SCHEMA,
        },
    }
)

SCENES_SCHEMA = vol.Schema({cv.string: SCENE_SCHEMA})


def _invert_data(
    data: dict[str, Any],
) -> dict[str, dict[str, tuple[int, dict[str, list[tuple[int, Any]]]]]]:
    """Inverts scene-centric data to entity-centric data.

    Conveerted data str: {entity_id: {scene_name: (priority, {attr_name: [(time, value)]})}}

    Raises ValueError if the time string is not in HH:MM format.
    """
    inverted_data: dict[
        str, dict[str, tuple[int, dict[str, list[tuple[int, Any]]]]]
    ] = {}
    for _scene_name, _scene_data in data.items():
        scene_name: str = _scene_name
        priority: int = _scene_data[YD.PRIORITY]
        for _time_str, _time_entries in _scene_data[YD.TIMES].items():
            time: int = to_seconds(
                _time_str
            )  # Raises ValueError if time_str not in HH:MM format
            for _time_entry in _time_entries:
                attributes: dict[str, Any] = _time_entry.copy()
                _entities: list[str] = attributes.pop(YD.ENTITIES, [])
                for entity_id in _entities:
                    inverted_data.setdefault(entity_id, {})
                    inverted_data[entity_id].setdefault(scene_name, (priority, {}))
                    for _attr_name, _value in attributes.items():
                        attr_name: str = _attr_name
                        value: Any = _value
                        inverted_data[entity_id][scene_name][1].setdefault(
                            attr_name, []
                        )
                        inverted_data[entity_id][scene_name][1][attr_name].append(
                            (time, value)
                        )
    return inverted_data


def _create_entities(
    data: dict[str, dict[str, tuple[int, dict[str, list[tuple[int, Any]]]]]],
    hass: HomeAssistant,
) -> dict[str, Entity]:
    """Create Entity objects from inverted data.

    Raises ValueError if the attribute for the entity type does not exist OR
                      if the entity state is not found in Home Assistant.
    """
    entities: dict[str, Entity] = {}
    for entity_id, scenes in data.items():
        entity_scenes: set[EntityScene] = set()
        for scene_name, (priority, attributes) in scenes.items():
            attr_scenes: set[AttrScene] = set()
            for attr_name, times in attributes.items():
                attrs: list[Attr] = []
                for time, value in times:
                    # Create the attribute object
                    try:
                        attrs.append(create_attr(attr_name, value, time))
                    except InputValidationError as e:
                        _LOGGER.error(
                            "Input validation error for attribute '%s' in entity '%s': %s",
                            attr_name,
                            entity_id,
                            e,
                        )
                        continue
                    except ValueError as e:
                        _LOGGER.error(
                            "Error creating attribute '%s'for entity '%s': %s",
                            attr_name,
                            entity_id,
                            e,
                        )
                        continue
                # Create the AttrScene with the attributes
                try:
                    attr_scenes.add(AttrScene(attrs))
                except InputValidationError as e:
                    _LOGGER.error(
                        "Input validation error for attribute scene '%s' in entity '%s': %s",
                        attr_name,
                        entity_id,
                        e,
                    )
                    continue
            # Create the EntityScene with the attribute scenes
            try:
                entity_scenes.add(EntityScene(scene_name, priority, attr_scenes))
            except InputValidationError as e:
                _LOGGER.error(
                    "Input validation error for entity scene '%s' in entity '%s': %s",
                    scene_name,
                    entity_id,
                    e,
                )
                continue
        # Create the entity object
        try:
            entities[entity_id] = create_entity(entity_id, entity_scenes, hass)
        except InputValidationError as e:
            _LOGGER.error(
                "Input validation error for entity '%s': %s", entity_id, e
            )
            continue
        except ValueError as e:
            _LOGGER.error("Error creating entity '%s': %s", entity_id, e)
            continue


    return entities


async def async_load_entities(
    integration_dir: Path, hass: HomeAssistant
) -> dict[str, "Entity"]:
    """Load entities from a YAML file.

    Returns a dictionary of entity IDs to Entity objects.

    Raises FileNotFoundError if the file does not exist.
    Raises yaml.YAMLError if the file is not a valid YAML file.
    Raises vol.Invalid if the data does not match the expected schema.
    Raises InputValidationError if the entities are not valid.
    """
    # Get raw data
    raw_data = await _async_load_yaml(
        hass, integration_dir / FILEPATH.SCENES_FILE
    )  # Raises ...
    # Validate the data format
    validated_data = SCENES_SCHEMA(raw_data)  # type: ignore[] # Raises vol.Invalid
    # Invert the data to entity-centric format
    inverted_data = _invert_data(validated_data)  # type: ignore[] # Raises ValueError
    # Create Entity objects
    return _create_entities(inverted_data, hass)
