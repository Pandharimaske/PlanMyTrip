"""
Human-in-the-Loop System for PlanMyTrip

Provides interactive refinement, feedback collection, and transparency 
in AI decision-making to ensure good user experience and control.

Features:
1. Interactive refinement before finalizing itinerary
2. Explanation of AI decisions
3. User feedback collection
4. Alternative suggestions
5. Parameter adjustment interface
6. Approval workflow
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ScoreExplanation:
    """Explain why a place got its score."""
    place_name: str
    total_score: float
    components: Dict[str, float]
    reasoning: str  # Human-readable explanation
    alternatives: List[str]  # Alternative places in same category


@dataclass
class ItineraryReviewPoint:
    """Single point in itinerary that user can review/adjust."""
    day: int
    time_slot: str  # "morning", "afternoon", "evening"
    place_name: str
    activity: str
    duration: str
    cost: float
    lat: float
    lng: float
    reasoning: str
    score: float
    alternatives: List[Dict]  # Alternative suggestions


@dataclass
class UserFeedback:
    """Collect user feedback on itinerary."""
    user_id: str
    itinerary_id: str
    overall_satisfaction: int  # 1-5
    timing_fit: int  # 1-5 (was schedule realistic?)
    cost_accuracy: int  # 1-5 (were costs accurate?)
    place_variety: int  # 1-5 (good mix of activities?)
    comments: str
    what_went_well: List[str]
    what_could_improve: List[str]
    would_revisit: bool
    timestamp: str


@dataclass
class RefinementRequest:
    """User request to refine itinerary."""
    user_id: str
    itinerary_id: str
    request_type: str  # "add", "remove", "swap", "reorder", "adjust_time"
    day: int
    time_slot: str
    details: Dict  # Type-specific details
    reason: Optional[str]


# ============================================================================
# HUMAN-IN-THE-LOOP ENGINE
# ============================================================================

class HumanInTheLoopEngine:
    """Manages interactive refinement and user approval workflow."""
    
    def __init__(self, storage_dir: str = "./hitl_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.feedback_dir = self.storage_dir / "feedback"
        self.feedback_dir.mkdir(exist_ok=True)
    
    def generate_review_points(
        self,
        itinerary: Dict,
        optimization_data: Dict,
        places_data: List[Dict]
    ) -> List[ItineraryReviewPoint]:
        """
        Convert itinerary into human-reviewable points with explanations.
        
        Args:
            itinerary: Full itinerary dict
            optimization_data: Optimization insights and scoring
            places_data: All places with scores
        
        Returns:
            List of review points user can interact with
        """
        review_points = []
        places_by_name = {p["name"]: p for p in places_data}
        
        for day_data in itinerary.get("days", []):
            day_num = day_data.get("day", 1)
            
            for time_slot in ["morning", "afternoon", "evening"]:
                slot_data = day_data.get(time_slot, {})
                if not slot_data or not slot_data.get("place"):
                    continue
                
                place_name = slot_data.get("place")
                place_info = places_by_name.get(place_name, {})
                
                # Generate reasoning
                reasoning = self._generate_place_reasoning(
                    place_name,
                    time_slot,
                    place_info,
                    day_data.get("theme", "")
                )
                
                # Get alternatives
                alternatives = self._get_alternative_places(
                    place_info,
                    places_data,
                    time_slot,
                    count=3
                )
                
                review_point = ItineraryReviewPoint(
                    day=day_num,
                    time_slot=time_slot,
                    place_name=place_name,
                    activity=slot_data.get("activity", ""),
                    duration=slot_data.get("duration", ""),
                    cost=slot_data.get("cost", 0),
                    lat=slot_data.get("lat", 0),
                    lng=slot_data.get("lng", 0),
                    reasoning=reasoning,
                    score=place_info.get("score", 0),
                    alternatives=alternatives
                )
                review_points.append(review_point)
        
        return review_points
    
    def _generate_place_reasoning(
        self,
        place_name: str,
        time_slot: str,
        place_info: Dict,
        day_theme: str
    ) -> str:
        """Generate human-readable explanation for why place is recommended."""
        components = place_info.get("component_scores", {})
        
        reasons = []
        
        # Relevance
        if components.get("relevance", 0) > 0.7:
            reasons.append("Highly relevant to your interests")
        
        # Popularity
        if components.get("popularity", 0) > 0.8:
            reasons.append("Popular and well-reviewed")
        elif place_info.get("rating", 0) > 4.5:
            reasons.append("Highly rated by visitors")
        
        # Distance
        if components.get("distance", 0) > 0.8:
            reasons.append("Conveniently located")
        
        # Timing
        if time_slot == "morning":
            reasons.append("Good for morning exploration")
        elif time_slot == "afternoon":
            reasons.append("Peak time for this activity")
        elif time_slot == "evening":
            reasons.append("Beautiful sunset/evening experience")
        
        # Theme
        if day_theme:
            reasons.append(f"Fits today's theme: {day_theme}")
        
        return " • ".join(reasons) if reasons else "Selected for your trip"
    
    def _get_alternative_places(
        self,
        current_place: Dict,
        all_places: List[Dict],
        time_slot: str,
        count: int = 3
    ) -> List[Dict]:
        """Get alternative places user could choose instead."""
        current_types = set(current_place.get("types", []))
        
        # Find similar places
        similar = []
        for place in all_places:
            if place.get("name") == current_place.get("name"):
                continue  # Skip current place
            
            place_types = set(place.get("types", []))
            
            # Calculate type similarity
            intersection = len(current_types.intersection(place_types))
            if intersection > 0:  # Has some type overlap
                similar.append({
                    "name": place.get("name"),
                    "rating": place.get("rating", 0),
                    "distance_km": self._estimate_distance(
                        current_place.get("lat", 0),
                        current_place.get("lng", 0),
                        place.get("lat", 0),
                        place.get("lng", 0)
                    ),
                    "score": place.get("score", 0),
                    "address": place.get("address", ""),
                })
        
        # Sort by score and return top N
        similar.sort(key=lambda x: x["score"], reverse=True)
        return similar[:count]
    
    def _estimate_distance(self, lat1, lng1, lat2, lng2) -> float:
        """Quick distance estimate in km."""
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    
    def generate_refinement_suggestions(
        self,
        itinerary: Dict,
        optimization_data: Dict
    ) -> List[str]:
        """
        Suggest refinements user might want to consider.
        
        Args:
            itinerary: Full itinerary
            optimization_data: Optimization insights
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        # Check utilization
        util_percent = optimization_data.get("route_metrics", {}).get(
            "utilization_percent", 50
        )
        
        if util_percent < 40:
            suggestions.append(
                "💡 Your schedule is quite relaxed. Would you like to add more activities for a fuller experience?"
            )
        elif util_percent > 85:
            suggestions.append(
                "⚠️ Your schedule is packed. Consider spreading travel over an extra day for comfort."
            )
        
        # Check cost
        cost = itinerary.get("total_estimated_cost", 0)
        budget = itinerary.get("total_budget", 0)
        if budget > 0:
            util_budget = (cost / budget) * 100
            if util_budget < 60:
                suggestions.append(
                    f"💰 You're using only {util_budget:.0f}% of budget. Want to add premium experiences?"
                )
        
        # Check place variety
        place_types = set()
        for day in itinerary.get("days", []):
            for slot in ["morning", "afternoon", "evening"]:
                if day.get(slot, {}).get("place"):
                    place_data = day.get(slot, {})
                    place_types.add(place_data.get("place", ""))
        
        if len(place_types) < 4:
            suggestions.append(
                "🎯 Limited variety so far. Interested in adding different types of activities?"
            )
        
        return suggestions
    
    def apply_refinement(
        self,
        itinerary: Dict,
        places_data: List[Dict],
        refinement: RefinementRequest
    ) -> Dict:
        """
        Apply user refinement to itinerary.
        
        Args:
            itinerary: Current itinerary
            places_data: All available places
            refinement: User refinement request
        
        Returns:
            Updated itinerary
        """
        day_idx = refinement.day - 1
        slot = refinement.time_slot
        
        if day_idx >= len(itinerary["days"]):
            return itinerary
        
        day = itinerary["days"][day_idx]
        
        if refinement.request_type == "swap":
            # Swap with another time slot
            other_slot = refinement.details.get("other_slot")
            if other_slot in day:
                day[slot], day[other_slot] = day[other_slot], day[slot]
        
        elif refinement.request_type == "replace":
            # Replace with alternative place
            new_place_name = refinement.details.get("place_name")
            new_place = next(
                (p for p in places_data if p["name"] == new_place_name),
                None
            )
            
            if new_place and slot in day:
                day[slot].update({
                    "place": new_place_name,
                    "lat": new_place.get("lat", 0),
                    "lng": new_place.get("lng", 0),
                    "cost": refinement.details.get("cost", day[slot].get("cost", 0)),
                })
        
        elif refinement.request_type == "remove":
            # Remove activity from slot
            day[slot] = {}
        
        elif refinement.request_type == "reorder":
            # Reorder time slots (move activity to different time)
            source_slot = refinement.details.get("source_slot")
            if source_slot in day:
                day[slot] = day[source_slot]
                day[source_slot] = {}
        
        # Recalculate daily cost
        day["day_total_cost"] = sum(
            day.get(s, {}).get("cost", 0)
            for s in ["morning", "afternoon", "evening"]
        )
        
        return itinerary
    
    def collect_feedback(
        self,
        user_id: str,
        itinerary_id: str,
        feedback_data: Dict,
        actual_expenses: Dict = None
    ) -> bool:
        """
        Collect and store user feedback after trip completion.
        
        Args:
            user_id: User identifier
            itinerary_id: Itinerary identifier
            feedback_data: User ratings and comments
            actual_expenses: Track actual vs estimated costs
        
        Returns:
            True if feedback saved successfully
        """
        try:
            feedback = UserFeedback(
                user_id=user_id,
                itinerary_id=itinerary_id,
                overall_satisfaction=feedback_data.get("overall_satisfaction", 3),
                timing_fit=feedback_data.get("timing_fit", 3),
                cost_accuracy=feedback_data.get("cost_accuracy", 3),
                place_variety=feedback_data.get("place_variety", 3),
                comments=feedback_data.get("comments", ""),
                what_went_well=feedback_data.get("what_went_well", []),
                what_could_improve=feedback_data.get("what_could_improve", []),
                would_revisit=feedback_data.get("would_revisit", True),
                timestamp=datetime.now().isoformat(),
            )
            
            # Save feedback
            feedback_file = self.feedback_dir / f"{user_id}_{itinerary_id}.json"
            with open(feedback_file, "w") as f:
                json.dump(asdict(feedback), f, indent=2)
            
            # If we have cost tracking, save that too
            if actual_expenses:
                cost_file = self.feedback_dir / f"{user_id}_{itinerary_id}_costs.json"
                with open(cost_file, "w") as f:
                    json.dump({
                        "estimated": feedback_data.get("estimated_costs", {}),
                        "actual": actual_expenses,
                        "timestamp": datetime.now().isoformat(),
                    }, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
    
    def get_user_insights(self, user_id: str) -> Dict:
        """
        Analyze feedback to identify user patterns and preferences.
        
        Args:
            user_id: User identifier
        
        Returns:
            Insights about user preferences and satisfaction
        """
        feedback_files = list(self.feedback_dir.glob(f"{user_id}_*"))
        
        if not feedback_files:
            return {
                "trips_count": 0,
                "average_satisfaction": 0,
                "insights": []
            }
        
        satisfactions = []
        timing_fits = []
        cost_accuracies = []
        place_varieties = []
        common_improvements = {}
        
        for file in feedback_files:
            if "_costs" in str(file):
                continue
            
            try:
                with open(file, "r") as f:
                    feedback = json.load(f)
                
                satisfactions.append(feedback.get("overall_satisfaction", 3))
                timing_fits.append(feedback.get("timing_fit", 3))
                cost_accuracies.append(feedback.get("cost_accuracy", 3))
                place_varieties.append(feedback.get("place_variety", 3))
                
                for improvement in feedback.get("what_could_improve", []):
                    common_improvements[improvement] = common_improvements.get(improvement, 0) + 1
            except:
                continue
        
        avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 0
        
        # Generate insights
        insights = []
        
        if avg_satisfaction >= 4.5:
            insights.append("✨ Very satisfied traveler - consistently positive feedback")
        elif avg_satisfaction < 2.5:
            insights.append("⚠️ May need better planning - recent trips less satisfactory")
        
        if sum(timing_fits) / len(timing_fits) if timing_fits else 0 < 3:
            insights.append("💡 Consider more relaxed schedules in future trip planning")
        
        if sum(cost_accuracies) / len(cost_accuracies) if cost_accuracies else 0 > 4:
            insights.append("💰 Cost estimates are accurate for this user")
        
        return {
            "trips_count": len(satisfactions),
            "average_satisfaction": round(avg_satisfaction, 2),
            "timing_average": round(sum(timing_fits) / len(timing_fits), 1) if timing_fits else 0,
            "cost_accuracy": round(sum(cost_accuracies) / len(cost_accuracies), 1) if cost_accuracies else 0,
            "place_variety_average": round(sum(place_varieties) / len(place_varieties), 1) if place_varieties else 0,
            "most_common_improvement": max(common_improvements.items(), key=lambda x: x[1])[0] if common_improvements else None,
            "insights": insights,
        }
    
    def generate_approval_summary(self, itinerary: Dict) -> Dict:
        """
        Generate user-friendly summary for final approval.
        
        Args:
            itinerary: Full itinerary
        
        Returns:
            Summary dict for user review
        """
        return {
            "destination": itinerary.get("destination"),
            "duration": f"{itinerary.get('total_days')} days",
            "budget": f"₹{itinerary.get('total_budget', 0):,.0f}",
            "estimated_cost": f"₹{itinerary.get('total_estimated_cost', 0):,.0f}",
            "cost_breakdown": itinerary.get("budget_breakdown", {}),
            "daily_highlights": [
                {
                    "day": day.get("day"),
                    "theme": day.get("theme"),
                    "activities_count": sum(
                        1 for slot in ["morning", "afternoon", "evening"]
                        if day.get(slot, {}).get("place")
                    )
                }
                for day in itinerary.get("days", [])
            ],
            "weather_note": itinerary.get("weather_note"),
            "packing_tips": itinerary.get("packing_tips", []),
            "ready_to_finalize": True,
        }
