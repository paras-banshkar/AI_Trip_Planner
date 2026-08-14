"""
Unit tests for utils/place_info_search.py.

All HTTP/SDK calls are mocked, so these run offline without real
GEOAPIFY_API_KEY / TAVILY_API_KEY.

Run:
    pytest tests/test_place_info_search.py -v
"""
import pytest
from utils.place_info_search import GeoapifyPlaceSearchTool, TavilyPlaceSearchTool


def _make_response(mocker, status_code=200, json_data=None):
    resp = mocker.Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = mocker.Mock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


GEOCODE_OK = {"features": [{"geometry": {"coordinates": [72.8347, 18.9067]}}]}
PLACES_OK = {
    "features": [
        {"properties": {"name": "Gateway of India", "formatted": "Mumbai, India"}},
        {"properties": {"address_line1": "Marine Drive", "formatted": "Mumbai, India"}},
    ]
}
PLACES_EMPTY = {"features": []}


class TestGeocode:
    def test_missing_api_key_raises(self):
        tool = GeoapifyPlaceSearchTool(api_key=None)
        with pytest.raises(ValueError, match="GEOAPIFY_API_KEY"):
            tool._geocode("Mumbai")

    def test_no_features_raises(self, mocker):
        tool = GeoapifyPlaceSearchTool(api_key="fake_key")
        mocker.patch(
            "utils.place_info_search.requests.get",
            return_value=_make_response(mocker, json_data={"features": []}),
        )
        with pytest.raises(ValueError, match="Could not geocode"):
            tool._geocode("Nowhereland")

    def test_returns_lon_lat(self, mocker):
        tool = GeoapifyPlaceSearchTool(api_key="fake_key")
        mocker.patch(
            "utils.place_info_search.requests.get",
            return_value=_make_response(mocker, json_data=GEOCODE_OK),
        )
        lon, lat = tool._geocode("Mumbai")
        assert (lon, lat) == (72.8347, 18.9067)


class TestSearchAttractions:
    def test_formats_results_from_geoapify(self, mocker):
        tool = GeoapifyPlaceSearchTool(api_key="fake_key")
        mocker.patch(
            "utils.place_info_search.requests.get",
            side_effect=[
                _make_response(mocker, json_data=GEOCODE_OK),
                _make_response(mocker, json_data=PLACES_OK),
            ],
        )
        result = tool.search_attractions("Mumbai")
        assert "Gateway of India" in result
        assert "Marine Drive" in result

    def test_empty_results_raises_to_trigger_fallback(self, mocker):
        # No-results must raise (not return ""), so the tool wrapper's
        # except-block falls back to Tavily instead of silently returning
        # nothing to the agent.
        tool = GeoapifyPlaceSearchTool(api_key="fake_key")
        mocker.patch(
            "utils.place_info_search.requests.get",
            side_effect=[
                _make_response(mocker, json_data=GEOCODE_OK),
                _make_response(mocker, json_data=PLACES_EMPTY),
            ],
        )
        with pytest.raises(ValueError, match="No results found"):
            tool.search_attractions("Middle of Nowhere")


class TestTavilyFallback:
    def test_returns_answer_field_when_present(self, mocker):
        mock_tavily_search = mocker.patch("utils.place_info_search.TavilySearch")
        mock_tavily_search.return_value.invoke.return_value = {
            "answer": "Top attractions include the Gateway of India and Marine Drive."
        }
        tool = TavilyPlaceSearchTool()

        result = tool.tavily_search_attractions("Mumbai")

        assert result == "Top attractions include the Gateway of India and Marine Drive."

    def test_returns_raw_result_when_no_answer_field(self, mocker):
        mock_tavily_search = mocker.patch("utils.place_info_search.TavilySearch")
        mock_tavily_search.return_value.invoke.return_value = {"results": ["some", "raw", "data"]}
        tool = TavilyPlaceSearchTool()

        result = tool.tavily_search_restaurants("Mumbai")

        assert result == {"results": ["some", "raw", "data"]}
