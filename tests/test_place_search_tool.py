"""
Unit tests for tools/place_search_tool.py — the Geoapify-then-Tavily
fallback wiring, invoked through .invoke() (the way LangGraph's ToolNode
actually calls these), not by calling the underlying search classes
directly.

GeoapifyPlaceSearchTool / TavilyPlaceSearchTool are mocked at the instance
level so no real API keys or network calls are needed.

Run:
    pytest tests/test_place_search_tool.py -v
"""
import pytest
from tools.place_search_tool import PlaceSearchTool


@pytest.fixture
def place_tool(mocker):
    # Avoid __init__ needing real GEOAPIFY_API_KEY / building real HTTP clients.
    mocker.patch("tools.place_search_tool.GeoapifyPlaceSearchTool")
    mocker.patch("tools.place_search_tool.TavilyPlaceSearchTool")
    return PlaceSearchTool()


@pytest.fixture
def tools_by_name(place_tool):
    return {t.name: t for t in place_tool.place_search_tool_list}


class TestSearchAttractions:
    def test_uses_geoapify_result_when_it_succeeds(self, place_tool, tools_by_name):
        place_tool.geoapify_search.search_attractions.return_value = "- Gateway of India"

        result = tools_by_name["search_attractions"].invoke({"place": "Mumbai"})

        assert "Gateway of India" in result
        assert "Geoapify" in result
        place_tool.tavily_search.tavily_search_attractions.assert_not_called()

    def test_falls_back_to_tavily_when_geoapify_fails(self, place_tool, tools_by_name):
        place_tool.geoapify_search.search_attractions.side_effect = ValueError("No results found")
        place_tool.tavily_search.tavily_search_attractions.return_value = "Marine Drive, Gateway of India"

        result = tools_by_name["search_attractions"].invoke({"place": "Mumbai"})

        assert "Marine Drive" in result
        place_tool.tavily_search.tavily_search_attractions.assert_called_once_with("Mumbai")


class TestSearchRestaurants:
    def test_falls_back_to_tavily_when_geoapify_fails(self, place_tool, tools_by_name):
        place_tool.geoapify_search.search_restaurants.side_effect = Exception("Geoapify down")
        place_tool.tavily_search.tavily_search_restaurants.return_value = "Some good restaurants"

        result = tools_by_name["search_restaurants"].invoke({"place": "Goa"})

        assert "Some good restaurants" in result


class TestSearchActivities:
    def test_uses_geoapify_result_when_it_succeeds(self, place_tool, tools_by_name):
        place_tool.geoapify_search.search_activities.return_value = "- Scuba diving"

        result = tools_by_name["search_activities"].invoke({"place": "Goa"})

        assert "Scuba diving" in result


class TestSearchTransportation:
    def test_falls_back_to_tavily_when_geoapify_fails(self, place_tool, tools_by_name):
        place_tool.geoapify_search.search_transportation.side_effect = ValueError("No results found")
        place_tool.tavily_search.tavily_search_transportation.return_value = "Local buses and taxis"

        result = tools_by_name["search_transportation"].invoke({"place": "Manali"})

        assert "Local buses and taxis" in result
