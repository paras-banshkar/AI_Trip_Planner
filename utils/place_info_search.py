import requests
from langchain_tavily import TavilySearch

from logger.logging import get_logger

logger = get_logger(__name__)


class GeoapifyPlaceSearchTool:
    """
    Replaces the old Google Places integration with Geoapify's Places API
    (free tier, no billing required). Geoapify doesn't accept a plain place
    name directly, so each search first geocodes the place to (lon, lat),
    then queries the Places API for POIs in a radius around that point.
    """

    GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
    PLACES_URL = "https://api.geoapify.com/v2/places"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _geocode(self, place: str):
        """Resolve a place name to (lon, lat) using Geoapify's Geocoding API."""
        if not self.api_key:
            raise ValueError("GEOAPIFY_API_KEY is not set.")
        params = {"text": place, "limit": 1, "apiKey": self.api_key}
        response = requests.get(self.GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            raise ValueError(f"Could not geocode place: {place}")
        lon, lat = features[0]["geometry"]["coordinates"]
        return lon, lat

    def _search_places(self, place: str, categories: str, radius: int = 20000, limit: int = 15) -> str:
        """Search for places of given Geoapify category/categories around a resolved place."""
        lon, lat = self._geocode(place)
        params = {
            "categories": categories,
            "filter": f"circle:{lon},{lat},{radius}",
            "bias": f"proximity:{lon},{lat}",
            "limit": limit,
            "apiKey": self.api_key,
        }
        response = requests.get(self.PLACES_URL, params=params, timeout=10)
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            # Explicitly raise instead of returning None/empty string so the
            # caller's except-block fallback (Tavily) always gets triggered.
            logger.warning(f"Geoapify returned no results for '{categories}' near '{place}', falling back to Tavily.")
            raise ValueError(f"No results found for categories '{categories}' near {place}")

        results = []
        for feature in features:
            props = feature.get("properties", {})
            name = props.get("name") or props.get("address_line1", "Unnamed place")
            address = props.get("formatted", "")
            results.append(f"- {name} ({address})")
        return "\n".join(results)

    def search_attractions(self, place: str) -> str:
        """Search attractions/tourist sights of a place using Geoapify."""
        return self._search_places(
            place,
            categories="tourism.sights,tourism.attraction,entertainment.museum,entertainment.culture",
        )

    def search_restaurants(self, place: str) -> str:
        """Search restaurants/eateries of a place using Geoapify."""
        return self._search_places(
            place,
            categories="catering.restaurant,catering.cafe,catering.fast_food",
        )

    def search_activities(self, place: str) -> str:
        """Search activities of a place using Geoapify."""
        return self._search_places(
            place,
            categories="entertainment,leisure.park,tourism.attraction",
        )

    def search_transportation(self, place: str) -> str:
        """Search transportation options of a place using Geoapify."""
        return self._search_places(place, categories="public_transport", radius=15000)


class TavilyPlaceSearchTool:
    def __init__(self):
        pass

    def tavily_search_attractions(self, place: str) -> dict:
        """Searches for attractions in the specified place using TavilySearch."""
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"top attractive places in and around {place}"})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result

    def tavily_search_restaurants(self, place: str) -> dict:
        """Searches for available restaurants in the specified place using TavilySearch."""
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"what are the top 10 restaurants and eateries in and around {place}."})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result

    def tavily_search_activity(self, place: str) -> dict:
        """Searches for popular activities in the specified place using TavilySearch."""
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"activities in and around {place}"})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result

    def tavily_search_transportation(self, place: str) -> dict:
        """Searches for available modes of transportation in the specified place using TavilySearch."""
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"What are the different modes of transportations available in {place}"})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result