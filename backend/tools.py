import httpx
import os

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
WEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

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
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo_url = (
                f"http://api.openweathermap.org/geo/1.0/direct"
                f"?q={destination}&limit=1&appid={WEATHER_KEY}"
            )
            geo_res = await client.get(geo_url)
            geo_data = geo_res.json()

            if not geo_data:
                return {"description": "clear sky", "temp": 28, "humidity": 60, "feels_like": 30}

            lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

            weather_url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
            )
            weather_res = await client.get(weather_url)
            w = weather_res.json()

            return {
                "description": w["weather"][0]["description"],
                "temp": round(w["main"]["temp"], 1),
                "humidity": w["main"]["humidity"],
                "feels_like": round(w["main"]["feels_like"], 1),
                "icon": w["weather"][0]["icon"],
            }
    except Exception:
        return {"description": "clear sky", "temp": 28, "humidity": 60, "feels_like": 30}


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
