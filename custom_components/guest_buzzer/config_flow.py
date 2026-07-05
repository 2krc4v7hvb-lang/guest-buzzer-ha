"""Config flow for the Guest Access Buzzer integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BASE_URL,
    CONF_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class BuzzerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """UI setup: enter the buzzer base URL and arm key."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BuzzerOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            base = user_input[CONF_BASE_URL].rstrip("/")
            key = user_input[CONF_KEY].strip()
            session = async_get_clientsession(self.hass)

            try:
                resp = await session.get(f"{base}/api/arm-status?key={key}")
                if resp.status == 401:
                    errors["base"] = "invalid_auth"
                else:
                    resp.raise_for_status()
                    data = await resp.json()
                    if "armed" not in data:
                        errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(base)
                self._abort_if_unique_id_configured()

                # Use the property's display name if available.
                title = "Guest Buzzer"
                try:
                    cfg = await (await session.get(f"{base}/api/config")).json()
                    if cfg.get("property_name"):
                        title = f"{cfg['property_name']} Buzzer"
                except Exception:  # noqa: BLE001
                    pass

                return self.async_create_entry(
                    title=title, data={CONF_BASE_URL: base, CONF_KEY: key}
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default="https://"): str,
                vol.Required(CONF_KEY): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class BuzzerOptionsFlow(config_entries.OptionsFlow):
    """Adjust the poll interval from the UI."""

    def __init__(self, config_entry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
