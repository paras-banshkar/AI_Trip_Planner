"""
Unit tests for utils/weather_info.py.

Includes a regression test for the fixed bug where `units=metric` was
missing from the request params, causing OpenWeatherMap to return Kelvin
while the tool labeled it as °C.

Run:
    pytest tests/test_weather_info.py -v
"""
from utils.weather_info import WeatherForecastTool


def _make_response(mocker, status_code=200, json_data=None):
    resp = mocker.Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = str(json_data)
    return resp


class TestGetCurrentWeather:
    def test_requests_metric_units(self, mocker):
        """Regression test: params must always include units=metric."""
        tool = WeatherForecastTool(api_key="fake_key")
        mock_get = mocker.patch(
            "utils.weather_info.requests.get",
            return_value=_make_response(
                mocker,
                json_data={"main": {"temp": 28.5}, "weather": [{"description": "clear sky"}]},
            ),
        )

        tool.get_current_weather("Goa")

        _, kwargs = mock_get.call_args
        assert kwargs["params"]["units"] == "metric"

    def test_returns_parsed_json_on_success(self, mocker):
        tool = WeatherForecastTool(api_key="fake_key")
        mocker.patch(
            "utils.weather_info.requests.get",
            return_value=_make_response(
                mocker,
                json_data={"main": {"temp": 28.5}, "weather": [{"description": "clear sky"}]},
            ),
        )

        result = tool.get_current_weather("Goa")

        assert result["main"]["temp"] == 28.5

    def test_returns_empty_dict_on_non_200(self, mocker):
        tool = WeatherForecastTool(api_key="fake_key")
        mocker.patch(
            "utils.weather_info.requests.get",
            return_value=_make_response(mocker, status_code=404, json_data={}),
        )

        result = tool.get_current_weather("Nowhereland")

        assert result == {}


class TestGetForecastWeather:
    def test_requests_metric_units(self, mocker):
        tool = WeatherForecastTool(api_key="fake_key")
        mock_get = mocker.patch(
            "utils.weather_info.requests.get",
            return_value=_make_response(mocker, json_data={"list": []}),
        )

        tool.get_forecast_weather("Manali")

        _, kwargs = mock_get.call_args
        assert kwargs["params"]["units"] == "metric"
