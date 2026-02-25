"""OREI HDMI Matrix integration for Home Assistant."""

import json
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
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    version = manifest.get("version", "0")
    versioned_url = f"{CARD_URL}?v={version}"

    # Serve the JS file at /orei_matrix/orei-matrix-card.js
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL, str(Path(__file__).parent / CARD_JS), False),
        ])
    except Exception:
        _LOGGER.warning("Could not register static path for Lovelace card")

    # Primary: register as a proper Lovelace resource (survives restarts)
    await _register_card_resource(hass, versioned_url)

    # Fallback: also inject via add_extra_js_url for immediate availability
    add_extra_js_url(hass, versioned_url)

    return True


async def _register_card_resource(hass: HomeAssistant, url: str) -> None:
    """Safely add the card JS to Lovelace resources if not already present."""
    try:
        resources = hass.data.get("lovelace", {}).get("resources")
        if resources is None:
            _LOGGER.debug("Lovelace resources collection not available")
            return

        # Check if any orei_matrix resource already exists
        for item in resources.async_items():
            existing_url = item.get("url", "")
            if DOMAIN in existing_url and CARD_JS in existing_url:
                # Update the URL if version changed, otherwise leave it alone
                if existing_url != url:
                    await resources.async_update_item(
                        item["id"], {"url": url}
                    )
                    _LOGGER.info("Updated Lovelace resource to: %s", url)
                return

        # Not found — add it
        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.info("Registered Lovelace resource: %s", url)
    except Exception:
        _LOGGER.debug("Could not auto-register Lovelace resource", exc_info=True)


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
