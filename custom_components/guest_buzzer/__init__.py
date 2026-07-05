"""The Guest Access Buzzer integration."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging

from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BASE_URL,
    CONF_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import BuzzerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = BuzzerCoordinator(
        hass, entry.data[CONF_BASE_URL], entry.data[CONF_KEY], scan_interval
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register a webhook for instant (push) updates, then tell the backend its URL.
    webhook_id = entry.data.get("webhook_id")
    if webhook_id:
        webhook.async_register(
            hass, DOMAIN, "Guest Access Buzzer", webhook_id,
            _make_webhook_handler(coordinator, entry.data[CONF_KEY]),
        )
        await _register_with_backend(hass, entry, webhook_id)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_id = entry.data.get("webhook_id")
    if webhook_id:
        webhook.async_unregister(hass, webhook_id)
        await _register_with_backend(hass, entry, None)  # clear it on the backend

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change (picks up a new poll interval)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _register_with_backend(hass, entry, webhook_id) -> None:
    """Send (or clear) our webhook URL to the backend."""
    base = entry.data[CONF_BASE_URL].rstrip("/")
    key = entry.data[CONF_KEY]
    try:
        url = webhook.async_generate_url(hass, webhook_id) if webhook_id else ""
    except Exception:  # noqa: BLE001
        _LOGGER.warning("No external URL configured — push disabled, polling only")
        return
    try:
        session = async_get_clientsession(hass)
        await session.post(f"{base}/api/ha-webhook?key={key}", json={"url": url})
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Could not register push webhook: %s", err)


def _make_webhook_handler(coordinator: BuzzerCoordinator, key: str):
    """Build the webhook receiver, verifying the HMAC signature with the key."""

    async def handler(hass, webhook_id, request):
        body = await request.read()
        sig = request.headers.get("X-Buzzer-Signature", "")
        expected = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return web.Response(status=401)
        try:
            data = json.loads(body)
        except ValueError:
            return web.Response(status=400)
        coordinator.apply_push(data)
        return web.Response(status=200)

    return handler
