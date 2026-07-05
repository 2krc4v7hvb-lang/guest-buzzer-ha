"""Polling + push coordinator for the Guest Access Buzzer."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BuzzerCoordinator(DataUpdateCoordinator):
    """Polls /api/arm-status, triggers /api/arm, and accepts push updates."""

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
        self._unsub_expiry = None

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

    @callback
    def apply_push(self, data: dict) -> None:
        """Apply a pushed state change immediately (from the webhook)."""
        armed = bool(data.get("armed"))
        secs = int(data.get("seconds_remaining") or 0)
        new = dict(self.data or {})
        new["armed"] = armed
        new["seconds_remaining"] = secs if armed else 0
        self.async_set_updated_data(new)

        if self._unsub_expiry is not None:
            self._unsub_expiry()
            self._unsub_expiry = None
        if armed and secs > 0:
            # Push tells us when it ends; flip off locally at that time (polling
            # is still the fallback if this is missed).
            self._unsub_expiry = async_call_later(self.hass, secs, self._expire)

    @callback
    def _expire(self, _now) -> None:
        self._unsub_expiry = None
        new = dict(self.data or {})
        new["armed"] = False
        new["seconds_remaining"] = 0
        self.async_set_updated_data(new)
