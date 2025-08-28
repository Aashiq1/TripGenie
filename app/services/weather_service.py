"""Simple weather service using Open-Meteo (no API key required).

Provides daily max temperature and precipitation probability for a date range.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, Optional
import requests


class WeatherService:
    """Fetches simple daily forecasts for scheduling decisions.

    Uses Open-Meteo (https://open-meteo.com/) free API.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def get_daily_forecast(
        self,
        latitude: float,
        longitude: float,
        start_date: dt.date,
        end_date: dt.date,
        timezone: str = "auto",
    ) -> Dict[str, Dict[str, float]]:
        """Return mapping of ISO date -> {max_temp_c, precip_prob}.

        If the API call fails, returns an empty dict.
        """
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone,
                "daily": [
                    "temperature_2m_max",
                    "precipitation_probability_max",
                ],
            }

            resp = requests.get(self.BASE_URL, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            result: Dict[str, Dict[str, float]] = {}
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            temps = daily.get("temperature_2m_max", [])
            precps = daily.get("precipitation_probability_max", [])

            for i, iso_date in enumerate(dates):
                result[iso_date] = {
                    "max_temp_c": float(temps[i]) if i < len(temps) and temps[i] is not None else None,
                    "precip_prob": float(precps[i]) if i < len(precps) and precps[i] is not None else None,
                }

            return result
        except Exception:
            return {}


