"""
Optimization Agent - orchestrates route optimization, scoring, and constraint checking.

This agent runs after places are fetched and before the planner agent,
optimizing which places to include and in what order.
"""

from typing import List, Dict
from scoring import score_places, WEIGHTS as DEFAULT_WEIGHTS
from route_optimizer import (
    optimize_itinerary_routes,
    calculate_day_feasibility,
    estimate_travel_time,
    build_distance_matrix,
)
from constraints import ConstraintValidator
from user_preferences import get_or_create_user_profile, apply_user_preferences_to_weighting


def optimize_places_for_trip(
    places: List[Dict],
    interests: List[str],
    budget: float,
    days: int,
    travel_type: str,
    user_id: str = "default"
) -> Dict:
    """
    Orchestrate complete place optimization for a trip.
    
    Args:
        places: All scraped places from Google Places API
        interests: User interests
        budget: Total trip budget
        days: Number of days
        travel_type: solo/couple/family/group
        user_id: For personalization
    
    Returns:
        Optimized places, routes, and recommendations
    """
    
    # 1. Load user profile for personalization
    user_profile = get_or_create_user_profile(user_id)
    weights = apply_user_preferences_to_weighting(user_profile, DEFAULT_WEIGHTS.copy())
    
    # 2. Score places based on interests and preferences
    scored_places = score_places(places, interests)
    
    # Filter to top places (reasonable number per day)
    places_per_day = min(6, max(3, len(scored_places) // days))
    max_places = places_per_day * days
    filtered_places = scored_places[:max_places]
    
    # 3. Optimize routes with clustering and TSP
    day_routes = optimize_itinerary_routes(filtered_places, days)
    
    # 4. Validate feasibility and calculate metrics
    validator = ConstraintValidator(budget, days, travel_type)
    feasibility_reports = []
    
    for day_idx, day_places in enumerate(day_routes, 1):
        feasibility = calculate_day_feasibility(day_places, time_slots=3)
        feasibility_reports.append({
            "day": day_idx,
            **feasibility
        })
    
    # 5. Generate optimization insights
    insights = generate_optimization_insights(
        filtered_places,
        day_routes,
        feasibility_reports,
        budget,
        days,
        validator
    )
    
    return {
        "optimized_places": filtered_places,
        "day_routes": day_routes,
        "feasibility_reports": feasibility_reports,
        "insights": insights,
        "scoring_details": {
            "weights_used": weights,
            "total_places_evaluated": len(places),
            "places_selected": len(filtered_places),
        }
    }


def generate_optimization_insights(
    places: List[Dict],
    day_routes: List[List[Dict]],
    feasibility_reports: List[Dict],
    budget: float,
    days: int,
    validator: ConstraintValidator,
) -> Dict:
    """
    Generate insights about the optimized itinerary.
    
    Args:
        places: Optimized places
        day_routes: Routes per day
        feasibility_reports: Time feasibility for each day
        budget: Trip budget
        days: Number of days
        validator: Constraint validator
    
    Returns:
        Dictionary with optimization insights
    """
    
    insights = {
        "optimization_quality": assess_optimization_quality(feasibility_reports),
        "route_metrics": calculate_route_metrics(day_routes),
        "recommendations": [],
    }
    
    # Check time efficiency
    avg_utilization = sum(
        report.get("utilization_percent", 0) for report in feasibility_reports
    ) / len(feasibility_reports) if feasibility_reports else 0
    
    if avg_utilization < 50:
        insights["recommendations"].append(
            "✓ Relaxed pace: Good balance between activities and rest."
        )
    elif avg_utilization > 85:
        insights["recommendations"].append(
            "⚠ Tight schedule: Consider reducing places or extending trip."
        )
    
    # Check geographic clustering quality
    total_distance = sum(
        calculate_route_distance(day_route)
        for day_route in day_routes if day_route
    )
    
    avg_daily_distance = total_distance / days if days > 0 else 0
    if avg_daily_distance < 20:
        insights["recommendations"].append(
            "✓ Excellent clustering: Minimal travel time between activities."
        )
    elif avg_daily_distance > 50:
        insights["recommendations"].append(
            "💡 High travel distance: Consider focusing on specific areas per day."
        )
    
    # Cost insights
    daily_budget = budget / days if days > 0 else 0
    insights["daily_budget_guidance"] = f"₹{int(daily_budget)}/day"
    
    # Place diversity
    place_types = {}
    for place in places:
        for ptype in place.get("types", []):
            place_types[ptype] = place_types.get(ptype, 0) + 1
    
    insights["place_type_diversity"] = {
        "total_types": len(place_types),
        "distribution": dict(sorted(place_types.items(), key=lambda x: x[1], reverse=True)[:5]),
    }
    
    return insights


def assess_optimization_quality(feasibility_reports: List[Dict]) -> str:
    """
    Assess overall quality of optimization.
    
    Args:
        feasibility_reports: Time feasibility for each day
    
    Returns:
        Quality assessment string
    """
    if not feasibility_reports:
        return "unknown"
    
    avg_util = sum(
        report.get("utilization_percent", 0) for report in feasibility_reports
    ) / len(feasibility_reports)
    
    all_feasible = all(report.get("feasible", False) for report in feasibility_reports)
    
    if all_feasible and 40 < avg_util < 85:
        return "excellent"
    elif all_feasible and avg_util <= 40:
        return "good_relaxed"
    elif all_feasible and avg_util >= 85:
        return "good_packed"
    else:
        return "needs_adjustment"


def calculate_route_metrics(day_routes: List[List[Dict]]) -> Dict:
    """
    Calculate metrics for optimized routes.
    
    Args:
        day_routes: Routes per day
    
    Returns:
        Route metrics
    """
    metrics = {
        "days_with_activities": sum(1 for route in day_routes if route),
        "total_places": sum(len(route) for route in day_routes),
        "avg_places_per_day": 0,
        "max_places_in_day": 0,
        "min_places_in_day": 0,
    }
    
    if day_routes:
        place_counts = [len(route) for route in day_routes]
        metrics["avg_places_per_day"] = sum(place_counts) / len(day_routes)
        metrics["max_places_in_day"] = max(place_counts) if place_counts else 0
        metrics["min_places_in_day"] = min(place_counts) if place_counts else 0
    
    return metrics


def calculate_route_distance(route: List[Dict]) -> float:
    """
    Calculate total distance for a route.
    
    Args:
        route: List of places
    
    Returns:
        Total distance in km
    """
    if not route or len(route) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(route) - 1):
        from route_optimizer import haversine_distance
        dist = haversine_distance(
            route[i]["lat"], route[i]["lng"],
            route[i+1]["lat"], route[i+1]["lng"]
        )
        total += dist
    
    return round(total, 1)
