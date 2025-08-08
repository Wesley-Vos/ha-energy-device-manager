"""The Energy device monitor integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import CONF_HIGH_TARIFF_ENTITY, CONF_LOW_TARIFF_ENTITY

_PLATFORMS: list[Platform] = [Platform.SENSOR]

type EnergyDeviceMonitorConfigEntry = ConfigEntry[Controller]


async def async_setup_entry(
    hass: HomeAssistant, entry: EnergyDeviceMonitorConfigEntry
) -> bool:
    """Set up Energy device monitor from a config entry."""

    try:
        i = 0
    except Exception as ex:
        raise ConfigEntryError("Cannot setup controller") from ex

    entry.runtime_data = None

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_update_entry(
    hass: HomeAssistant, entry: EnergyDeviceMonitorConfigEntry
) -> None:
    """Update entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: EnergyDeviceMonitorConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
