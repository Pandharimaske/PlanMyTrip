"""
Preference-weighted scoring model for attractions.

Scores places based on:
1. Category relevance (how well place matches user interests)
2. Popularity (rating + review count)
3. Distance from cluster center (prefer closer places)
4. Opening hours suitability (prefer open during travel time)
"""

import math
from typing import List, Dict
from datetime import datetime

# Weights for different scoring components
WEIGHTS = {
    "relevance": 0.35,
    "popularity": 0.30,
    "distance": 0.20,
    "opening_hours": 0.15,
}

# Mapping of interests to Google Places types for relevance
INTEREST_TYPES = {
    "food": ["restaurant", "cafe", "bakery", "fast_food", "bar", "pub"],
    "culture": ["museum", "art_gallery", "cultural_landmark", "library"],
    "adventure": ["park", "hiking_area", "rock_climbing", "zip_line"],
    "shopping": ["shopping_mall", "department_store", "market", "clothing_store"],
    "history": ["tourist_attraction", "historical_landmark", "monument", "ruins"],
    "nature": ["park", "garden", "natural_landmark", "nature_preserve"],
    "nightlife": ["bar", "nightclub", "lounge", "pub"],
    "religious": ["place_of_worship", "temple", "mosque", "church", "shrine"],
    "art": ["art_gallery", "museum", "cultural_landmark"],
    "beaches": ["beach", "water_park"],
    "temples": ["temple", "place_of_worship", "shrine"],
    "trekking": ["hiking_area", "mountain_pass", "scenic_viewpoint"],
}

def calculate_relevance_score(place: Dict, interests: List[str]) -> float:
    """
    Calculate how relevant a place is to user interests (0-1).
    
    Args:
        place: Place dict with 'types' field from Google Places
        interests: List of user interests
    
    Returns:
        Relevance score 0-1
    """
    if not interests:
        return 0.5  # Neutral score if no interests specified
    
    place_types = set(place.get("types", []))
    interest_keyword_types = set()
    
    for interest in interests:
        interest_keyword_types.update(INTEREST_TYPES.get(interest.lower(), []))
    
    if not interest_keyword_types or not place_types:
        return 0.5
    
    # Calculate intersection ratio
    matches = len(place_types.intersection(interest_keyword_types))
    total_possible = len(interest_keyword_types)
    
    return min(1.0, (matches / total_possible) * 1.5) if total_possible > 0 else 0.5


def calculate_popularity_score(place: Dict) -> float:
    """
    Calculate popularity score based on rating and review count (0-1).
    
    Args:
        place: Place dict with 'rating' and 'user_ratings_total' fields
    
    Returns:
        Popularity score 0-1
    """
    rating = place.get("rating", 3.0)  # Default 3.0 if no rating
    num_reviews = place.get("user_ratings_total", 0)
    
    # Normalize rating to 0-1 (scale 5 to 1)
    rating_score = rating / 5.0
    
    # Normalize review count to 0-1 (log scale, assume 1000+ reviews is max)
    review_score = min(1.0, math.log(num_reviews + 1) / math.log(1001))
    
    # Weighted combination: rating more important than volume
    return (rating_score * 0.6) + (review_score * 0.4)


def calculate_distance_score(place: Dict, cluster_center: tuple) -> float:
    """
    Calculate distance score - penalize far places, prefer closer ones (0-1).
    
    Args:
        place: Place dict with 'lat' and 'lng'
        cluster_center: (lat, lng) of cluster center
    
    Returns:
        Distance score 0-1 (higher = closer)
    """
    lat1, lng1 = cluster_center
    lat2, lng2 = place.get("lat", 0), place.get("lng", 0)
    
    # Haversine distance (km)
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlng/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c
    
    # Exponential decay: max score at 0km, drops with distance
    # At 5km distance, score = 0.37, at 10km = 0.135
    distance_score = math.exp(-distance_km / 5.0)
    
    return distance_score


def calculate_opening_hours_score(place: Dict, desired_time: str = "afternoon") -> float:
    """
    Calculate opening hours suitability (0-1).
    Not fully implemented in Google Places API response, returns neutral score.
    
    Args:
        place: Place dict (would need opening_hours field)
        desired_time: "morning", "afternoon", or "evening"
    
    Returns:
        Opening hours score 0-1
    """
    # Places API doesn't always include detailed opening hours
    # For now, return neutral score. Can be enhanced with business hours API
    if place.get("business_status") == "CLOSED_PERMANENTLY":
        return 0.0
    return 0.8  # Assume most places are open


def score_places(
    places: List[Dict],
    interests: List[str],
    cluster_center: tuple = None,
) -> List[Dict]:
    """
    Score and rank places based on all criteria.
    
    Args:
        places: List of place dicts from Google Places API
        interests: User interests
        cluster_center: (lat, lng) center of cluster, if None uses first place
    
    Returns:
        Sorted list of places with 'score' and 'component_scores' fields
    """
    if not places:
        return []
    
    if cluster_center is None and places:
        cluster_center = (places[0]["lat"], places[0]["lng"])
    
    scored_places = []
    
    for place in places:
        relevance = calculate_relevance_score(place, interests)
        popularity = calculate_popularity_score(place)
        distance = calculate_distance_score(place, cluster_center)
        opening = calculate_opening_hours_score(place)
        
        total_score = (
            relevance * WEIGHTS["relevance"] +
            popularity * WEIGHTS["popularity"] +
            distance * WEIGHTS["distance"] +
            opening * WEIGHTS["opening_hours"]
        )
        
        scored_places.append({
            **place,
            "score": round(total_score, 3),
            "component_scores": {
                "relevance": round(relevance, 3),
                "popularity": round(popularity, 3),
                "distance": round(distance, 3),
                "opening_hours": round(opening, 3),
            }
        })
    
    # Sort by total score descending
    scored_places.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_places


def adaptive_preference_weighting(user_history: List[Dict]) -> Dict[str, float]:
    """
    Adjust weights based on user's past trip preferences.
    
    Args:
        user_history: List of past trips with interest distribution
    
    Returns:
        Adjusted weights dict
    """
    # Default weights if no history
    if not user_history:
        return WEIGHTS.copy()
    
    adjusted = WEIGHTS.copy()
    
    # Analyze past preference patterns
    # If user frequently picks high-rating places, increase popularity weight
    avg_ratings = sum(
        trip.get("avg_rating", 4.0)
        for trip in user_history
    ) / len(user_history)
    
    if avg_ratings > 4.5:
        adjusted["popularity"] = 0.35
        adjusted["relevance"] = 0.30
    
    # If user travels far (implications for distance), decrease distance weight
    avg_distance = sum(
        trip.get("avg_travel_distance", 0)
        for trip in user_history
    ) / len(user_history)
    
    if avg_distance > 10:
        adjusted["distance"] = 0.15
        adjusted["relevance"] = 0.40
    
    return adjusted
