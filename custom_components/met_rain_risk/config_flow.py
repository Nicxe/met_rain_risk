"""Config flow for MET Rain Risk."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import (
    CONF_CONTACT,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_CONTACT,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)


def _location_to_lat_lon(location: dict[str, Any] | None) -> tuple[float, float]:
    location = location or {}
    lat = float(location.get("latitude"))
    lon = float(location.get("longitude"))
    return lat, lon


def _round_coord(value: float) -> float:
    # 4 decimals is ~11m for latitude; good enough to avoid duplicate entries
    return round(float(value), 4)

def _is_valid_contact(contact: str) -> bool:
    contact = (contact or "").strip()
    if not contact:
        return False
    # A pragmatic check: either an email-like string or a URL.
    return ("@" in contact and "." in contact) or contact.startswith("http")


class MetRainRiskConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MET Rain Risk."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                lat, lon = _location_to_lat_lon(user_input.get(CONF_LOCATION))
            except (TypeError, ValueError):
                errors["base"] = "invalid_location"
            else:
                contact = str(user_input.get(CONF_CONTACT, "")).strip()
                if not _is_valid_contact(contact):
                    errors["base"] = "invalid_contact"
                else:
                    unique = f"{_round_coord(lat)},{_round_coord(lon)}"
                    await self.async_set_unique_id(unique)
                    self._abort_if_unique_id_configured()

                    title = f"MET Rain Risk ({_round_coord(lat)},{_round_coord(lon)})"
                    data = {
                        CONF_LATITUDE: lat,
                        CONF_LONGITUDE: lon,
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                            )
                        ),
                        CONF_CONTACT: contact,
                    }
                    return self.async_create_entry(title=title, data=data)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LOCATION,
                    default={
                        "latitude": self.hass.config.latitude,
                        "longitude": self.hass.config.longitude,
                    },
                ): selector({"location": {}}),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_MINUTES
                ): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 60,
                            "step": 1,
                            "unit_of_measurement": "min",
                            "mode": "box",
                        }
                    }
                ),
                vol.Required(CONF_CONTACT, default=DEFAULT_CONTACT): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MetRainRiskOptionsFlowHandler(config_entry)


class MetRainRiskOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle MET Rain Risk options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # Home Assistant sets `config_entry` on the base class; it's read-only in newer HA.
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                lat, lon = _location_to_lat_lon(user_input.get(CONF_LOCATION))
            except (TypeError, ValueError):
                errors["base"] = "invalid_location"
            else:
                contact = str(user_input.get(CONF_CONTACT, "")).strip()
                if not _is_valid_contact(contact):
                    errors["base"] = "invalid_contact"
                else:
                    data = dict(self._config_entry.options)
                    data.update(
                        {
                            CONF_LATITUDE: lat,
                            CONF_LONGITUDE: lon,
                            CONF_SCAN_INTERVAL: int(
                                user_input.get(
                                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                                )
                            ),
                            CONF_CONTACT: contact,
                        }
                    )
                    return self.async_create_entry(title="", data=data)

        lat = float(
            self._config_entry.options.get(
                CONF_LATITUDE,
                self._config_entry.data.get(CONF_LATITUDE, self.hass.config.latitude),
            )
        )
        lon = float(
            self._config_entry.options.get(
                CONF_LONGITUDE,
                self._config_entry.data.get(CONF_LONGITUDE, self.hass.config.longitude),
            )
        )

        default_location = {"latitude": lat, "longitude": lon}

        default_scan = int(
            self._config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self._config_entry.data.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                ),
            )
        )
        default_contact = str(
            self._config_entry.options.get(
                CONF_CONTACT,
                self._config_entry.data.get(CONF_CONTACT, DEFAULT_CONTACT),
            )
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION, default=default_location): selector({"location": {}}),
                vol.Optional(CONF_SCAN_INTERVAL, default=default_scan): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 60,
                            "step": 1,
                            "unit_of_measurement": "min",
                            "mode": "box",
                        }
                    }
                ),
                vol.Required(CONF_CONTACT, default=default_contact): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


