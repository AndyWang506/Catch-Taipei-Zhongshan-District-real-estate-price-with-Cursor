"""
Example usage of the Maps-enabled chatbot.
"""

from __future__ import annotations

from .chatbot_with_maps import MapsEnabledChatbot


def main() -> None:
    """Example of using Google Maps with the chatbot."""
    
    # Initialize the maps-enabled chatbot
    chatbot = MapsEnabledChatbot()
    
    print("Maps-Enabled Chatbot Example")
    print("=" * 50)
    print()
    
    # Example 1: Search for nearby places
    print("Example 1: Searching for nearby coffee shops...")
    try:
        result = chatbot.search_nearby_places(
            location="San Francisco, CA",
            keyword="coffee",
            radius=2000,
        )
        print("Results:", result)
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Example 2: Get directions
    print("Example 2: Getting directions...")
    try:
        directions = chatbot.get_directions(
            origin="San Francisco, CA",
            destination="Los Angeles, CA",
            mode="driving",
        )
        print("Directions:", directions)
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Example 3: Chat with automatic maps integration
    print("Example 3: Chat with automatic maps detection...")
    response, usage = chatbot.send_text(
        "Find coffee shops near San Francisco",
        use_maps=True,
    )
    print("Response:", response)
    print()
    
    # Example 4: Geocode an address
    print("Example 4: Geocoding an address...")
    try:
        geocode_result = chatbot.geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")
        print("Geocode result:", geocode_result)
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()


if __name__ == "__main__":
    main()

