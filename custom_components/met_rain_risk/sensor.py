"""Sensor platform for MET Rain Risk."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MetRainRiskCoordinator, MetRainRiskData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor(s) from a config entry."""
    coordinator: MetRainRiskCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([MetRainRiskSensor(entry, coordinator)])


class MetRainRiskSensor(CoordinatorEntity[MetRainRiskCoordinator], SensorEntity):
    """Sensor exposing rain risk for next 12 hours."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-rainy"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: ConfigEntry, coordinator: MetRainRiskCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_rain_risk_12h"
        self._attr_name = "Rain risk (next 12h)"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="MET Norway",
            model="Locationforecast 2.0",
        )

    @property
    def native_value(self) -> float | None:
        data: MetRainRiskData | None = self.coordinator.data
        if not data or data.max_probability_12h is None:
            return None
        # Keep as float; HA will render nicely
        return round(float(data.max_probability_12h), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data: MetRainRiskData | None = self.coordinator.data
        if not data:
            return {"attribution": ATTRIBUTION}

        attrs: dict[str, Any] = {
            "attribution": ATTRIBUTION,
            "latitude": data.latitude,
            "longitude": data.longitude,
        }

        hourly: dict[str, Any] = {}
        for hour in data.hourly[:12]:
            t = hour.time.isoformat()
            hourly[t] = {
                "probability": hour.probability_of_precipitation,
                "precipitation_amount": hour.precipitation_amount,
                "symbol_code": hour.symbol_code,
            }

        attrs["hourly"] = hourly
        return attrs


