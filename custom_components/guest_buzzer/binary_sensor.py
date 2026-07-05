"""Binary sensor: is the buzzer armed."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BuzzerArmedSensor(coordinator, entry)])


class BuzzerArmedSensor(CoordinatorEntity, BinarySensorEntity):
    """On while the buzzer's arm window is active."""

    _attr_has_entity_name = True
    _attr_name = "Armed"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_armed"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Guest Access",
        )

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("armed"))

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data or {}
        return {
            "seconds_remaining": d.get("seconds_remaining"),
            "window_seconds": d.get("window_seconds"),
            "buzzer_enabled": d.get("buzzer_enabled"),
        }
