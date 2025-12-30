"""Constants for the MET Rain Risk integration."""

from __future__ import annotations

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.const import Platform

DOMAIN = "met_rain_risk"

VERSION = "0.1.0"

PROJECT_URL = "https://www.home-assistant.io/"

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_LOCATION = "location"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CONTACT = "contact"

DEFAULT_SCAN_INTERVAL_MINUTES = 10
# met.no requires a descriptive User-Agent, including contact info.
# You should customize this in the integration options.
DEFAULT_CONTACT = ""

MET_NO_LOCATIONFORECAST_COMPLETE_URL = (
    "https://api.met.no/weatherapi/locationforecast/2.0/complete"
)

ATTRIBUTION = "Data from MET Norway"

__all__ = [
    "ATTRIBUTION",
    "CONF_CONTACT",
    "CONF_LOCATION",
    "CONF_SCAN_INTERVAL",
    "DEFAULT_CONTACT",
    "DEFAULT_SCAN_INTERVAL_MINUTES",
    "DOMAIN",
    "PROJECT_URL",
    "VERSION",
    "MET_NO_LOCATIONFORECAST_COMPLETE_URL",
    "PLATFORMS",
    # re-export commonly used HA consts to keep our modules consistent
    "CONF_LATITUDE",
    "CONF_LONGITUDE",
]


