from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent import generate_itinerary
from memory import save_trip, get_past_trips, get_trip_by_id, get_similar_trips
from pdf_export import build_pdf
from interactive_refinement import (
    InteractiveRefinementEngine,
    RefinementRequestModel,
    FeedbackSubmission,
    ApprovalRequest,
)

app = FastAPI(title="PlanMyTrip API")

# Initialize Human-in-the-Loop Engine
refinement_engine = InteractiveRefinementEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TripRequest(BaseModel):
    destination: str
    days: int
    budget: float
    interests: List[str]
    travel_type: str
    user_id: str = "default"

class SaveTripRequest(BaseModel):
    itinerary: dict
    user_id: str = "default"

class ChatRequest(BaseModel):
    message: str
    itinerary: dict
    history: List[dict] = []

@app.get("/")
def root():
    return {"status": "PlanMyTrip API running", "agents": ["weather","places","optimization","planner","constraint","explanation"]}

@app.post("/api/plan")
async def plan_trip(req: TripRequest):
    try:
        similar = get_similar_trips(req.destination, req.interests, top_k=2)
        result = await generate_itinerary(req)
        result["similar_past_trips"] = [
            {"destination": s["destination"], "days": s["days"], "id": s["id"]}
            for s in similar
        ]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_replan(req: ChatRequest):
    try:
        from chat import handle_chat
        response = await handle_chat(req.message, req.itinerary, req.history)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trips/save")
def save_trip_endpoint(req: SaveTripRequest):
    try:
        trip_id = save_trip(req.itinerary, req.user_id)
        
        # Also update user preferences based on this trip
        from user_preferences import get_or_create_user_profile
        user_profile = get_or_create_user_profile(req.user_id)
        user_profile.add_trip(req.itinerary)
        
        return {"success": True, "trip_id": trip_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trips/{user_id}")
def list_trips(user_id: str = "default"):
    return {"trips": get_past_trips(user_id)}

@app.get("/api/trips/load/{trip_id}")
def load_trip(trip_id: str):
    trip = get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@app.get("/api/recommendations/{user_id}")
def get_user_recommendations(user_id: str = "default"):
    """Get personalized recommendations based on user's trip history."""
    try:
        from user_preferences import get_or_create_user_profile
        user_profile = get_or_create_user_profile(user_id)
        
        return {
            "recommended_interests": user_profile.get_recommended_interests(),
            "recommended_budget": user_profile.get_recommended_budget(),
            "recommended_duration": user_profile.get_recommended_duration(),
            "travel_pace": user_profile.preferences["travel_patterns"]["travel_pace"],
            "favorite_destinations": user_profile.preferences["travel_patterns"]["favorite_destinations"],
            "past_trips_count": user_profile.preferences["trips_count"],
            "cost_preferences": user_profile.get_cost_distribution_preferences(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/pdf")
def export_pdf(itinerary: dict):
    try:
        pdf_bytes = build_pdf(itinerary)
        dest = itinerary.get("destination", "trip").replace(" ", "_")
        filename = f"PlanMyTrip_{dest}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HUMAN-IN-THE-LOOP ENDPOINTS - Interactive Refinement
# ============================================================================

@app.post("/api/review/start")
def start_review_session(request: dict):
    """
    Start interactive review session for itinerary.
    
    POST body:
    {
      "user_id": "user123",
      "itinerary_id": "trip_001",
      "itinerary": {...},
      "optimization_data": {...},
      "places_data": [...]
    }
    """
    try:
        review_session = refinement_engine.start_review_session(
            user_id=request.get("user_id"),
            itinerary_id=request.get("itinerary_id"),
            itinerary=request.get("itinerary", {}),
            optimization_data=request.get("optimization_data", {}),
            places_data=request.get("places_data", []),
        )
        return review_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/review/{session_id}/details")
def get_review_details(session_id: str, day: int, time_slot: str):
    """
    Get detailed info about a specific activity in review.
    
    Shows alternatives and reasoning.
    """
    try:
        details = refinement_engine.get_review_point_details(
            session_id=session_id,
            day=day,
            time_slot=time_slot,
        )
        if "error" in details:
            raise HTTPException(status_code=404, detail=details["error"])
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review/{session_id}/refine")
def apply_refinement(session_id: str, refinement: RefinementRequestModel):
    """
    Apply user refinement to an activity.
    
    Refinement types:
    - "replace": Change to alternative place
    - "swap": Swap with another time slot
    - "remove": Remove activity
    - "reorder": Move to different time
    
    Example:
    {
      "user_id": "user123",
      "itinerary_id": "trip_001",
      "request_type": "replace",
      "day": 1,
      "time_slot": "morning",
      "details": {"place_name": "Alternative Place", "cost": 500},
      "reason": "Prefer this place instead"
    }
    """
    try:
        result = refinement_engine.apply_refinement(session_id, refinement)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/review/{session_id}/preview")
def get_approval_preview(session_id: str):
    """
    Get final preview before approval.
    
    Shows changes made and final cost comparison.
    """
    try:
        preview = refinement_engine.get_approval_preview(session_id)
        if "error" in preview:
            raise HTTPException(status_code=404, detail=preview["error"])
        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review/{session_id}/approve")
def approve_itinerary(session_id: str, approval: ApprovalRequest):
    """
    Finalize and approve itinerary.
    
    Example:
    {
      "user_id": "user123",
      "itinerary_id": "trip_001",
      "approved": true,
      "final_itinerary": {...}
    }
    """
    try:
        result = refinement_engine.finalize_itinerary(session_id, approval)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Save the approved itinerary
        if result.get("status") == "approved":
            save_trip(approval.final_itinerary, approval.user_id)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback/submit")
def submit_trip_feedback(feedback: FeedbackSubmission):
    """
    Submit feedback after completing trip.
    
    Example:
    {
      "user_id": "user123",
      "itinerary_id": "trip_001",
      "overall_satisfaction": 5,
      "timing_fit": 4,
      "cost_accuracy": 5,
      "place_variety": 4,
      "comments": "Amazing trip! Best vacation ever.",
      "what_went_well": ["Smooth travel", "Great timing", "Budget accurate"],
      "what_could_improve": ["Could have more restaurants"],
      "would_revisit": true,
      "actual_expenses": {
        "accommodation": 11000,
        "food": 7500,
        "activities": 5000,
        "transport": 3200
      }
    }
    """
    try:
        result = refinement_engine.submit_feedback(feedback)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/{user_id}/history")
def get_user_trip_history(user_id: str):
    """
    Get user's trip history, feedback summary, and personalized insights.
    
    Shows:
    - Number of trips completed
    - Average satisfaction ratings
    - Insights about preferences
    - Personalized recommendations for next trip
    """
    try:
        history = refinement_engine.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
