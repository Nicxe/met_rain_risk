"""The MET Rain Risk integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CONTACT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_CONTACT,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import MetRainRiskCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (YAML is not supported; config entries only)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MET Rain Risk from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    lat = float(entry.options.get(CONF_LATITUDE, entry.data.get(CONF_LATITUDE, hass.config.latitude)))
    lon = float(entry.options.get(CONF_LONGITUDE, entry.data.get(CONF_LONGITUDE, hass.config.longitude)))
    contact = str(entry.options.get(CONF_CONTACT, entry.data.get(CONF_CONTACT, DEFAULT_CONTACT)))
    scan_minutes = int(
        entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
    )

    coordinator = MetRainRiskCoordinator(
        hass=hass,
        latitude=lat,
        longitude=lon,
        contact=contact,
        update_interval=timedelta(minutes=scan_minutes),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.error(
            "Failed to set up %s (%s): %s",
            DOMAIN,
            entry.title,
            ex,
            exc_info=True,
        )
        raise ConfigEntryNotReady from ex

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    async def _options_updated(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        new_lat = float(
            updated_entry.options.get(
                CONF_LATITUDE,
                updated_entry.data.get(CONF_LATITUDE, hass.config.latitude),
            )
        )
        new_lon = float(
            updated_entry.options.get(
                CONF_LONGITUDE,
                updated_entry.data.get(CONF_LONGITUDE, hass.config.longitude),
            )
        )
        new_contact = str(
            updated_entry.options.get(
                CONF_CONTACT,
                updated_entry.data.get(CONF_CONTACT, DEFAULT_CONTACT),
            )
        )
        new_scan_minutes = int(
            updated_entry.options.get(
                CONF_SCAN_INTERVAL,
                updated_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
            )
        )

        coordinator.set_config(
            latitude=new_lat,
            longitude=new_lon,
            contact=new_contact,
            update_interval=timedelta(minutes=new_scan_minutes),
        )
        await coordinator.async_request_refresh()

    entry.async_on_unload(entry.add_update_listener(_options_updated))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


