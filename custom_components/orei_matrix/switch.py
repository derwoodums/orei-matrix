"""Power switch entity for the OREI Matrix integration."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OreiMatrixCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the OREI Matrix power switch."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OreiMatrixPowerSwitch(data["coordinator"], entry)])


class OreiMatrixPowerSwitch(CoordinatorEntity[OreiMatrixCoordinator], SwitchEntity):
    """Switch entity for matrix power on/off."""

    _attr_has_entity_name = True
    _attr_name = "Power"
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: OreiMatrixCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_power"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "OREI",
            "configuration_url": f"http://{self._entry.data['host']}",
        }

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("power")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.set_power(False)
        await self.coordinator.async_request_refresh()
