"""
MCP (Model Context Protocol) client for Google Maps integration.
Communicates with the mcp-google-map HTTP server.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional, Mapping, Tuple

import requests

from .config import MCPSettings, load_mcp_settings


class MCPClient:
    """
    Client for interacting with the Google Maps MCP server.
    """

    def __init__(
        self,
        settings: Optional[MCPSettings] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._settings = settings or load_mcp_settings()
        self._session = session or requests.Session()
        self._session_id = str(uuid.uuid4())

    def _headers(self) -> Dict[str, str]:
        """Get headers for MCP requests."""
        headers = {
            "Content-Type": "application/json",
        }
        if self._settings.api_key:
            headers["X-Google-Maps-API-Key"] = self._settings.api_key
        return headers

    def _make_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the MCP server.
        
        Args:
            method: The MCP method name (e.g., 'tools/call')
            params: Parameters for the method
            
        Returns:
            The JSON response from the server
        """
        url = f"{self._settings.url.rstrip('/')}/mcp"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
        }
        if params:
            payload["params"] = params

        response = self._session.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise RuntimeError(f"MCP Error: {result['error']}")
        
        return result.get("result", {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from the MCP server."""
        result = self._make_request("tools/list")
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            name: The name of the tool to call
            arguments: The arguments for the tool
            
        Returns:
            The tool's response
        """
        result = self._make_request(
            "tools/call",
            params={"name": name, "arguments": arguments},
        )
        return result

    # Convenience methods for Google Maps tools

    def search_nearby(
        self,
        location: str,
        radius: Optional[int] = None,
        keyword: Optional[str] = None,
        min_rating: Optional[float] = None,
        open_now: Optional[bool] = None,
        type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for nearby places.
        
        Args:
            location: Location (address or lat,lng)
            radius: Search radius in meters (default: 5000)
            keyword: Search keyword
            min_rating: Minimum rating (0-5)
            open_now: Only show places open now
            type: Place type filter
            
        Returns:
            Search results
        """
        args: Dict[str, Any] = {"location": location}
        if radius is not None:
            args["radius"] = radius
        if keyword:
            args["keyword"] = keyword
        if min_rating is not None:
            args["minRating"] = min_rating
        if open_now is not None:
            args["openNow"] = open_now
        if type:
            args["type"] = type

        return self.call_tool("search_nearby", args)

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a place.
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Place details
        """
        return self.call_tool("get_place_details", {"placeId": place_id})

    def geocode(self, address: str) -> Dict[str, Any]:
        """
        Convert an address to coordinates.
        
        Args:
            address: Address to geocode
            
        Returns:
            Geocoding results with coordinates
        """
        return self.call_tool("maps_geocode", {"address": address})

    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Convert coordinates to an address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Reverse geocoding results with address
        """
        return self.call_tool("maps_reverse_geocode", {"lat": lat, "lng": lng})

    def distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving",
    ) -> Dict[str, Any]:
        """
        Calculate distances and travel times.
        
        Args:
            origins: List of origin locations
            destinations: List of destination locations
            mode: Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            Distance matrix results
        """
        return self.call_tool(
            "maps_distance_matrix",
            {
                "origins": origins,
                "destinations": destinations,
                "mode": mode,
            },
        )

    def directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
    ) -> Dict[str, Any]:
        """
        Get turn-by-turn directions.
        
        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            Directions results
        """
        return self.call_tool(
            "maps_directions",
            {
                "origin": origin,
                "destination": destination,
                "mode": mode,
            },
        )

    def elevation(self, locations: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Get elevation data for locations.
        
        Args:
            locations: List of (lat, lng) tuples
            
        Returns:
            Elevation data
        """
        # Convert tuples to list of dicts
        location_dicts = [{"lat": lat, "lng": lng} for lat, lng in locations]
        return self.call_tool("maps_elevation", {"locations": location_dicts})

