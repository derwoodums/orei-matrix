"""OREI HDMI Matrix integration for Home Assistant."""

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .client import OreiMatrixClient
from .const import DOMAIN, PLATFORMS
from .coordinator import OreiMatrixCoordinator

_LOGGER = logging.getLogger(__name__)

CARD_JS = "orei-matrix-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_JS}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the Lovelace card as a frontend resource."""
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL, str(Path(__file__).parent / CARD_JS), False),
        ])
    except Exception:
        _LOGGER.warning("Could not register static path for Lovelace card")

    add_extra_js_url(hass, CARD_URL)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OREI Matrix from a config entry."""
    host = entry.data[CONF_HOST]
    client = OreiMatrixClient(host)

    coordinator = OreiMatrixCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload OREI Matrix config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
