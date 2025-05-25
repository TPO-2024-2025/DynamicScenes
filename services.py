"""API setup for the services of the Dynamic Scenes integration."""

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .constants import INTEGRATION_DOMAIN, SERVICEDATA, SERVICENAME
from .coordinator import ServiceCoordinator

_LOGGER = logging.getLogger(__name__)

# Schema definitions for service validation
SCENE_CONDITION_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_ID): cv.entity_ids,  # type: ignore[]
        vol.Required(SERVICEDATA.SCENE): cv.string,
    }
)

RESET_CUSTOM_SCENE_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_ID): cv.entity_ids,  # type: ignore[]
    }
)

ADJUSTMENTS_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_ID): cv.entity_ids,  # type: ignore[]
    }
)

SET_TIMESHIFT_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_ID): cv.entity_ids,  # type: ignore[]
        vol.Required(SERVICEDATA.TIMESHIFT): cv.positive_int,
    }
)

SHIFT_TIMESHIFT_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICEDATA.ENTITY_ID): cv.entity_ids,  # type: ignore[]
        vol.Required(SERVICEDATA.SHIFT): cv.positive_int,
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
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_ID)  # type: ignore[]
        scene: str = call.data.get(SERVICEDATA.SCENE)  # type: ignore[]
        sc.set_scene_active(entity_ids, scene)

    async def handle_unset_scene_condition_met(call: ServiceCall):
        """Tells the integration that the conditions for some scene are not met anymore."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_ID)  # type: ignore[]
        scene: str = call.data.get(SERVICEDATA.SCENE)  # type: ignore[]
        sc.set_scene_inactive(entity_ids, scene)

    # ===== Custom Scenes =====

    async def handle_stop_adjustments(call: ServiceCall):
        """Reset the scene from custom to the currently active scene."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_ID)  # type: ignore[]
        sc.set_custom_active(entity_ids)

    async def handle_continue_adjustments(call: ServiceCall):
        """Reset the scene from custom to the currently active scene."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_ID)  # type: ignore[]
        sc.set_custom_inactive(entity_ids)

    # ===== Timeshifts =====

    async def handle_set_timeshift(call: ServiceCall):
        """Set the timeshift of entities."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_ID)  # type: ignore[]
        timeshift: int = call.data.get(SERVICEDATA.TIMESHIFT)  # type: ignore[]
        sc.set_timeshift(entity_ids, timeshift)

    async def handle_shift_time(call: ServiceCall):
        """Shift the timeshift of entities."""
        entity_ids: list[str] = call.data.get(SERVICEDATA.ENTITY_ID)  # type: ignore[]
        shift: int = call.data.get(SERVICEDATA.SHIFT)  # type: ignore[]
        sc.shift_timeshift(entity_ids, shift)

    # ===== Register the services =====

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.SET_SCENE_CONDITION_MET,
        handle_set_scene_condition_met,
        schema=SCENE_CONDITION_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.UNSET_SCENE_CONDITION_MET,
        handle_unset_scene_condition_met,
        schema=SCENE_CONDITION_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.CONTINUE_ADJUSTMENTS,
        handle_continue_adjustments,
        schema=ADJUSTMENTS_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.STOP_ADJUSTMENTS,
        handle_stop_adjustments,
        schema=ADJUSTMENTS_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.SET_TIMESHIFT,
        handle_set_timeshift,
        schema=SET_TIMESHIFT_SCHEMA,
    )

    hass.services.async_register(
        INTEGRATION_DOMAIN,
        SERVICENAME.SHIFT_TIME,
        handle_shift_time,
        schema=SHIFT_TIMESHIFT_SCHEMA,
    )

    # Return an unregister function
    return lambda: unregister_services(hass)


async def unregister_services(hass: HomeAssistant):
    """Unregister services."""
    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.SET_SCENE_CONDITION_MET
    )

    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.UNSET_SCENE_CONDITION_MET
    )

    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.STOP_ADJUSTMENTS
    )

    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.CONTINUE_ADJUSTMENTS
    )

    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.SET_TIMESHIFT
    )

    hass.services.async_remove(
        INTEGRATION_DOMAIN, SERVICENAME.SHIFT_TIME
    )
