"""Select entities for OREI Matrix output source selection."""

import asyncio
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUM_OUTPUTS
from .coordinator import OreiMatrixCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up OREI Matrix outputs as select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OreiMatrixCoordinator = data["coordinator"]

    entities = []
    for i in range(1, NUM_OUTPUTS + 1):
        name = _get_output_name(coordinator, i, f"Output {i}")
        entities.append(OreiMatrixOutputSelect(coordinator, entry, i, name))

    async_add_entities(entities)


def _get_output_name(
    coordinator: OreiMatrixCoordinator, output_num: int, default: str
) -> str:
    """Get output name from coordinator data, ignoring default device names."""
    if coordinator.data:
        names = coordinator.data.get("output_names", {})
        name = names.get(output_num, "")
        if name and not name.lower().startswith("hdmi output"):
            return name
    return default


class OreiMatrixOutputSelect(CoordinatorEntity[OreiMatrixCoordinator], SelectEntity):
    """Select entity representing one matrix output — pick which input it receives."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:video-input-hdmi"

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
        self._attr_unique_id = f"{entry.entry_id}_output_{output_num}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "OREI",
            "configuration_url": f"http://{self._entry.data['host']}",
        }

    @property
    def options(self) -> list[str]:
        """Return list of available input names."""
        if self.coordinator.data is None:
            return [f"Input {i}" for i in range(1, 5)]
        input_names = self.coordinator.data.get("input_names", {})
        if input_names:
            return [input_names[k] for k in sorted(input_names)]
        return [f"Input {i}" for i in range(1, 5)]

    @property
    def current_option(self) -> str | None:
        """Return the name of the currently routed input."""
        if self.coordinator.data is None:
            return None
        routing = self.coordinator.data.get("routing", {})
        input_num = routing.get(self._output_num)
        if input_num is None:
            return None
        input_names = self.coordinator.data.get("input_names", {})
        return input_names.get(input_num, f"Input {input_num}")

    async def async_select_option(self, option: str) -> None:
        """Route the selected input to this output."""
        input_num = self._resolve_input_num(option)
        if input_num is None:
            _LOGGER.warning("Unknown source '%s' for %s", option, self.name)
            return

        _LOGGER.debug(
            "Switching output %d to input %d (%s)",
            self._output_num, input_num, option,
        )
        resp = await self.coordinator.client.video_switch(input_num, self._output_num)
        _LOGGER.debug("video switch response: %s", resp)

        # Optimistic update
        if self.coordinator.data:
            self.coordinator.data["routing"][self._output_num] = input_num
            self.async_write_ha_state()

        await asyncio.sleep(0.5)
        await self.coordinator.async_request_refresh()

    def _resolve_input_num(self, source_name: str) -> int | None:
        """Resolve a source name to its 1-based input number."""
        if self.coordinator.data is None:
            return None
        input_names = self.coordinator.data.get("input_names", {})
        for num, name in input_names.items():
            if name == source_name:
                return num
        if source_name.startswith("Input "):
            try:
                return int(source_name.split()[-1])
            except ValueError:
                pass
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Expose output connection status as an attribute."""
        attrs = {"output_number": self._output_num}
        if self.coordinator.data:
            connected = self.coordinator.data.get("output_connected", {})
            if self._output_num in connected:
                attrs["signal_connected"] = connected[self._output_num]
        return attrs
