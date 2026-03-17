"""
User preference tracking and learning system.

Features:
1. Track user preferences from past trips
2. Learn preferred categories, budget habits, travel patterns
3. Adaptive weighting for future recommendations
4. User profile building (interests, budget preference, travel pace)
"""

from typing import List, Dict, Optional
from pathlib import Path
import json
import pickle
from datetime import datetime

USER_PROFILES_DIR = Path("./user_profiles")
USER_PROFILES_DIR.mkdir(exist_ok=True)


class UserProfile:
    """Stores and manages user preferences and history."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.profile_path = USER_PROFILES_DIR / f"{user_id}_profile.json"
        self.preferences = self._load_profile()
        
    def _load_profile(self) -> Dict:
        """Load user profile from disk or create new one."""
        if self.profile_path.exists():
            with open(self.profile_path, "r") as f:
                return json.load(f)
        
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "trips_count": 0,
            "interest_preferences": {},
            "budget_preferences": {
                "average_budget": 0,
                "budget_per_day_avg": 0,
                "spent_percent_avg": 0,  # How much of budget gets spent
            },
            "travel_patterns": {
                "preferred_duration": 3,  # days
                "travel_type_distribution": {},
                "favorite_destinations": [],
                "travel_pace": "moderate",  # slow, moderate, fast
            },
            "cost_preferences": {
                "accommodation_percent": 0,
                "food_percent": 0,
                "activities_percent": 0,
                "transport_percent": 0,
            },
            "visit_history": [],
        }
    
    def save_profile(self):
        """Save user profile to disk."""
        with open(self.profile_path, "w") as f:
            json.dump(self.preferences, f, indent=2)
    
    def add_trip(self, trip_data: Dict):
        """
        Record a completed trip and update preferences.
        
        Args:
            trip_data: Itinerary with all trip details
        """
        # Extract trip metadata
        destination = trip_data.get("destination", "Unknown")
        total_days = trip_data.get("total_days", 0)
        total_budget = trip_data.get("total_budget", 0)
        total_cost = trip_data.get("total_estimated_cost", 0)
        weather = trip_data.get("weather", {})
        places = trip_data.get("places_data", [])
        
        # Update interest preferences based on visited places
        self._update_interest_preferences(places, total_days)
        
        # Update budget preferences
        old_avg = self.preferences["budget_preferences"]["average_budget"]
        old_count = self.preferences["trips_count"]
        
        new_avg = (old_avg * old_count + total_budget) / (old_count + 1)
        self.preferences["budget_preferences"]["average_budget"] = round(new_avg)
        
        per_day_avg = (total_budget / total_days) if total_days > 0 else total_budget
        self.preferences["budget_preferences"]["budget_per_day_avg"] = round(per_day_avg)
        
        if total_budget > 0:
            spent_percent = (total_cost / total_budget) * 100
            self.preferences["budget_preferences"]["spent_percent_avg"] = round(spent_percent, 1)
        
        # Update cost breakdown preferences
        breakdown = trip_data.get("budget_breakdown", {})
        total_cost = sum(breakdown.values()) if breakdown else total_cost
        
        if total_cost > 0:
            self.preferences["cost_preferences"]["accommodation_percent"] = \
                round((breakdown.get("accommodation", 0) / total_cost) * 100)
            self.preferences["cost_preferences"]["food_percent"] = \
                round((breakdown.get("food", 0) / total_cost) * 100)
            self.preferences["cost_preferences"]["activities_percent"] = \
                round((breakdown.get("activities", 0) / total_cost) * 100)
            self.preferences["cost_preferences"]["transport_percent"] = \
                round((breakdown.get("transport", 0) / total_cost) * 100)
        
        # Update travel patterns
        if destination not in self.preferences["travel_patterns"]["favorite_destinations"]:
            self.preferences["travel_patterns"]["favorite_destinations"].append(destination)
        
        # Infer travel pace from activities per day
        days = trip_data.get("days", [])
        activities_per_day = sum(
            len([slot for slot in ["morning", "afternoon", "evening"] 
                 if d.get(slot, {}).get("place")])
            for d in days
        ) / len(days) if days else 0
        
        if activities_per_day > 3.5:
            self.preferences["travel_patterns"]["travel_pace"] = "fast"
        elif activities_per_day < 1.5:
            self.preferences["travel_patterns"]["travel_pace"] = "slow"
        else:
            self.preferences["travel_patterns"]["travel_pace"] = "moderate"
        
        # Record visit
        self.preferences["visit_history"].append({
            "destination": destination,
            "date": datetime.now().isoformat(),
            "days": total_days,
            "budget": total_budget,
            "cost": total_cost,
            "pace": self.preferences["travel_patterns"]["travel_pace"],
        })
        
        self.preferences["trips_count"] += 1
        self.save_profile()
    
    def _update_interest_preferences(self, places: List[Dict], days: int):
        """
        Update interest distribution from visited places.
        
        Args:
            places: List of places visited
            days: Duration of trip
        """
        if not places:
            return
        
        place_types_seen = {}
        for place in places:
            types = place.get("types", [])
            for ptype in types:
                place_types_seen[ptype] = place_types_seen.get(ptype, 0) + 1
        
        # Map place types back to interests
        type_to_interest = {
            "restaurant": "food",
            "cafe": "food",
            "museum": "culture",
            "art_gallery": "art",
            "park": "nature",
            "shopping_mall": "shopping",
            "tourist_attraction": "history",
            "place_of_worship": "religious",
            "beach": "beaches",
            "hiking_area": "trekking",
            "bar": "nightlife",
        }
        
        for ptype, count in place_types_seen.items():
            interest = type_to_interest.get(ptype)
            if interest:
                old_count = self.preferences["interest_preferences"].get(interest, 0)
                self.preferences["interest_preferences"][interest] = old_count + count
    
    def get_recommended_interests(self, top_k: int = 4) -> List[str]:
        """
        Get user's top interests based on history.
        
        Args:
            top_k: Number of top interests to return
        
        Returns:
            List of recommended interests
        """
        interests = self.preferences["interest_preferences"]
        if not interests:
            return ["food", "culture", "nature", "history"]  # defaults
        
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        return [interest for interest, _ in sorted_interests[:top_k]]
    
    def get_recommended_budget(self) -> float:
        """Get user's typical budget based on history."""
        return self.preferences["budget_preferences"]["average_budget"] or 10000
    
    def get_recommended_duration(self) -> int:
        """Get user's typical trip duration."""
        recent_trips = self.preferences["visit_history"][-5:]
        if not recent_trips:
            return 3
        
        avg_days = sum(trip["days"] for trip in recent_trips) / len(recent_trips)
        return round(avg_days)
    
    def get_travel_pace_weights(self) -> Dict[str, float]:
        """
        Get activity weighting based on user's travel pace preference.
        
        Returns:
            Weights for activity intensity
        """
        pace = self.preferences["travel_patterns"]["travel_pace"]
        
        weights = {
            "fast": {
                "morning_activities": 1.3,
                "afternoon_activities": 1.3,
                "evening_activities": 1.2,
                "travel_flexibility": 0.8,
            },
            "moderate": {
                "morning_activities": 1.0,
                "afternoon_activities": 1.0,
                "evening_activities": 1.0,
                "travel_flexibility": 1.0,
            },
            "slow": {
                "morning_activities": 0.7,
                "afternoon_activities": 0.8,
                "evening_activities": 0.9,
                "travel_flexibility": 1.3,
            },
        }
        
        return weights.get(pace, weights["moderate"])
    
    def get_cost_distribution_preferences(self) -> Dict[str, float]:
        """
        Get user's preferred cost distribution.
        
        Returns:
            Dict with percentage preferences for each category
        """
        prefs = self.preferences["cost_preferences"]
        total = sum(prefs.values()) if any(prefs.values()) else 100
        
        if total == 0:
            return {
                "accommodation": 0.40,
                "food": 0.35,
                "activities": 0.15,
                "transport": 0.10,
            }
        
        return {
            "accommodation": prefs.get("accommodation_percent", 40) / 100,
            "food": prefs.get("food_percent", 35) / 100,
            "activities": prefs.get("activities_percent", 15) / 100,
            "transport": prefs.get("transport_percent", 10) / 100,
        }
    
    def should_revisit_destination(self, destination: str) -> bool:
        """
        Check if user might want to revisit a destination.
        
        Args:
            destination: Destination name
        
        Returns:
            True if user has visited before
        """
        visited = [trip["destination"] for trip in self.preferences["visit_history"]]
        return destination in visited
    
    def get_similar_past_trips(self, destination: str, interests: List[str]) -> List[Dict]:
        """
        Find similar past trips for reference.
        
        Args:
            destination: Target destination
            interests: User interests for this trip
        
        Returns:
            List of similar past trips
        """
        visits = self.preferences["visit_history"]
        similar = [
            trip for trip in visits
            if trip["destination"].lower() == destination.lower()
        ]
        
        return similar[-3:] if similar else []  # Return last 3 visits to this destination


