"""Polling coordinator for the Guest Access Buzzer."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BuzzerCoordinator(DataUpdateCoordinator):
    """Polls /api/arm-status and triggers /api/arm."""

    def __init__(
        self, hass: HomeAssistant, base_url: str, key: str, scan_interval: int = DEFAULT_SCAN_INTERVAL
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._session = async_get_clientsession(hass)
        self.base_url = base_url.rstrip("/")
        self.key = key

    @property
    def status_url(self) -> str:
        return f"{self.base_url}/api/arm-status?key={self.key}"

    @property
    def arm_url(self) -> str:
        return f"{self.base_url}/api/arm?key={self.key}"

    async def _async_update_data(self) -> dict:
        try:
            async with asyncio.timeout(10):
                resp = await self._session.get(self.status_url)
                if resp.status == 401:
                    raise UpdateFailed("unauthorized — check the arm key")
                resp.raise_for_status()
                return await resp.json()
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"error fetching buzzer status: {err}") from err

    async def async_arm(self) -> None:
        """Arm the buzzer, then refresh state."""
        async with asyncio.timeout(10):
            resp = await self._session.get(self.arm_url)
            resp.raise_for_status()
        await self.async_request_refresh()
