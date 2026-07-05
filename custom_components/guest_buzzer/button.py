"""Button: arm the buzzer."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    async_add_entities([BuzzerArmButton(coordinator, entry)])


class BuzzerArmButton(CoordinatorEntity, ButtonEntity):
    """Arms the buzzer window."""

    _attr_has_entity_name = True
    _attr_name = "Arm buzzer"
    _attr_icon = "mdi:bullhorn"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_arm"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Guest Access",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_arm()
