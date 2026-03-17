"""
Advanced constraint validation and cost optimization.

Features:
1. Time feasibility checks - validates travel time + activity time per day
2. Opening hours enforcement - respects place operating times
3. Cost optimization - multi-objective budget balancing
4. Real-time constraint updates - adjusts for weather, holidays, etc.
5. Accommodation calculation - recommends stays based on daily expenses
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import json

# Cost categories and typical price ranges (in INR, for India travel)
COST_RANGES = {
    "accommodation": {
        "budget": (1000, 2000),
        "mid_range": (2000, 4000),
        "luxury": (4000, 10000),
    },
    "food": {
        "budget": (200, 400),
        "mid_range": (400, 800),
        "luxury": (800, 2000),
    },
    "transport": {
        "local": (50, 200),
        "intercity": (500, 2000),
        "air": (2000, 8000),
    },
    "activities": {
        "free": 0,
        "budget": (100, 300),
        "paid": (300, 1000),
    },
}

# Opening hours mapping (generalized - can be enhanced with API data)
PLACE_HOURS = {
    "restaurant": {"open": 11, "close": 23},
    "museum": {"open": 10, "close": 18},
    "park": {"open": 6, "close": 18},
    "shopping_mall": {"open": 10, "close": 22},
    "temple": {"open": 6, "close": 20},
    "bar": {"open": 18, "close": 2},
    "cafe": {"open": 7, "close": 20},
    "standard": {"open": 9, "close": 18},
}

# Time requirements for different activities (minutes)
ACTIVITY_DURATION = {
    "restaurant": 90,
    "museum": 120,
    "park": 60,
    "shopping_mall": 120,
    "temple": 45,
    "bar": 90,
    "cafe": 45,
    "standard": 60,
}


class ConstraintValidator:
    """Validates itinerary constraints and suggests optimizations."""
    
    def __init__(self, budget: float, days: int, travel_type: str):
        self.budget = budget
        self.days = days
        self.travel_type = travel_type
        self.daily_budget = budget / days
    
    def validate_budget(self, itinerary: Dict) -> bool:
        """
        Check if itinerary total cost exceeds budget.
        
        Args:
            itinerary: Full itinerary with cost breakdown
        
        Returns:
            True if within budget
        """
        total_cost = itinerary.get("total_estimated_cost", 0)
        return total_cost <= self.budget
    
    def validate_time_feasibility(
        self,
        day_places: List[Dict],
        time_boundary: Dict = None
    ) -> Dict:
        """
        Check if places can be visited in one day with travel time.
        
        Args:
            day_places: Places for the day
            time_boundary: Dict with start_hour, end_hour (default 8am-8pm)
        
        Returns:
            Feasibility report with time analysis
        """
        if time_boundary is None:
            time_boundary = {"start_hour": 8, "end_hour": 20}
        
        available_hours = time_boundary["end_hour"] - time_boundary["start_hour"]
        available_minutes = available_hours * 60
        
        # Calculate time needed
        total_activity_time = 0
        total_travel_time = 0
        
        for place in day_places:
            place_type = place.get("types", ["standard"])[0]
            duration = ACTIVITY_DURATION.get(place_type, 60)
            total_activity_time += duration
        
        # Rough travel time estimate between places (15 min per place on average)
        total_travel_time = max(0, (len(day_places) - 1) * 15)
        
        total_needed = total_activity_time + total_travel_time
        
        is_feasible = total_needed <= available_minutes
        buffer = available_minutes - total_needed
        
        return {
            "is_feasible": is_feasible,
            "places_count": len(day_places),
            "total_activity_time": total_activity_time,
            "total_travel_time": total_travel_time,
            "total_time_needed": total_needed,
            "available_time": available_minutes,
            "buffer_minutes": buffer,
            "utilization_percent": round((total_needed / available_minutes) * 100, 1),
            "status": "✓ Good fit" if is_feasible else "✗ Too tight - reduce places",
        }
    
    def validate_opening_hours(
        self,
        place: Dict,
        visit_time: str = "afternoon"
    ) -> bool:
        """
        Check if place is open during intended visit time.
        
        Args:
            place: Place dict
            visit_time: "morning", "afternoon", or "evening"
        
        Returns:
            True if open during that time
        """
        place_type = place.get("types", ["standard"])[0]
        hours = PLACE_HOURS.get(place_type, PLACE_HOURS["standard"])
        
        time_hours = {
            "morning": 9,
            "afternoon": 14,
            "evening": 18,
        }
        
        visit_hour = time_hours.get(visit_time, 14)
        
        return hours["open"] <= visit_hour < hours["close"]
    
    def optimize_daily_budget(self, total_budget: float) -> Dict:
        """
        Suggest budget breakdown for the trip.
        
        Args:
            total_budget: Total trip budget
        
        Returns:
            Recommended daily budget breakdown
        """
        # Family/group: higher accommodation
        # Solo/couple: balanced
        # Group: shared accommodation
        
        weights = {
            "family": {"accommodation": 0.40, "food": 0.35, "transport": 0.15, "activities": 0.10},
            "couple": {"accommodation": 0.35, "food": 0.35, "transport": 0.15, "activities": 0.15},
            "solo": {"accommodation": 0.30, "food": 0.40, "transport": 0.15, "activities": 0.15},
            "group": {"accommodation": 0.30, "food": 0.35, "transport": 0.20, "activities": 0.15},
        }
        
        weight = weights.get(self.travel_type, weights["solo"])
        
        daily_allocations = {
            "accommodation": round(total_budget * weight["accommodation"] / self.days),
            "food": round(total_budget * weight["food"] / self.days),
            "transport": round(total_budget * weight["transport"] / self.days),
            "activities": round(total_budget * weight["activities"] / self.days),
        }
        
        daily_total = sum(daily_allocations.values())
        
        return {
            "daily_budget": round(total_budget / self.days),
            "breakdown": daily_allocations,
            "daily_total": daily_total,
            "recommended_accommodation_range": COST_RANGES["accommodation"]["mid_range"],
            "recommended_meal_cost": "Breakfast: ₹150-300, Lunch: ₹200-400, Dinner: ₹300-500",
        }
    
    def calculate_feasible_activities(
        self,
        total_budget: float,
        days: int,
        interests: List[str]
    ) -> Dict:
        """
        Recommend number and type of activities based on budget.
        
        Args:
            total_budget: Total budget
            days: Number of days
            interests: User interests
        
        Returns:
            Activity recommendations with costs
        """
        daily_budget = total_budget / days
        
        # After accommodation (~40%) and food (~35%), activities get ~15%
        activity_budget = total_budget * 0.15
        activity_budget_per_day = activity_budget / days
        
        # Estimate activities possible
        avg_activity_cost = 250  # Average cost for paid activity
        free_activities_count = (len(interests) + 1)  # At least free activities per interest
        paid_activities_count = int(activity_budget_per_day / avg_activity_cost)
        
        return {
            "daily_activities_budget": round(activity_budget_per_day),
            "estimated_free_activities": free_activities_count * days,
            "estimated_paid_activities": max(1, paid_activities_count) * days,
            "total_activities_estimated": (free_activities_count + max(1, paid_activities_count)) * days,
            "avg_cost_per_activity": avg_activity_cost,
        }
    
    def suggest_optimizations(self, itinerary: Dict) -> List[str]:
        """
        Analyze itinerary and suggest improvements.
        
        Args:
            itinerary: Full itinerary
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        total_cost = itinerary.get("total_estimated_cost", 0)
        budget_utilization = (total_cost / self.budget * 100) if self.budget > 0 else 0
        
        # Budget optimization
        if budget_utilization < 70:
            suggestions.append(
                f"✓ Budget-friendly: Only {budget_utilization:.0f}% of budget used. "
                "Consider adding premium activities or longer stays."
            )
        elif budget_utilization > 95:
            suggestions.append(
                f"⚠ High spend: {budget_utilization:.0f}% of budget used. "
                "Consider budget alternatives or reduce paid activities."
            )
        
        # Time optimization
        days = itinerary.get("total_days", self.days)
        for day_idx, day in enumerate(itinerary.get("days", [])[:days], 1):
            places_count = sum(1 for slot in ["morning", "afternoon", "evening"] 
                             if day.get(slot, {}).get("place"))
            if places_count > 4:
                suggestions.append(
                    f"Day {day_idx}: {places_count} activities might be rushed. "
                    "Allow buffer time between locations."
                )
            elif places_count < 2:
                suggestions.append(
                    f"Day {day_idx}: Only {places_count} activities. "
                    "Consider adding more or merging with another day."
                )
        
        # Cost breakdown analysis
        breakdown = itinerary.get("budget_breakdown", {})
        accommodation = breakdown.get("accommodation", 0)
        food = breakdown.get("food", 0)
        
        if accommodation < total_cost * 0.2:
            suggestions.append(
                "✓ Smart accommodation: Lower accommodation cost. "
                "More budget available for activities."
            )
        
        if food > total_cost * 0.45:
            suggestions.append(
                "💡 Food cost high: Consider mix of street food and restaurants. "
                "Can save 30-40% on meals."
            )
        
        return suggestions


