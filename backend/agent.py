"""
Multi-agent itinerary planner using LangGraph.

Agents:
  1. WeatherAgent        — fetches & summarises weather
  2. PlacesAgent         — fetches & scores POIs
  3. OptimizationAgent   — clusters & optimizes route efficiency
  4. PlannerAgent        — builds day-wise itinerary with optimized places
  5. ConstraintAgent     — validates budget & time feasibility
  6. ExplanationAgent    — adds tips, packing list, weather note
"""

import os, json, asyncio
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from tools import get_weather, get_places, get_hotels
from optimization_agent import optimize_places_for_trip
from user_preferences import get_or_create_user_profile

# Load environment variables from .env file
load_dotenv()

# llm = ChatGroq(
#     api_key=os.getenv("GROQ_API_KEY"),
#     model="llama-3.3-70b-versatile",
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
    user_id: str
    weather: dict
    places: List[dict]
    hotels: List[dict]
    optimized_places: List[dict]
    day_routes: List[List[dict]]
    optimization_insights: dict
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
        hotels = loop.run_until_complete(
            get_hotels(state["destination"], state["budget"], state["days"])
        )
    finally:
        loop.close()
    state["places"] = places
    state["hotels"] = hotels
    return state

# ── Agent 3: Optimization ────────────────────────────────────────────────────

def optimization_agent(state: TripState) -> TripState:
    """Optimize places using clustering, scoring, and route optimization."""
    try:
        optimization_result = optimize_places_for_trip(
            places=state["places"],
            interests=state["interests"],
            budget=state["budget"],
            days=state["days"],
            travel_type=state["travel_type"],
            user_id=state.get("user_id", "default"),
        )
        
        state["optimized_places"] = optimization_result.get("optimized_places", [])
        state["day_routes"] = optimization_result.get("day_routes", [])
        state["optimization_insights"] = optimization_result.get("insights", {})
    except Exception as e:
        # If optimization fails, fall back to original places
        state["optimized_places"] = state["places"]
        state["day_routes"] = []
        state["optimization_insights"] = {"error": str(e)}
    
    return state

# ── Agent 4: Planner ────────────────────────────────────────────────────────

def planner_agent(state: TripState) -> TripState:
    # Use optimized places if available, otherwise fall back to raw places
    places_to_use = state.get("optimized_places", state.get("places", []))
    
    # If we have optimized routes, use them as hints for clustering
    route_hints = ""
    if state.get("day_routes"):
        for day_idx, day_route in enumerate(state["day_routes"][:state["days"]], 1):
            if day_route:
                route_hints += f"\nDay {day_idx} suggested places: {', '.join(p['name'] for p in day_route[:3])}"
    
    places_text = "\n".join([
        f"- {p['name']} | Rating: {p['rating']} | Score: {p.get('score', 0)} | {p['address']} | lat:{p['lat']:.4f} lng:{p['lng']:.4f}"
        for p in places_to_use
    ])
    
    w = state["weather"]
    weather_str = f"{w.get('description','')}, {w.get('temp',28)}°C, humidity {w.get('humidity',60)}%"

    prompt = f"""You are a travel planning AI. Build a {state['days']}-day trip itinerary for {state['destination']}.

Trip info:
- Travel type: {state['travel_type']}
- Total budget: ₹{int(state['budget'])}
- Interests: {', '.join(state['interests'])}
- Weather: {weather_str}

Optimization hints (places already grouped for efficiency):{route_hints}

Available places (scored by relevance, USE ONLY THESE, include lat/lng from list):
{places_text}

Rules:
- Follow the suggested grouping for each day to minimize travel time
- Each day has morning, afternoon, evening
- Realistic Indian pricing in ₹
- day_total_cost = sum of all 3 slot costs
- Prefer places with higher scores above

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

# ── Agent 5: Constraint ──────────────────────────────────────────────────────

def constraint_agent(state: TripState) -> TripState:
    raw = state["raw_itinerary"]
    budget = state["budget"]
    
    # Enhanced validation using new constraints module
    from constraints import ConstraintValidator
    validator = ConstraintValidator(budget, state["days"], state["travel_type"])
    
    # Prepare validation context
    validation_info = f"""
