"""
Memory system using FAISS + sentence-transformers.
Saves trip summaries as embeddings so we can retrieve
similar past trips and personalise future suggestions.
"""

import os, json, pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

MEMORY_DIR = Path("./memory_store")
MEMORY_DIR.mkdir(exist_ok=True)
INDEX_PATH  = MEMORY_DIR / "trips.index"
META_PATH   = MEMORY_DIR / "trips_meta.pkl"

MODEL_NAME = "all-MiniLM-L6-v2"
DIM = 384

_encoder = None
_index   = None
_meta    = None

def _get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(MODEL_NAME)
    return _encoder

def _load_store():
    global _index, _meta
    if _index is None:
        if INDEX_PATH.exists() and META_PATH.exists():
            _index = faiss.read_index(str(INDEX_PATH))
            with open(META_PATH, "rb") as f:
                _meta = pickle.load(f)
        else:
            _index = faiss.IndexFlatL2(DIM)
            _meta = []

def _save_store():
    faiss.write_index(_index, str(INDEX_PATH))
    with open(META_PATH, "wb") as f:
        pickle.dump(_meta, f)

def _trip_to_text(itinerary: dict) -> str:
    dest   = itinerary.get("destination", "")
    days   = itinerary.get("total_days", "")
    budget = itinerary.get("total_budget", "")
    cost   = itinerary.get("total_estimated_cost", "")
    places = [
        slot["place"]
        for day in itinerary.get("days", [])
        for slot in [day.get("morning",{}), day.get("afternoon",{}), day.get("evening",{})]
        if slot.get("place")
    ]
    themes = [d.get("theme","") for d in itinerary.get("days", [])]
    return (
        f"Trip to {dest} for {days} days, budget Rs{budget}, "
        f"estimated cost Rs{cost}. "
        f"Themes: {', '.join(themes)}. "
        f"Places visited: {', '.join(places[:10])}."
    )

def save_trip(itinerary: dict, user_id: str = "default") -> str:
    _load_store()
    enc  = _get_encoder()
    text = _trip_to_text(itinerary)
    vec  = enc.encode([text], convert_to_numpy=True).astype("float32")
    _index.add(vec)
    trip_id = f"{user_id}_{itinerary.get('destination','')}_{len(_meta)}"
    _meta.append({
        "id": trip_id,
        "destination": itinerary.get("destination",""),
        "days":   itinerary.get("total_days",""),
        "budget": itinerary.get("total_budget",""),
        "cost":   itinerary.get("total_estimated_cost",""),
        "summary": text,
        "itinerary": itinerary,
    })
    _save_store()
    return trip_id

def get_past_trips(user_id: str = "default") -> list:
    _load_store()
    return [
        {"id": m["id"], "destination": m["destination"],
         "days": m["days"], "budget": m["budget"],
         "cost": m["cost"], "summary": m["summary"]}
        for m in _meta if m["id"].startswith(user_id)
    ]

def get_trip_by_id(trip_id: str):
    _load_store()
    for m in _meta:
        if m["id"] == trip_id:
            return m["itinerary"]
    return None

def get_similar_trips(destination: str, interests: list, top_k: int = 3) -> list:
    _load_store()
    if _index.ntotal == 0:
        return []
    enc   = _get_encoder()
    query = f"Trip to {destination} with interests: {', '.join(interests)}"
    vec   = enc.encode([query], convert_to_numpy=True).astype("float32")
    k     = min(top_k, _index.ntotal)
    distances, indices = _index.search(vec, k)
    return [
        {**_meta[idx], "score": float(distances[0][i])}
        for i, idx in enumerate(indices[0]) if idx < len(_meta)
    ]
