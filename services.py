"""API setup for the services of the Dynamic Scenes integration."""

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .constants import INTEGRATION_DOMAIN, SERVICEDATA, SERVICENAME
from .coordinator import ServiceCoordinator

_LOGGER = logging.getLogger(__name__)

# Entty_ids and scene name
ENTITY_SCENE_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_IDS): cv.entity_ids,  # type: ignore
        vol.Required(SERVICEDATA.SCENE): cv.string,
    }
)

# Only entity_ids
ENTITY_ONLY_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_IDS): cv.entity_ids,  # type: ignore
    }
)

# For setting timeshift
ENTITY_TIMESHIFT_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_IDS): cv.entity_ids,  # type: ignore
        vol.Required(SERVICEDATA.TIMESHIFT): vol.All(
            vol.Coerce(int),
            vol.Range(min=-720, max=720),  # -12h to +12h in minutes
        ),
    }
)

# For shifting timeshift
ENTITY_SHIFT_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_IDS): cv.entity_ids,  # type: ignore
        vol.Required(SERVICEDATA.SHIFT): vol.All(
            vol.Coerce(int),
            vol.Range(min=-720, max=720),  # -12h to +12h in minutes
        ),
    }
)


async def async_register_services(hass: HomeAssistant, sc: ServiceCoordinator):
    """Register services for the integration.

    Returns: The function to unregister the services.
    """

    _LOGGER.debug("SERVICES: Registering services")

    # ===== Scenes =====

    async def handle_set_scene_condition_met(call: ServiceCall) -> None:
        """Tells the integration that the conditions for some scene are met."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_IDS, [])
        scene: str = call.data.get(SERVICEDATA.SCENE, "Unknown")
        sc.set_scene_active(entity_ids, scene)

    async def handle_unset_scene_condition_met(call: ServiceCall):
        """Tells the integration that the conditions for some scene are not met anymore."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_IDS, [])
        scene: str = call.data.get(SERVICEDATA.SCENE, "Unknown")
        sc.set_scene_inactive(entity_ids, scene)

    # ===== Custom Scenes =====

    async def handle_stop_adjustments(call: ServiceCall):
        """Reset the scene from custom to the currently active scene."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_IDS, [])
        sc.set_custom_active(entity_ids)

    async def handle_continue_adjustments(call: ServiceCall):
        """Reset the scene from custom to the currently active scene."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_IDS, [])
        sc.set_custom_inactive(entity_ids)

    # ===== Timeshifts =====

    async def handle_set_timeshift(call: ServiceCall):
        """Set the timeshift of entities."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_IDS, [])
        timeshift: int = call.data.get(SERVICEDATA.TIMESHIFT, -1)
        sc.set_timeshift(entity_ids, timeshift)

    async def handle_shift_time(call: ServiceCall):
        """Shift the timeshift of entities."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_IDS, [])
        shift: int = call.data.get(SERVICEDATA.SHIFT, -1)
        sc.shift_timeshift(entity_ids, shift)

    # ===== Register the services =====

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.SET_SCENE_CONDITION_MET,
        handle_set_scene_condition_met,
        schema=ENTITY_SCENE_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.UNSET_SCENE_CONDITION_MET,
        handle_unset_scene_condition_met,
        schema=ENTITY_SCENE_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.CONTINUE_ADJUSTMENTS,
        handle_continue_adjustments,
        schema=ENTITY_ONLY_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.STOP_ADJUSTMENTS,
        handle_stop_adjustments,
        schema=ENTITY_ONLY_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.SET_TIMESHIFT,
        handle_set_timeshift,
        schema=ENTITY_TIMESHIFT_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.SHIFT_TIME,
        handle_shift_time,
        schema=ENTITY_SHIFT_SCHEMA,
    )

    # Return an unregister function
    return lambda: unregister_services(hass)


async def unregister_services(hass: HomeAssistant):
    """Unregister services."""
    hass.services.async_remove(INTEGRATION_DOMAIN, SERVICENAME.SET_SCENE_CONDITION_MET)

    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.UNSET_SCENE_CONDITION_MET
    )

    hass.services.async_remove(INTEGRATION_DOMAIN, SERVICENAME.STOP_ADJUSTMENTS)

    hass.services.async_remove(INTEGRATION_DOMAIN, SERVICENAME.CONTINUE_ADJUSTMENTS)

    hass.services.async_remove(INTEGRATION_DOMAIN, SERVICENAME.SET_TIMESHIFT)

    hass.services.async_remove(INTEGRATION_DOMAIN, SERVICENAME.SHIFT_TIME)