Budget validation ({validator.travel_type} trip):
- Total budget: ₹{int(budget)}
- Daily budget: ₹{int(validator.daily_budget)}
- Number of days: {state['days']}

Optimization insights:
- Total places selected: {len(state.get('optimized_places', state['places']))}
- Route clustering quality: {state.get('optimization_insights', {}).get('optimization_quality', 'unknown')}
"""

    prompt = f"""You are a budget validation AI. Review this itinerary and fix:
1. total_estimated_cost must NOT exceed ₹{int(budget)}
2. Each day_total_cost must equal morning.cost + afternoon.cost + evening.cost
3. budget_breakdown values must sum to total_estimated_cost
4. No 0-cost slots allowed
5. Consider {validator.travel_type}-specific budget distribution
{validation_info}

Return the CORRECTED itinerary as ONLY valid JSON, same structure.

Itinerary:
{json.dumps(raw, indent=2)}"""

    try:
        state["validated_itinerary"] = call_llm_json(prompt)
    except Exception:
        state["validated_itinerary"] = raw
    return state

# ── Agent 6: Explanation ────────────────────────────────────────────────────

def explanation_agent(state: TripState) -> TripState:
    validated = state["validated_itinerary"]
    w = state["weather"]
    weather_str = f"{w.get('description','')}, {w.get('temp',28)}°C"
    
    # Add optimization insights to the prompt
    insights_text = ""
    if state.get("optimization_insights"):
        insights = state["optimization_insights"]
        insights_text = f"""
Route Optimization Quality: {insights.get('optimization_quality', 'good')}
Daily average utilization: {sum(r.get('utilization_percent', 50) for r in insights.get('feasibility_reports', [{}])) / max(1, len(insights.get('feasibility_reports', [{}]))) if isinstance(insights.get('feasibility_reports'), list) else 'N/A'}%
Place type diversity: {insights.get('place_type_diversity', {}).get('total_types', 'varied')} types
"""

    prompt = f"""You are a travel guide AI. Add these fields to the itinerary JSON:
1. "weather_note": one sentence travel advisory for {state['destination']} given "{weather_str}"
2. "tip" field inside each day object: one practical, specific travel tip for that day
3. "packing_tips": list of exactly 4 items to pack for this specific trip
4. "optimization_notes": brief note about route efficiency based on:
{insights_text}

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
    result["places_data"] = state.get("optimized_places", state["places"])
    result["optimization"] = state.get("optimization_insights", {})
    result["hotels"] = state.get("hotels", [])
    # Select best mid-range hotel by default
    if state.get("hotels") and len(state["hotels"]) > 1:
        result["selected_hotel"] = state["hotels"][1]  # Mid-range hotel
        result["accommodation_cost"] = state["hotels"][1]["price_per_night"] * state["days"]
    state["final_itinerary"] = result
    return state

# ── Build Graph ───────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(TripState)
    g.add_node("weather_node", weather_agent)
    g.add_node("places_node", places_agent)
    g.add_node("optimization_node", optimization_agent)
    g.add_node("planner_node", planner_agent)
    g.add_node("constraint_node", constraint_agent)
    g.add_node("explanation_node", explanation_agent)

    g.set_entry_point("weather_node")
    g.add_edge("weather_node", "places_node")
    g.add_edge("places_node", "optimization_node")
    g.add_edge("optimization_node", "planner_node")
    g.add_edge("planner_node", "constraint_node")
    g.add_edge("constraint_node", "explanation_node")
    g.add_edge("explanation_node", END)
    return g.compile()

GRAPH = build_graph()

async def generate_itinerary(req) -> dict:
    # Initialize LLM if using LangChain
    global llm
    if llm is None:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model="llama-3.3-70b-versatile",
                temperature=0.5,
                max_tokens=4096,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM: {str(e)}")
    
    initial: TripState = {
        "destination": req.destination,
        "days": req.days,
        "budget": req.budget,
        "interests": req.interests,
        "travel_type": req.travel_type,
        "user_id": getattr(req, "user_id", "default"),
        "weather": {},
        "places": [],
        "hotels": [],
        "optimized_places": [],
        "day_routes": [],
        "optimization_insights": {},
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
