import requests

from logger.logging import get_logger

logger = get_logger(__name__)


class WeatherForecastTool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, place: str):
        """Get current weather of a place"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": place,
                "appid": self.api_key,
                # BUGFIX: this was previously missing, which meant OpenWeatherMap
                # returned temperature in Kelvin while the caller labeled it °C.
                "units": "metric",
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                logger.warning(
                    f"Weather lookup failed for '{place}': "
                    f"status={response.status_code}, body={response.text}"
                )
                return {}
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API request failed for '{place}': {e}")
            raise

    def get_forecast_weather(self, place: str):
        """Get weather forecast of a place"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": place,
                "appid": self.api_key,
                "cnt": 10,
                "units": "metric",
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                logger.warning(
                    f"Forecast lookup failed for '{place}': "
                    f"status={response.status_code}, body={response.text}"
                )
                return {}
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Forecast API request failed for '{place}': {e}")
            raise
