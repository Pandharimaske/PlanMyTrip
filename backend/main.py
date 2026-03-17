from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import io

from agent import generate_itinerary
from memory import save_trip, get_past_trips, get_trip_by_id, get_similar_trips
from pdf_export import build_pdf

app = FastAPI(title="PlanMyTrip API")

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
    return {"status": "PlanMyTrip API running", "agents": ["weather","places","planner","constraint","explanation"]}

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