def get_or_create_user_profile(user_id: str) -> UserProfile:
    """Get existing user profile or create new one."""
    return UserProfile(user_id)


def apply_user_preferences_to_weighting(
    user_profile: UserProfile,
    base_weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Adapt scoring weights based on user profile.
    
    Args:
        user_profile: UserProfile object
        base_weights: Default weights from scoring module
    
    Returns:
        Adjusted weights
    """
    adjusted = base_weights.copy()
    
    # If user consistently overspends on accommodation, reduce it
    spent_percent = user_profile.preferences["budget_preferences"]["spent_percent_avg"]
    if spent_percent and spent_percent > 100:
        adjusted["distance"] = adjusted.get("distance", 0.2) + 0.05
        adjusted["relevance"] = adjusted.get("relevance", 0.35) - 0.05
    
    # If user prefers slow pace, increase importance of being close by
    if user_profile.preferences["travel_patterns"]["travel_pace"] == "slow":
        adjusted["distance"] = adjusted.get("distance", 0.2) + 0.1
        adjusted["popularity"] = adjusted.get("popularity", 0.3) - 0.05
    
    # If user prefers fast pace, increase activity relevance
    if user_profile.preferences["travel_patterns"]["travel_pace"] == "fast":
        adjusted["relevance"] = adjusted.get("relevance", 0.35) + 0.1
        adjusted["distance"] = adjusted.get("distance", 0.2) - 0.05
    
    return adjusted
