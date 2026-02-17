"""DataUpdateCoordinator for the OREI Matrix integration."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import OreiMatrixClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class OreiMatrixCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the OREI matrix for current state."""

    def __init__(self, hass: HomeAssistant, client: OreiMatrixClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the matrix device."""
        try:
            video = await self.client.get_video_status()
            output = await self.client.get_output_status()
            input_st = await self.client.get_input_status()
        except ConnectionError as err:
            raise UpdateFailed(f"Error communicating with OREI matrix: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        # Power state (present in all responses)
        power = video.get("power", 0)

        # Routing: "allsource" = [1, 2, 2, 1, 0] — input per output, trailing 0
        # 4 logical outputs (HDMI + HDBaseT mirror the same routing)
        routing = {}
        allsource = video.get("allsource", [])
        for idx, src in enumerate(allsource):
            if src == 0:  # trailing sentinel
                break
            routing[idx + 1] = src

        # Input names: "allinputname" = ["input1", "input2", "input3", "input4"]
        input_names = {}
        for idx, name in enumerate(video.get("allinputname", [])):
            input_names[idx + 1] = name

        # Output names: use HDMI names as the canonical output names
        output_names = {}
        for idx, name in enumerate(video.get("alloutputname", [])):
            output_names[idx + 1] = name

        # Input signal detection: "inactive" = [1, 0, 0, 0]
        # Per-index: 1 = no signal (inactive), 0 = has signal (active)
        input_active = {}
        inactive_arr = input_st.get("inactive", [])
        for idx, val in enumerate(inactive_arr):
            input_active[idx + 1] = val == 0

        # Output connection: combine HDMI and HDBaseT — connected if either has signal
        output_connected = {}
        hdmi_conn = output.get("allconnect", [])
        hdbt_conn = output.get("allhdbtconnect", [])
        for idx in range(max(len(hdmi_conn), len(hdbt_conn))):
            hdmi_val = hdmi_conn[idx] if idx < len(hdmi_conn) else 0
            hdbt_val = hdbt_conn[idx] if idx < len(hdbt_conn) else 0
            output_connected[idx + 1] = bool(hdmi_val or hdbt_val)

        return {
            "power": bool(power),
            "routing": routing,
            "input_names": input_names,
            "output_names": output_names,
            "input_active": input_active,
            "output_connected": output_connected,
            "video_raw": video,
            "output_raw": output,
            "input_raw": input_st,
        }
