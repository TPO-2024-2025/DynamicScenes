"""The DynamicScenes integration for Home Assistant."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .config import Config
from .constants import HASSDATA, INTEGRATION_DOMAIN
from .coordinator import ServiceCoordinator, UpdateCoordinator
from .http_api import DynamicScenesDataView
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)


# ===== Setup and shutdown =====

def _setup_hass_data(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Set up the Home Assistant data structure for the integration."""
    hass.data.setdefault(INTEGRATION_DOMAIN, {})
    hass.data[INTEGRATION_DOMAIN].setdefault(entry_id, {})
    return hass.data[INTEGRATION_DOMAIN][entry_id]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the dynamic scenes integration."""
    _LOGGER.debug("INIT: Setting up dynamic scenes integration")

    hass_data = _setup_hass_data(hass, entry.entry_id)

    # Wait for 2 sec so the entities finish loadin TODO: BIG UF...
    await asyncio.sleep(2)

    # Create the config
    config = Config(entry, Path(__file__).parent, hass)
    await config.async_load_entities()

    hass_data[HASSDATA.CONFIG] = config

    # Register API endpoint
    hass.http.register_view(DynamicScenesDataView(hass, config))

    # Create service coordinator and register services
    service_coordinator = ServiceCoordinator(config)

    unregister_services = await async_register_services(hass, service_coordinator)
    hass_data[HASSDATA.UNREGISTER_SERVICES] = unregister_services

    # Create update coordinator, start it, store it.
    update_coordinator = UpdateCoordinator(config)
    update_coordinator.start_updates()

    hass_data[HASSDATA.UPDATE_COORDINATOR] = update_coordinator

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("INIT: Unloading dynamic scenes integration")

    hass_data = _setup_hass_data(hass, entry.entry_id)

    # Unregister services
    if HASSDATA.UNREGISTER_SERVICES in hass_data:
        hass_data[HASSDATA.UNREGISTER_SERVICES]()

    # Stop the update coordinator
    if HASSDATA.UPDATE_COORDINATOR in hass_data:
        hass_data[HASSDATA.UPDATE_COORDINATOR].stop_updates()

    # Clear the config
    if HASSDATA.CONFIG in hass_data:
        del hass_data[HASSDATA.CONFIG]

    return True
