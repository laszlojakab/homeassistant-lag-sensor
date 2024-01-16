"""Lag sensor integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """
    Initialize the lag sensor.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry which contains information gathered by the config flow.

    Returns:
        The value indicates whether the setup succeeded.
    """
    hass.async_create_task(hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS))
    config_entry.async_on_unload(config_entry.add_update_listener(config_entry_update_listener))

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
