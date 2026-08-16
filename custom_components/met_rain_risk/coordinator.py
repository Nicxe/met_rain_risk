"""Coordinator for MET Rain Risk."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import MET_NO_LOCATIONFORECAST_COMPLETE_URL, PROJECT_URL, VERSION


@dataclass(frozen=True, slots=True)
class HourForecast:
    """Forecast data for a specific hour."""

    time: datetime
    probability_of_precipitation: float
    precipitation_amount: float | None
    symbol_code: str | None


@dataclass(frozen=True, slots=True)
class MetRainRiskData:
    """Parsed data exposed by the coordinator."""

    latitude: float
    longitude: float
    api_updated_at: datetime | None
    hourly: list[HourForecast]
    max_probability_12h: float | None


def _get(obj: dict[str, Any] | None, *path: str) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


class MetRainRiskCoordinator(DataUpdateCoordinator[MetRainRiskData]):
    """Fetch data from met.no and expose rain risk for next 12 hours."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        latitude: float,
        longitude: float,
        contact: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name="met_rain_risk",
            update_interval=update_interval,
        )
        self._latitude = float(latitude)
        self._longitude = float(longitude)
        self._contact = str(contact)

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    def set_config(
        self,
        *,
        latitude: float,
        longitude: float,
        contact: str,
        update_interval: timedelta,
    ) -> None:
        self._latitude = float(latitude)
        self._longitude = float(longitude)
        self._contact = str(contact)
        self.update_interval = update_interval

    def _build_url(self) -> str:
        return f"{MET_NO_LOCATIONFORECAST_COMPLETE_URL}?lat={self._latitude}&lon={self._longitude}"

    def _user_agent(self) -> str:
        # met.no requires a descriptive User-Agent including contact details.
        # Prefer the recommended pattern: app/version (+url; contact)
        # Keep contact last so it stays readable in logs if needed.
        return f"met_rain_risk/{VERSION} (+{PROJECT_URL}; {self._contact})"

    async def _async_update_data(self) -> MetRainRiskData:
        session = aiohttp_client.async_get_clientsession(self.hass)
        url = self._build_url()
        headers = {
            "User-Agent": self._user_agent(),
            "From": self._contact,
            "Accept": "application/json",
        }
        # Coordinates and contact details are private configuration values.
        # Keep diagnostics useful without copying request data into logs.
        self.logger.debug("Requesting met.no forecast")

        try:
            async with async_timeout.timeout(10):
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        self.logger.error(
                            "met.no request failed (HTTP %s)", resp.status
                        )
                        raise UpdateFailed(f"met.no returned HTTP {resp.status}")
                    payload: dict[str, Any] = await resp.json()
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed("Error fetching met.no data") from err

        now = dt_util.utcnow()
        end = now + timedelta(hours=12)

        api_updated_at: datetime | None = None
        updated_at_raw = _get(payload, "properties", "meta", "updated_at")
        if isinstance(updated_at_raw, str):
            api_updated_at = dt_util.parse_datetime(updated_at_raw)

        timeseries = _get(payload, "properties", "timeseries")
        if not isinstance(timeseries, list):
            raise UpdateFailed("Unexpected met.no payload shape: missing properties.timeseries")

        hourly: list[HourForecast] = []

        for item in timeseries:
            if not isinstance(item, dict):
                continue
            t_raw = item.get("time")
            if not isinstance(t_raw, str):
                continue
            t = dt_util.parse_datetime(t_raw)
            if t is None:
                continue

            # only future points in next 12 hours
            if t <= now:
                continue
            if t > end:
                break

            prob = _get(item, "data", "next_1_hours", "details", "probability_of_precipitation")
            try:
                prob_f = float(prob) if prob is not None else 0.0
            except (TypeError, ValueError):
                prob_f = 0.0

            precip_amount = _get(item, "data", "next_1_hours", "details", "precipitation_amount")
            try:
                precip_f = float(precip_amount) if precip_amount is not None else None
            except (TypeError, ValueError):
                precip_f = None

            symbol = _get(item, "data", "next_1_hours", "summary", "symbol_code")
            symbol_s = str(symbol) if isinstance(symbol, str) else None

            hourly.append(
                HourForecast(
                    time=t,
                    probability_of_precipitation=max(0.0, min(100.0, prob_f)),
                    precipitation_amount=precip_f,
                    symbol_code=symbol_s,
                )
            )
            if len(hourly) >= 12:
                break

        max_prob: float | None = None
        if hourly:
            max_prob = max(h.probability_of_precipitation for h in hourly)

        return MetRainRiskData(
            latitude=self._latitude,
            longitude=self._longitude,
            api_updated_at=api_updated_at,
            hourly=hourly,
            max_probability_12h=max_prob,
        )