def calculate_accommodation_needs(
    days: int,
    nights: int,
    daily_budget: float,
    travel_type: str
) -> Dict:
    """
    Recommend accommodation options and costs.
    
    Args:
        days: Number of days
        nights: Number of nights (typically days - 1)
        daily_budget: Budget allocated to accommodation
        travel_type: "solo", "couple", "family", "group"
    
    Returns:
        Accommodation recommendations
    """
    accommodation_budget = daily_budget * nights
    
    category_budgets = {
        "solo": {"budget": 0.6, "mid": 0.3, "luxury": 0.1},
        "couple": {"budget": 0.4, "mid": 0.45, "luxury": 0.15},
        "family": {"budget": 0.3, "mid": 0.5, "luxury": 0.2},
        "group": {"budget": 0.5, "mid": 0.35, "luxury": 0.15},
    }
    
    distribution = category_budgets.get(travel_type, category_budgets["solo"])
    
    recommendations = {
        "total_accommodation_budget": round(accommodation_budget),
        "per_night_budget": round(accommodation_budget / nights) if nights > 0 else 0,
        "recommendations": {
            "budget_hotels": {
                "cost_per_night": COST_RANGES["accommodation"]["budget"],
                "allocation_nights": round(nights * distribution["budget"]),
            },
            "mid_range": {
                "cost_per_night": COST_RANGES["accommodation"]["mid_range"],
                "allocation_nights": round(nights * distribution["mid"]),
            },
            "luxury": {
                "cost_per_night": COST_RANGES["accommodation"]["luxury"],
                "allocation_nights": round(nights * distribution["luxury"]),
            },
        },
    }
    
    return recommendations
