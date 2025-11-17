"""
Enhanced chatbot with Google Maps MCP integration.
"""

from __future__ import annotations

import json
import re
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from .chatbot import DeepSeekChatbot
from .mcp_client import MCPClient
from .config import MCPSettings, load_mcp_settings


class MapsEnabledChatbot(DeepSeekChatbot):
    """
    Chatbot with Google Maps functionality via MCP.
    Automatically uses Google Maps tools when relevant queries are detected.
    """

    def __init__(
        self,
        *,
        system_prompt: str | None = None,
        mcp_client: Optional[MCPClient] = None,
        mcp_settings: Optional[MCPSettings] = None,
        enable_maps: bool = True,
        **kwargs,
    ) -> None:
        # Initialize base chatbot
        default_system = (
            "You are a helpful AI assistant with access to Google Maps. "
            "When users ask about locations, places, directions, or distances, "
            "you can use Google Maps tools to provide accurate information. "
            "Always use the tools when relevant to answer location-based questions."
        )
        super().__init__(
            system_prompt=system_prompt or default_system,
            **kwargs,
        )
        
        # Initialize MCP client
        self._mcp_client = mcp_client
        if enable_maps and self._mcp_client is None:
            try:
                settings = mcp_settings or load_mcp_settings()
                self._mcp_client = MCPClient(settings=settings)
            except Exception as e:
                print(f"Warning: Could not initialize MCP client: {e}")
                print("Google Maps features will be disabled.")
                self._mcp_client = None
        
        self._enable_maps = enable_maps and self._mcp_client is not None

    def _extract_location_query(self, text: str) -> Optional[dict]:
        """
        Simple heuristic to detect location-related queries.
        Returns a dict with query type and parameters if detected.
        """
        text_lower = text.lower()
        
        # Search nearby places
        if any(keyword in text_lower for keyword in [
            "find", "search", "nearby", "near", "around", "places", "restaurants",
            "hotels", "gas station", "coffee", "shopping", "what's near"
        ]):
            return {"type": "search_nearby", "query": text}
        
        # Directions
        if any(keyword in text_lower for keyword in [
            "directions", "how to get", "route", "navigate", "way to", "drive to"
        ]):
            return {"type": "directions", "query": text}
        
        # Distance
        if any(keyword in text_lower for keyword in [
            "distance", "how far", "miles", "kilometers", "km", "away"
        ]):
            return {"type": "distance", "query": text}
        
        # Geocoding
        if any(keyword in text_lower for keyword in [
            "coordinates", "latitude", "longitude", "lat lng", "where is"
        ]):
            return {"type": "geocode", "query": text}
        
        return None

    def _parse_location_and_keyword(
        self, query: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Very lightweight parser to split a sentence into keyword + location.
        Looks for connectors such as "in", "near", "around", etc.
        """

        cleaned = query.strip()
        if not cleaned:
            return None, None

        lowered = cleaned.lower()
        connectors = [" in ", " near ", " around ", " at ", " within "]
        for connector in connectors:
            idx = lowered.rfind(connector)
            if idx != -1:
                keyword_part = cleaned[:idx].strip(" ,.:;-")
                location_part = cleaned[idx + len(connector) :].strip(" ,.:;-")
                location_part = re.sub(r"[.?!]+$", "", location_part).strip()
                keyword_part = re.sub(r"[.?!]+$", "", keyword_part).strip()
                return self._clean_keyword(keyword_part), location_part or None

        return self._clean_keyword(cleaned), None

    @staticmethod
    def _clean_keyword(text: str) -> Optional[str]:
        """
        Remove filler phrases like "find me" or "show me" from the keyword.
        """

        if not text:
            return None

        lowered = text.lower()
        fillers = [
            "find me",
            "find",
            "show me",
            "search for",
            "search",
            "locate",
            "what is",
            "what's",
            "what are",
            "give me",
            "tell me",
        ]
        for filler in fillers:
            if lowered.startswith(filler):
                trimmed = text[len(filler) :].strip(" ,.:;-")
                return trimmed or None
        return text

    def _geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Use the MCP geocode tool to convert a human-readable location into coordinates.
        """

        if not self._mcp_client or not location:
            return None

        try:
            result = self._mcp_client.geocode(location)
        except Exception:
            return None

        content = result.get("content")
        if not content:
            return None

        text_blob = ""
        if isinstance(content, list) and content:
            text_blob = content[0].get("text", "")
        elif isinstance(content, str):
            text_blob = content

        if not text_blob:
            return None

        try:
            data = json.loads(text_blob)
        except json.JSONDecodeError:
            return None

        results = data.get("results") or []
        if not results:
            return None

        geometry = results[0].get("geometry") or {}
        loc = geometry.get("location") or {}
        lat = loc.get("lat")
        lng = loc.get("lng")
        if lat is None or lng is None:
            return None
        return float(lat), float(lng)

    def _call_maps_tool(self, query_type: str, query: str) -> str:
        """
        Call appropriate Google Maps tool based on query type.
        Returns a formatted string with the results.
        """
        if not self._mcp_client:
            return "Google Maps is not available."

        try:
            if query_type == "search_nearby":
                keyword, location = self._parse_location_and_keyword(query)
                if not location:
                    return (
                        "Please include a city or address so I know where to search."
                    )

                coords = self._geocode_location(location)
                if not coords:
                    return (
                        "I couldn't understand the location you provided. "
                        "Please rewrite it or provide a specific address/city."
                    )

                lat, lng = coords
                args = {"location": f"{lat},{lng}", "radius": 5000}
                if keyword:
                    args["keyword"] = keyword

                result = self._mcp_client.search_nearby(**args)
                return self._format_search_results(result)
            
            elif query_type == "directions":
                # Extract origin and destination - simplified
                return "Please provide origin and destination addresses for directions."
            
            elif query_type == "distance":
                return "Please provide two locations to calculate distance."
            
            elif query_type == "geocode":
                # Extract address from query
                return "Please provide an address to get coordinates."
            
        except Exception as e:
            return f"Error calling Google Maps: {str(e)}"
        
        return "Could not process location query."

    def _format_search_results(self, result: dict) -> str:
        """Format search results for display."""
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                try:
                    data = json.loads(text_content)
                    places = data.get("results", [])
                    if not places:
                        return "No places found."
                    
                    formatted = f"Found {len(places)} places:\n\n"
                    for i, place in enumerate(places[:10], 1):  # Limit to 10
                        name = place.get("name", "Unknown")
                        rating = place.get("rating", "N/A")
                        address = place.get("vicinity", place.get("formatted_address", "N/A"))
                        formatted += f"{i}. {name}\n"
                        formatted += f"   Rating: {rating}/5\n"
                        formatted += f"   Address: {address}\n\n"
                    return formatted
                except json.JSONDecodeError:
                    return text_content
            elif isinstance(content, str):
                return content
        
        return json.dumps(result, indent=2)

    def send_text(
        self,
        text: str,
        *,
        model: str = "deepseek-chat",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_maps: Optional[bool] = None,
    ) -> Tuple[str, dict]:
        """
        Send a text message, optionally using Google Maps tools.
        
        Args:
            text: User message
            use_maps: If True, automatically use maps tools when relevant.
                     If None, uses self._enable_maps setting.
        """
        use_maps = use_maps if use_maps is not None else self._enable_maps
        
        # Check if this is a location-related query
        if use_maps:
            location_query = self._extract_location_query(text)
            if location_query:
                maps_result = self._call_maps_tool(
                    location_query["type"],
                    location_query["query"]
                )
                # Include maps result in the prompt
                enhanced_text = f"{text}\n\n[Google Maps Result]:\n{maps_result}"
                return super().send_text(
                    enhanced_text,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        
        return super().send_text(
            text,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Expose MCP client methods for direct access
    @property
    def maps(self) -> Optional[MCPClient]:
        """Access the MCP client directly for advanced usage."""
        return self._mcp_client

    def search_nearby_places(
        self,
        location: str,
        radius: Optional[int] = None,
        keyword: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Search for nearby places."""
        if not self._mcp_client:
            raise RuntimeError("MCP client not available")
        return self._mcp_client.search_nearby(
            location=location,
            radius=radius,
            keyword=keyword,
            **kwargs,
        )

    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
    ) -> dict:
        """Get directions between two locations."""
        if not self._mcp_client:
            raise RuntimeError("MCP client not available")
        return self._mcp_client.directions(
            origin=origin,
            destination=destination,
            mode=mode,
        )

    def get_distance(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving",
    ) -> dict:
        """Calculate distances between locations."""
        if not self._mcp_client:
            raise RuntimeError("MCP client not available")
        return self._mcp_client.distance_matrix(
            origins=origins,
            destinations=destinations,
            mode=mode,
        )

    def geocode_address(self, address: str) -> dict:
        """Convert address to coordinates."""
        if not self._mcp_client:
            raise RuntimeError("MCP client not available")
        return self._mcp_client.geocode(address)

