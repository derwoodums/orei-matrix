"""Binary sensor entities for OREI Matrix signal detection."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUM_INPUTS, NUM_OUTPUTS
from .coordinator import OreiMatrixCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up OREI Matrix signal detection binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OreiMatrixCoordinator = data["coordinator"]

    entities: list[BinarySensorEntity] = []

    # Input signal sensors
    for i in range(1, NUM_INPUTS + 1):
        name = _get_input_name(coordinator, i, f"Input {i}")
        entities.append(
            OreiMatrixInputSignal(coordinator, entry, i, f"{name} Signal")
        )

    # Output connection sensors
    for i in range(1, NUM_OUTPUTS + 1):
        name = _get_output_name(coordinator, i, f"Output {i}")
        entities.append(
            OreiMatrixOutputSignal(coordinator, entry, i, f"{name} Connected")
        )

    async_add_entities(entities)


def _get_input_name(coordinator, input_num, default):
    if coordinator.data:
        names = coordinator.data.get("input_names", {})
        if input_num in names and names[input_num]:
            return names[input_num]
    return default


def _get_output_name(coordinator, output_num, default):
    if coordinator.data:
        names = coordinator.data.get("output_names", {})
        name = names.get(output_num, "")
        if name and not name.lower().startswith("hdmi output"):
            return name
    return default


class OreiMatrixInputSignal(
    CoordinatorEntity[OreiMatrixCoordinator], BinarySensorEntity
):
    """Binary sensor for input active signal detection."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: OreiMatrixCoordinator,
        entry: ConfigEntry,
        input_num: int,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._input_num = input_num
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_input_{input_num}_signal"

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
        return self.coordinator.data.get("input_active", {}).get(self._input_num)


class OreiMatrixOutputSignal(
    CoordinatorEntity[OreiMatrixCoordinator], BinarySensorEntity
):
    """Binary sensor for output connection status."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: OreiMatrixCoordinator,
        entry: ConfigEntry,
        output_num: int,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._output_num = output_num
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_output_{output_num}_signal"

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
        return self.coordinator.data.get("output_connected", {}).get(self._output_num)
