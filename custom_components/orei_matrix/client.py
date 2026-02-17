"""Async HTTP client for OREI UHD44-EXB400R-K matrix switcher."""

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_PATH, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class OreiMatrixClient:
    """HTTP client for the OREI matrix CGI API."""

    def __init__(self, host: str, port: int = 80) -> None:
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}{API_PATH}"

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to the matrix API and return JSON response."""
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self._base_url, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    _LOGGER.debug("API %s -> %s", payload.get("comhead"), data)
                    return data
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to OREI matrix at %s", self._host)
            raise ConnectionError(f"Timeout connecting to {self._host}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to OREI matrix at %s: %s", self._host, err)
            raise ConnectionError(f"Cannot connect to {self._host}: {err}") from err

    # ── Status queries ──────────────────────────────────────────────

    async def get_status(self) -> dict[str, Any]:
        """Get device info: model, firmware, IP, MAC."""
        return await self._request({"comhead": "get status", "language": 0})

    async def get_video_status(self) -> dict[str, Any]:
        """Get routing map, input/output names, preset names, power state."""
        return await self._request({"comhead": "get video status", "language": 0})

    async def get_output_status(self) -> dict[str, Any]:
        """Get output signal detection, stream enables, scaler, HDCP."""
        return await self._request({"comhead": "get output status", "language": 0})

    async def get_input_status(self) -> dict[str, Any]:
        """Get input EDID and active signal info."""
        return await self._request({"comhead": "get input status", "language": 0})

    # ── Commands ────────────────────────────────────────────────────

    async def video_switch(self, input_num: int, output_num: int) -> dict[str, Any]:
        """Route an input to an output.

        Args:
            input_num: 1-based input number (1-4).
            output_num: 1-based output number (1-8, where 1-4=HDMI, 5-8=HDBaseT).
        """
        return await self._request({
            "comhead": "video switch",
            "language": 0,
            "source": [input_num, output_num],
        })

    async def set_power(self, on: bool) -> dict[str, Any]:
        """Turn matrix power on (1) or off (0)."""
        return await self._request({
            "comhead": "set poweronoff",
            "language": 0,
            "power": 1 if on else 0,
        })

    # ── Validation ──────────────────────────────────────────────────

    async def validate_connection(self) -> dict[str, Any]:
        """Test connectivity and return device status. Raises on failure."""
        return await self.get_status()
