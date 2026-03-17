"""
Multi-agent itinerary planner using LangGraph.

Agents:
  1. WeatherAgent     — fetches & summarises weather
  2. PlacesAgent      — fetches & scores POIs
  3. PlannerAgent     — builds raw day-wise itinerary
  4. ConstraintAgent  — validates budget & feasibility
  5. ExplanationAgent — adds tips, packing list, weather note
"""

import os, json, asyncio
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from tools import get_weather, get_places

# llm = ChatGroq(
#     api_key=os.getenv("GROQ_API_KEY"),
#     model="llama3-70b-8192",
#     temperature=0.5,
#     max_tokens=4096,
# )
llm = None
# ── Shared State ─────────────────────────────────────────────────────────────

class TripState(TypedDict):
    destination: str
    days: int
    budget: float
    interests: List[str]
    travel_type: str
    weather: dict
    places: List[dict]
    raw_itinerary: dict
    validated_itinerary: dict
    final_itinerary: dict
    error: str

# ── Helper ───────────────────────────────────────────────────────────────────

def call_llm_json(prompt: str) -> dict:
    response = llm.invoke(prompt)
    content = response.content.strip()
    start = content.find("{")
    end = content.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"LLM returned no JSON: {content[:200]}")
    return json.loads(content[start:end])

# ── Agent 1: Weather ─────────────────────────────────────────────────────────

def weather_agent(state: TripState) -> TripState:
    loop = asyncio.new_event_loop()
    try:
        weather = loop.run_until_complete(get_weather(state["destination"]))
    finally:
        loop.close()
    state["weather"] = weather
    return state

# ── Agent 2: Places ──────────────────────────────────────────────────────────

def places_agent(state: TripState) -> TripState:
    loop = asyncio.new_event_loop()
    try:
        places = loop.run_until_complete(
            get_places(state["destination"], state["interests"], state["days"])
        )
    finally:
        loop.close()
    state["places"] = places
    return state

# ── Agent 3: Planner ─────────────────────────────────────────────────────────

def planner_agent(state: TripState) -> TripState:
    places_text = "\n".join([
        f"- {p['name']} | Rating: {p['rating']} | {p['address']} | lat:{p['lat']:.4f} lng:{p['lng']:.4f}"
        for p in state["places"]
    ])
    w = state["weather"]
    weather_str = f"{w.get('description','')}, {w.get('temp',28)}°C, humidity {w.get('humidity',60)}%"

    prompt = f"""You are a travel planning AI. Build a {state['days']}-day trip itinerary for {state['destination']}.

Trip info:
- Travel type: {state['travel_type']}
- Total budget: ₹{int(state['budget'])}
- Interests: {', '.join(state['interests'])}
- Weather: {weather_str}

Available places (USE ONLY THESE, include lat/lng from list):
{places_text}

Rules:
- Group nearby places (same lat/lng area) on the same day
- Each day has morning, afternoon, evening
- Realistic Indian pricing in ₹
- day_total_cost = sum of all 3 slot costs

Return ONLY valid JSON:
{{
  "days": [
    {{
      "day": 1,
      "theme": "string",
      "morning": {{"place": "string", "activity": "string", "duration": "2 hours", "cost": 500, "lat": 0.0, "lng": 0.0}},
      "afternoon": {{"place": "string", "activity": "string", "duration": "3 hours", "cost": 800, "lat": 0.0, "lng": 0.0}},
      "evening": {{"place": "string", "activity": "string", "duration": "2 hours", "cost": 400, "lat": 0.0, "lng": 0.0}},
      "day_total_cost": 1700
    }}
  ],
  "total_estimated_cost": 5000,
  "budget_breakdown": {{"accommodation": 2000, "food": 1500, "transport": 800, "activities": 700}}
}}"""

    result = call_llm_json(prompt)
    state["raw_itinerary"] = result
    return state

# ── Agent 4: Constraint ──────────────────────────────────────────────────────

def constraint_agent(state: TripState) -> TripState:
    raw = state["raw_itinerary"]
    budget = state["budget"]

    prompt = f"""You are a budget validation AI. Review this itinerary and fix:
1. total_estimated_cost must NOT exceed ₹{int(budget)}
2. Each day_total_cost must equal morning.cost + afternoon.cost + evening.cost
3. budget_breakdown values must sum to total_estimated_cost
4. No 0-cost slots allowed

Return the CORRECTED itinerary as ONLY valid JSON, same structure.

Itinerary:
{json.dumps(raw, indent=2)}"""

    try:
        state["validated_itinerary"] = call_llm_json(prompt)
    except Exception:
        state["validated_itinerary"] = raw
    return state

# ── Agent 5: Explanation ─────────────────────────────────────────────────────

def explanation_agent(state: TripState) -> TripState:
    validated = state["validated_itinerary"]
    w = state["weather"]
    weather_str = f"{w.get('description','')}, {w.get('temp',28)}°C"

    prompt = f"""You are a travel guide AI. Add these fields to the itinerary JSON:
1. "weather_note": one sentence travel advisory for {state['destination']} given "{weather_str}"
2. "tip" field inside each day object: one practical, specific travel tip for that day
3. "packing_tips": list of exactly 4 items to pack for this specific trip

Return the COMPLETE JSON with additions. ONLY valid JSON, no extra text.

Input:
{json.dumps(validated, indent=2)}"""

    try:
        result = call_llm_json(prompt)
    except Exception:
        result = validated

    result["destination"] = state["destination"]
    result["total_days"] = state["days"]
    result["total_budget"] = state["budget"]
    result["weather"] = state["weather"]
    result["places_data"] = state["places"]
    state["final_itinerary"] = result
    return state

# ── Build Graph ───────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(TripState)
    g.add_node("weather_node", weather_agent)
    g.add_node("places_node", places_agent)
    g.add_node("planner_node", planner_agent)
    g.add_node("constraint_node", constraint_agent)
    g.add_node("explanation_node", explanation_agent)

    g.set_entry_point("weather_node")
    g.add_edge("weather_node", "places_node")
    g.add_edge("places_node", "planner_node")
    g.add_edge("planner_node", "constraint_node")
    g.add_edge("constraint_node", "explanation_node")
    g.add_edge("explanation_node", END)
    return g.compile()

GRAPH = build_graph()

async def generate_itinerary(req) -> dict:
    initial: TripState = {
        "destination": req.destination,
        "days": req.days,
        "budget": req.budget,
        "interests": req.interests,
        "travel_type": req.travel_type,
        "weather": {},
        "places": [],
        "raw_itinerary": {},
        "validated_itinerary": {},
        "final_itinerary": {},
        "error": "",
    }

    import concurrent.futures
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, lambda: GRAPH.invoke(initial))

    final = result.get("final_itinerary", {})
    if not final:
        raise ValueError("Agents failed to generate itinerary")
    return final
