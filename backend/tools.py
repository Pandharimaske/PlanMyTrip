import httpx
import os
from datetime import datetime

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

INTEREST_TYPE_MAP = {
    "food": "restaurant",
    "culture": "museum",
    "adventure": "park",
    "shopping": "shopping_mall",
    "history": "tourist_attraction",
    "nature": "park",
    "nightlife": "bar",
    "religious": "place_of_worship",
    "art": "art_gallery",
    "beaches": "tourist_attraction",
    "temples": "place_of_worship",
    "trekking": "park",
}

async def get_weather(destination: str) -> dict:
    """
    Get weather for destination using free Open-Meteo API (no API key required).
    First geocodes the destination, then fetches current weather.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Geocode using Open-Meteo's free geocoding API
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={destination}&count=1&language=en&format=json"
            geo_res = await client.get(geo_url)
            geo_data = geo_res.json()

            if not geo_data.get("results"):
                return {"description": "clear sky", "temp": 28, "humidity": 60, "feels_like": 30}

            result = geo_data["results"][0]
            lat, lon = result["latitude"], result["longitude"]

            # Get current weather using Open-Meteo's free weather API
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,apparent_temperature"
            )
            weather_res = await client.get(weather_url)
            w = weather_res.json()

            if "current" in w:
                current = w["current"]
                # Map WMO weather codes to descriptions
                weather_desc = _get_weather_description(current.get("weather_code", 0))
                return {
                    "description": weather_desc,
                    "temp": round(current.get("temperature_2m", 28), 1),
                    "humidity": current.get("relative_humidity_2m", 60),
                    "feels_like": round(current.get("apparent_temperature", 28), 1),
                }
            else:
                return {"description": "clear sky", "temp": 28, "humidity": 60, "feels_like": 30}
    except Exception as e:
        return {"description": "clear sky", "temp": 28, "humidity": 60, "feels_like": 30}


def _get_weather_description(code: int) -> str:
    """
    Convert WMO weather code to description.
    https://www.weatherapi.com/docs/weather_codes.asp
    """
    if code == 0:
        return "clear sky"
    elif code == 1 or code == 2:
        return "partly cloudy"
    elif code == 3:
        return "overcast"
    elif code == 45 or code == 48:
        return "foggy"
    elif code == 51 or code == 53 or code == 55:
        return "light rain"
    elif code == 61 or code == 63 or code == 65:
        return "rain"
    elif code == 71 or code == 73 or code == 75:
        return "snow"
    elif code == 77:
        return "snow grains"
    elif code == 80 or code == 81 or code == 82:
        return "rain showers"
    elif code == 85 or code == 86:
        return "snow showers"
    elif code == 95 or code == 96 or code == 99:
        return "thunderstorm"
    else:
        return "clear sky"


async def get_hotels(destination: str, budget: float, days: int) -> list:
    """
    Generate hotel options based on destination and budget.
    Uses realistic pricing tiers: budget, mid-range, luxury
    """
    hotels = [
        {
            "name": f"Budget Stay - {destination}",
            "type": "Budget Hotel",
            "price_per_night": max(800, int(budget / days * 0.15)),
            "rating": 3.8,
            "amenities": ["WiFi", "AC", "Breakfast"],
            "description": "Clean, comfortable rooms perfect for budget travelers",
            "location": f"City Center, {destination}"
        },
        {
            "name": f"Comfort Inn - {destination}",
            "type": "3-Star Hotel",
            "price_per_night": max(2000, int(budget / days * 0.30)),
            "rating": 4.2,
            "amenities": ["WiFi", "AC", "Restaurant", "Gym", "Breakfast Included"],
            "description": "Good quality mid-range hotel with excellent service",
            "location": f"Main Area, {destination}"
        },
        {
            "name": f"Premium Resort - {destination}",
            "type": "4-Star Hotel",
            "price_per_night": max(4000, int(budget / days * 0.50)),
            "rating": 4.6,
            "amenities": ["WiFi", "AC", "Restaurant", "Gym", "Spa", "Swimming Pool", "Room Service"],
            "description": "Luxury accommodation with premium amenities",
            "location": f"Prime Location, {destination}"
        },
        {
            "name": f"Heritage Homestay - {destination}",
            "type": "Homestay",
            "price_per_night": max(1200, int(budget / days * 0.20)),
            "rating": 4.4,
            "amenities": ["WiFi", "AC", "Home Cooked Meals", "Local Experience"],
            "description": "Authentic local experience staying with a family",
            "location": f"Local Area, {destination}"
        }
    ]
    return hotels


async def get_places(destination: str, interests: list, days: int) -> list:
    places = []
    seen_names = set()

    async with httpx.AsyncClient(timeout=15) as client:
        queries = []
        for interest in interests[:4]:
            ptype = INTEREST_TYPE_MAP.get(interest.lower(), "tourist_attraction")
            queries.append(f"{ptype} in {destination}")
        queries.append(f"top tourist attractions in {destination}")

        for query in queries:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {"query": query, "key": GOOGLE_MAPS_KEY}
            try:
                res = await client.get(url, params=params)
                data = res.json()
                for p in data.get("results", [])[:6]:
                    name = p["name"]
                    if name not in seen_names:
                        seen_names.add(name)
                        places.append({
                            "name": name,
                            "address": p.get("formatted_address", ""),
                            "rating": p.get("rating", 4.0),
                            "user_ratings_total": p.get("user_ratings_total", 0),
                            "types": p.get("types", []),
                            "lat": p["geometry"]["location"]["lat"],
                            "lng": p["geometry"]["location"]["lng"],
                            "place_id": p.get("place_id", ""),
                            "photo_ref": (
                                p["photos"][0]["photo_reference"]
                                if p.get("photos") else None
                            ),
                        })
            except Exception:
                continue

    places.sort(key=lambda x: x["rating"], reverse=True)
    return places[: days * 6]
