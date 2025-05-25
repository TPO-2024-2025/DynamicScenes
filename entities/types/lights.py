"""Light entity types."""

import asyncio
from collections.abc import Callable
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import Context

from ...attributes.types import Brightness, ColorTemp, LightState  # noqa: TID252
from ...constants import SERVICECALLS  # noqa: TID252
from .. import Entity  # noqa: TID252

if TYPE_CHECKING:
    from attributes import Attr

_LOGGER = logging.getLogger(__name__)


class Light(Entity):
    """A light entity."""

    SUPPORTED_ATTRIBUTES = {Brightness, LightState}

    DOMAIN = "light"

    @classmethod
    def supports(cls, domain: str, entity_id: str, attributes: dict[str, Any]) -> bool:
        """Check if the entity is a light without color / color temperature."""
        _LOGGER.debug(
            "Light: Checking if domain '%s', attributes '%s' is light entity.",
            domain,
            attributes
        )

        if domain != cls.DOMAIN:
            _LOGGER.debug(
                "Light: '%s' is not Light, domain missmatch (%s != %s).",
                entity_id,
                domain,
                cls.DOMAIN,
            )
            return False

        if "brightness" not in attributes:
            _LOGGER.debug(
                "Light: '%s' is not Light, missing brightness attribute.",
                entity_id,
            )
            return False

        if attributes.get("supported_color_modes"): # IS NOT empty or None
            _LOGGER.debug(
                "Light: '%s' is not Light, supports_color_modes.",
                entity_id,
            )
            return False

        _LOGGER.debug(
            "Light: '%s' is a Light entity.",
            entity_id,
        )
        return True

    async def _set_entity_state(
            self,
            state: dict[type['Attr'], 'Attr'],
            context_creation_func: Callable[[], Context],
    ) -> None:
        """Call the light.turn_on or light.turn_off service."""
        if (state.get(LightState) is None or state[LightState] == "on"):
            # If state is None or "on", turn on the light
            kwargs = {
                attr_type.HASS_NAME: attr.value for attr_type, attr in state.items()
                if attr_type != LightState
            }
            _LOGGER.info("Light: Turning on '%s' with attributes: %s", self.entity_id, kwargs)

            #kwargs[SERVICECALLS.ENTITY_ID] = self.entity_id
            # await self._hass.services.async_call( # CONTEXT!
            #     self.DOMAIN, "turn_on",
            #     {SERVICECALLS.ENTITY_ID: self.entity_id, **kwargs}
            # )

            # TODO: TEMPORARY FIX: Template lights only change one attribute at a time.
            for kwarg, data in kwargs.items():
                # Call with each attribute separately
                context = context_creation_func()
                await self._hass.services.async_call(
                    self.DOMAIN, "turn_on",
                    {kwarg: data},
                    context=context,
                    target={SERVICECALLS.ENTITY_ID: self.entity_id}
                )
                await asyncio.sleep(0.1)  # TODO: A rabm to?
            # Call just with entity_id to update the state
            context = context_creation_func()
            await self._hass.services.async_call(
                self.DOMAIN, "turn_on",
                context=context,
                target={SERVICECALLS.ENTITY_ID: self.entity_id}
            )
        else:
            # If state is "off", turn off the light
            _LOGGER.info("Light: Turning off '%s'", self.entity_id)
            context = context_creation_func()
            await self._hass.services.async_call(
                self.DOMAIN, "turn_off",
                context=context,
                target={SERVICECALLS.ENTITY_ID: self.entity_id},
            )
            # TODO: Add transition!

class WWLight(Light):
    """A light that supports color temperature."""

    SUPPORTED_ATTRIBUTES = {Brightness, LightState, ColorTemp}

    DOMAIN = "light"

    @classmethod
    def supports(cls, domain: str, entity_id: str, attributes: dict[str, Any]) -> bool:
        """Check if the entity is a color temperature light."""
        _LOGGER.debug("WWLight: Checking if domain '%s', attributes '%s' is "
                      "color temperature light entity.", domain, attributes)

        if domain != cls.DOMAIN:
            _LOGGER.debug(
                "WWLIGHT: '%s' is not WWLight, domain missmatch (%s != %s).",
                entity_id,
                domain,
                cls.DOMAIN,
                )
            return False

        if "brightness" not in attributes:
            _LOGGER.debug(
                "WWLIGHT: '%s' is not WWLight, missing brightness attribute.",
                entity_id,
            )
            return False

        if "color_temp" not in attributes:
            _LOGGER.debug(
                "WWLIGHT: '%s' is not WWLight, missing color_temp attribute.",
                entity_id,
            )
            return False

        supported_color_modes = attributes.get("supported_color_modes", [])
        if not supported_color_modes or "color_temp" not in supported_color_modes: # Hasnt got / ..
            _LOGGER.debug(
                "WWLIGHT: '%s' is not WWLight, missing color_temp in supported_color_modes.",
                entity_id,
            )
            return False

        _LOGGER.info(
            "WWLIGHT: '%s' is a WWLight entity.",
            entity_id,
        )
        return True
