"""
Interactive Refinement API - User approval workflow

Provides endpoints for users to:
1. Review generated itinerary with AI explanations
2. Refine specific activities before finalizing
3. Get alternatives and suggestions
4. Finalize and approve
5. Submit feedback after trip
"""

from typing import List, Dict, Optional
from pydantic import BaseModel
from human_in_loop import (
    HumanInTheLoopEngine,
    RefinementRequest,
    ItineraryReviewPoint,
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ReviewRequest(BaseModel):
    """Request to review itinerary."""
    user_id: str
    itinerary_id: str
    itinerary: dict
    optimization_data: dict
    places_data: List[dict]


class RefinementRequestModel(BaseModel):
    """User refinement request."""
    user_id: str
    itinerary_id: str
    request_type: str  # "add", "remove", "swap", "replace", "reorder"
    day: int
    time_slot: str
    details: Dict
    reason: Optional[str] = None


class FeedbackSubmission(BaseModel):
    """User trip feedback."""
    user_id: str
    itinerary_id: str
    overall_satisfaction: int  # 1-5
    timing_fit: int
    cost_accuracy: int
    place_variety: int
    comments: str
    what_went_well: List[str]
    what_could_improve: List[str]
    would_revisit: bool
    actual_expenses: Optional[Dict] = None


class ApprovalRequest(BaseModel):
    """Request to finalize/approve itinerary."""
    user_id: str
    itinerary_id: str
    approved: bool
    final_itinerary: dict


# ============================================================================
# INTERACTIVE REFINEMENT ENGINE
# ============================================================================

class InteractiveRefinementEngine:
    """Manages interactive refinement workflow."""
    
    def __init__(self):
        self.hitl = HumanInTheLoopEngine()
        self.sessions = {}  # Store session state
    
    def start_review_session(
        self,
        user_id: str,
        itinerary_id: str,
        itinerary: Dict,
        optimization_data: Dict,
        places_data: List[Dict],
    ) -> Dict:
        """
        Start an interactive review session.
        
        Args:
            user_id: User ID
            itinerary_id: Itinerary ID
            itinerary: Generated itinerary
            optimization_data: Optimization metrics
            places_data: All places with scores
        
        Returns:
            Review session data
        """
        # Generate review points
        review_points = self.hitl.generate_review_points(
            itinerary,
            optimization_data,
            places_data
        )
        
        # Generate suggestions
        suggestions = self.hitl.generate_refinement_suggestions(
            itinerary,
            optimization_data
        )
        
        # Generate approval summary
        approval_summary = self.hitl.generate_approval_summary(itinerary)
        
        # Store session
        session_id = f"{user_id}_{itinerary_id}_{len(self.sessions)}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "itinerary_id": itinerary_id,
            "itinerary": itinerary.copy(),
            "original_itinerary": itinerary.copy(),
            "places_data": places_data,
            "refinements_applied": [],
            "status": "reviewing",
        }
        
        return {
            "session_id": session_id,
            "status": "review_in_progress",
            "step": "1_review",
            "review_points": [
                {
                    "day": rp.day,
                    "time_slot": rp.time_slot,
                    "place_name": rp.place_name,
                    "activity": rp.activity,
                    "duration": rp.duration,
                    "cost": rp.cost,
                    "reasoning": rp.reasoning,
                    "score": rp.score,
                    "alternatives": rp.alternatives,
                }
                for rp in review_points
            ],
            "suggestions": suggestions,
            "approval_summary": approval_summary,
            "message": "Review your itinerary. You can refine any activity before approving.",
        }
    
    def get_review_point_details(
        self,
        session_id: str,
        day: int,
        time_slot: str
    ) -> Dict:
        """
        Get detailed info about a specific review point.
        
        Args:
            session_id: Review session ID
            day: Day number
            time_slot: Time slot
        
        Returns:
            Detailed review point with more alternatives
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        itinerary = session["itinerary"]
        places_data = session["places_data"]
        
        if day > len(itinerary["days"]):
            return {"error": "Day not found"}
        
        day_data = itinerary["days"][day - 1]
        slot_data = day_data.get(time_slot, {})
        place_name = slot_data.get("place", "")
        
        place_info = next(
            (p for p in places_data if p["name"] == place_name),
            {}
        )
        
        # Get detailed alternatives
        current_types = set(place_info.get("types", []))
        similar_places = []
        
        for place in places_data:
            if place.get("name") == place_name:
                continue
            place_types = set(place.get("types", []))
            if len(current_types.intersection(place_types)) > 0:
                similar_places.append({
                    "name": place.get("name"),
                    "rating": place.get("rating"),
                    "score": place.get("score"),
                    "address": place.get("address"),
                    "cost_estimate": 500 + int(place.get("rating", 4) * 100),
                    "why_similar": "Similar type of activity",
                })
        
        similar_places.sort(key=lambda x: x["score"], reverse=True)
        
        # Determine which time slots this activity can be swapped to
        swap_options = {
            "morning": ["afternoon", "evening"],
            "afternoon": ["morning", "evening"],
            "evening": ["morning", "afternoon"],
        }
        can_swap_to = swap_options.get(time_slot, ["morning", "afternoon", "evening"])
        
        return {
            "current_selection": {
                "place": place_name,
                "activity": slot_data.get("activity"),
                "duration": slot_data.get("duration"),
                "cost": slot_data.get("cost"),
                "reasoning": self.hitl._generate_place_reasoning(
                    place_name, time_slot, place_info, day_data.get("theme", "")
                ),
            },
            "alternatives": similar_places[:8],
            "can_remove": True,
            "can_swap_to": can_swap_to,
        }
    
    def apply_refinement(
        self,
        session_id: str,
        refinement: RefinementRequestModel
    ) -> Dict:
        """
        Apply user refinement to itinerary.
        
        Args:
            session_id: Review session ID
            refinement: User refinement request
        
        Returns:
            Updated itinerary and confirmation
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Create refinement object
        ref = RefinementRequest(
            user_id=refinement.user_id,
            itinerary_id=refinement.itinerary_id,
            request_type=refinement.request_type,
            day=refinement.day,
            time_slot=refinement.time_slot,
            details=refinement.details,
            reason=refinement.reason,
        )
        
        # Apply refinement
        updated_itinerary = self.hitl.apply_refinement(
            session["itinerary"],
            session["places_data"],
            ref
        )
        
        session["itinerary"] = updated_itinerary
        session["refinements_applied"].append({
            "type": refinement.request_type,
            "day": refinement.day,
            "time_slot": refinement.time_slot,
            "reason": refinement.reason,
        })
        
        return {
            "status": "refinement_applied",
            "refinement_type": refinement.request_type,
            "message": f"✅ {refinement.request_type.capitalize()} applied successfully",
            "updated_itinerary": updated_itinerary,
            "refinements_count": len(session["refinements_applied"]),
        }
    
    def get_approval_preview(self, session_id: str) -> Dict:
        """
        Get final preview before approval.
        
        Args:
            session_id: Review session ID
        
        Returns:
            Final review summary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        itinerary = session["itinerary"]
        original = session["original_itinerary"]
        
        # Calculate changes
        changes_made = {
            "refinements_count": len(session["refinements_applied"]),
            "refinement_types": list(set(r["type"] for r in session["refinements_applied"])),
        }
        
        # Calculate cost difference
        original_cost = original.get("total_estimated_cost", 0)
        new_cost = itinerary.get("total_estimated_cost", 0)
        cost_diff = new_cost - original_cost
        
        return {
            "original_cost": original_cost,
            "updated_cost": new_cost,
            "cost_change": f"₹{cost_diff:+.0f}",
            "within_budget": new_cost <= itinerary.get("total_budget", 0),
            "changes_made": changes_made,
            "final_summary": self.hitl.generate_approval_summary(itinerary),
            "ready_to_approve": True,
        }
    
    def finalize_itinerary(
        self,
        session_id: str,
        approval_request: ApprovalRequest
    ) -> Dict:
        """
        Finalize and approve itinerary.
        
        Args:
            session_id: Review session ID
            approval_request: User approval
        
        Returns:
            Finalization result
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if not approval_request.approved:
            session["status"] = "cancelled"
            return {
                "status": "cancelled",
                "message": "Itinerary cancelled by user",
            }
        
        # Save approval metadata
        session["status"] = "approved"
        session["final_itinerary"] = approval_request.final_itinerary
        session["approved_at"] = datetime.now().isoformat()
        
        return {
            "status": "approved",
            "itinerary_id": approval_request.itinerary_id,
            "message": "✨ Itinerary approved and saved!",
            "refinements_applied": session["refinements_applied"],
            "next_step": "You can now export as PDF or share with companions",
            "action_items": [
                "📱 Share itinerary with travel companions",
                "🎫 Book attractions in advance",
                "🏨 Confirm hotel reservations",
                "✈️ Save important contact numbers",
            ]
        }
    
    def submit_feedback(
        self,
        feedback: FeedbackSubmission
    ) -> Dict:
        """
        Submit post-trip feedback.
        
        Args:
            feedback: User feedback after trip
        
        Returns:
            Feedback confirmation
        """
        success = self.hitl.collect_feedback(
            user_id=feedback.user_id,
            itinerary_id=feedback.itinerary_id,
            feedback_data={
                "overall_satisfaction": feedback.overall_satisfaction,
                "timing_fit": feedback.timing_fit,
                "cost_accuracy": feedback.cost_accuracy,
                "place_variety": feedback.place_variety,
                "comments": feedback.comments,
                "what_went_well": feedback.what_went_well,
                "what_could_improve": feedback.what_could_improve,
                "would_revisit": feedback.would_revisit,
            },
            actual_expenses=feedback.actual_expenses,
        )
        
        if not success:
            return {"status": "error", "message": "Failed to save feedback"}
        
        # Get insights
        insights = self.hitl.get_user_insights(feedback.user_id)
        
        return {
            "status": "feedback_saved",
            "message": "🙏 Thank you for your feedback!",
            "insights": insights,
            "next_actions": [
                "📊 Your preferences have been updated",
                "🎯 Better suggestions for your next trip",
                "💡 Your feedback helps us improve",
            ] if feedback.overall_satisfaction >= 4 else [
                "⚠️ We noted areas for improvement",
                "👀 We'll adjust our recommendations",
                "📞 Consider sharing specific feedback",
            ]
        }
    
    def get_user_history(self, user_id: str) -> Dict:
        """
        Get user's trip history and feedback summary.
        
        Args:
            user_id: User identifier
        
        Returns:
            User history and insights
        """
        insights = self.hitl.get_user_insights(user_id)
        
        return {
            "user_id": user_id,
            "trips_completed": insights["trips_count"],
            "overall_satisfaction": f"{insights['average_satisfaction']}/5",
            "timing_average": f"{insights['timing_average']}/5",
            "cost_accuracy": f"{insights['cost_accuracy']}/5",
            "insights": insights["insights"],
            "recommendations": self._generate_personalized_recommendations(insights),
        }
    
    def _generate_personalized_recommendations(self, insights: Dict) -> List[str]:
        """Generate recommendations based on user insights."""
        recommendations = []
        
        if insights["average_satisfaction"] < 3:
            recommendations.append("Next trip should have fewer activities to reduce stress")
        elif insights["average_satisfaction"] > 4.5:
            recommendations.append("You're very satisfied - try more complex/longer trips")
        
        if insights["timing_average"] < 3:
            recommendations.append("Recommend more buffer time in future schedules")
        
        if insights["cost_accuracy"] > 4:
            recommendations.append("Cost estimates work well for you - budget accordingly")
        else:
            recommendations.append("Consider adding 15-20% buffer to estimated costs")
        
        if insights["place_variety_average"] < 3:
            recommendations.append("Add more diverse activity types in future trips")
        
        return recommendations


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

from datetime import datetime

def create_interactive_flow() -> InteractiveRefinementEngine:
    """Factory function to create refinement engine."""
    return InteractiveRefinementEngine()


def format_review_message(review_data: Dict) -> str:
    """Format review data into user-friendly message."""
    message = """
    🎯 Your itinerary is ready for review!
    
    ✅ Generated Details:
    - Destination: {destination}
    - Duration: {duration}
    - Budget: {budget}
    - Estimated Cost: {estimated_cost}
    
    📋 Review Process:
    1. Review each activity and its reasoning
    2. Check out alternatives if you want different suggestions
    3. Make any refinements you'd like
    4. Approve when ready
    
    💡 You can: Add/remove activities, change timing, swap suggestions, or adjust costs
    
    Ready to review? Let's go! 👇
    """.strip()
    
    return message.format(**review_data.get("approval_summary", {}))
