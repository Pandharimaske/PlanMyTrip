#!/usr/bin/env python
"""
Quick Start Guide - Testing the Enhanced PlanMyTrip System

This document provides step-by-step instructions to test all new components.
"""

# ============================================================================
# SETUP & INSTALLATION
# ============================================================================

"""
1. Ensure all dependencies are installed (from pyproject.toml):
   - fastapi>=0.100.0
   - faiss-cpu>=1.13.2
   - langchain-groq>=1.1.2
   - sentence-transformers>=3.0.0
   - reportlab>=4.0.0
   - langgraph>=0.1.0
   - uvicorn>=0.30.0

2. Set environment variables:
   export GROQ_API_KEY="your-groq-api-key"
   export GOOGLE_MAPS_API_KEY="your-google-maps-key"
   export OPENWEATHER_API_KEY="your-openweather-key"

3. Start backend:
   cd backend
   .venv/bin/uvicorn main:app --reload --port 8000

4. Start frontend (optional):
   cd frontend
   npm run dev
"""

# ============================================================================
# TEST 1: Verify All Modules Load
# ============================================================================

def test_imports():
    """Verify all new modules import successfully."""
    print("Testing imports...")
    try:
        from scoring import score_places, calculate_relevance_score
        print("  ✓ scoring module")
        
        from route_optimizer import optimize_itinerary_routes, kmeans_clustering
        print("  ✓ route_optimizer module")
        
        from constraints import ConstraintValidator
        print("  ✓ constraints module")
        
        from user_preferences import UserProfile, get_or_create_user_profile
        print("  ✓ user_preferences module")
        
        from optimization_agent import optimize_places_for_trip
        print("  ✓ optimization_agent module")
        
        print("\n✅ All modules loaded successfully!\n")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        return False


# ============================================================================
# TEST 2: Test Scoring Module
# ============================================================================

def test_scoring():
    """Test the preference-weighted scoring system."""
    print("Testing scoring module...")
    from scoring import score_places
    
    # Sample places from Google Places API format
    sample_places = [
        {
            "name": "Falaknuma Palace",
            "rating": 4.5,
            "user_ratings_total": 2500,
            "types": ["tourist_attraction", "museum"],
            "lat": 17.3571,
            "lng": 78.4744,
            "address": "Hyderabad, Telangana"
        },
        {
            "name": "Charminar",
            "rating": 4.3,
            "user_ratings_total": 8000,
            "types": ["tourist_attraction", "historical_landmark"],
            "lat": 17.3629,
            "lng": 78.4733,
            "address": "Hyderabad, Telangana"
        },
        {
            "name": "Street Food Market",
            "rating": 4.1,
            "user_ratings_total": 1200,
            "types": ["restaurant", "cafe"],
            "lat": 17.3600,
            "lng": 78.4700,
            "address": "Hyderabad, Telangana"
        }
    ]
    
    interests = ["history", "food", "culture"]
    
    scored = score_places(sample_places, interests)
    
    print(f"\n  Input: {len(sample_places)} places, interests: {interests}")
    print(f"  Output: {len(scored)} scored places\n")
    
    for i, place in enumerate(scored, 1):
        print(f"  {i}. {place['name']}")
        print(f"     Score: {place['score']} (stars: {'★' * int(place['score']*5)})")
        print(f"     Components: {place['component_scores']}")
    
    print("\n✅ Scoring test complete!\n")
    return True


# ============================================================================
# TEST 3: Test Route Optimization
# ============================================================================

def test_route_optimization():
    """Test geographic clustering and TSP optimization."""
    print("Testing route optimization...")
    from route_optimizer import optimize_itinerary_routes
    
    # Sample 9 places (3 clusters)
    sample_places = [
        # Cluster 1: South Bangalore
        {"name": "Lumbini Garden", "lat": 12.8747, "lng": 77.6062, "rating": 4.0},
        {"name": "Bannerghatta Zoo", "lat": 12.8321, "lng": 77.6633, "rating": 4.2},
        {"name": "ISKCON Temple", "lat": 12.9729, "lng": 77.6522, "rating": 4.5},
        
        # Cluster 2: Central Bangalore  
        {"name": "Cubbon Park", "lat": 12.9352, "lng": 77.5898, "rating": 4.4},
        {"name": "Vidhana Soudha", "lat": 12.9334, "lng": 77.5891, "rating": 4.3},
        {"name": "Bangalore Palace", "lat": 12.9793, "lng": 77.5904, "rating": 4.3},
        
        # Cluster 3: North Bangalore
        {"name": "Whitefield Tech Park", "lat": 12.9698, "lng": 77.7490, "rating": 4.1},
        {"name": "Sri Venkateshwara Temple", "lat": 13.0837, "lng": 77.7710, "rating": 4.4},
        {"name": "Forum Value Mall", "lat": 13.0269, "lng": 77.7486, "rating": 4.2},
    ]
    
    days = 3
    routes = optimize_itinerary_routes(sample_places, days)
    
    print(f"\n  Input: {len(sample_places)} places, {days} days")
    print("  Optimized routes:\n")
    
    for day_idx, day_route in enumerate(routes, 1):
        if day_route:
            print(f"  Day {day_idx}:")
            for i, place in enumerate(day_route, 1):
                print(f"    {i}. {place['name']} ({place['lat']:.4f}, {place['lng']:.4f})")
    
    print("\n✅ Route optimization test complete!\n")
    return True


# ============================================================================
# TEST 4: Test Constraints & Validation
# ============================================================================

def test_constraints():
    """Test the constraint validation system."""
    print("Testing constraints module...")
    from constraints import ConstraintValidator, calculate_accommodation_needs
    
    validator = ConstraintValidator(budget=50000, days=5, travel_type="couple")
    
    # Test daily budget optimization
    breakdown = validator.optimize_daily_budget(50000)
    
    print(f"\n  Budget: ₹50,000 for 5 days (couple)")
    print(f"  Daily budget: ₹{breakdown['daily_budget']}")
    print(f"  Breakdown:")
    for category, amount in breakdown['breakdown'].items():
        print(f"    {category}: ₹{amount}")
    
    # Test time feasibility
    sample_day_activities = [
        {"name": "Museum", "types": ["museum"], "lat": 12.9, "lng": 77.6},
        {"name": "Park", "types": ["park"], "lat": 12.91, "lng": 77.61},
        {"name": "Restaurant", "types": ["restaurant"], "lat": 12.92, "lng": 77.62},
    ]
    
    feasibility = validator.validate_time_feasibility(sample_day_activities)
    
    print(f"\n  Time feasibility for {len(sample_day_activities)} activities:")
    print(f"    Total time needed: {feasibility['total_time_needed']} min")
    print(f"    Available time: {feasibility['available_time']} min")
    print(f"    Utilization: {feasibility['utilization_percent']}%")
    print(f"    Status: {feasibility['status']}")
    
    print("\n✅ Constraints test complete!\n")
    return True


# ============================================================================
# TEST 5: Test User Preferences & Learning
# ============================================================================

def test_user_preferences():
    """Test user preference learning."""
    print("Testing user preferences module...")
    from user_preferences import UserProfile
    
    # Create a new user profile
    user = UserProfile("test_user_123")
    
    # Simulate past trip
    sample_trip = {
        "destination": "Goa",
        "total_days": 5,
        "total_budget": 30000,
        "total_estimated_cost": 28500,
        "budget_breakdown": {
            "accommodation": 12000,
            "food": 8500,
            "activities": 4500,
            "transport": 3500
        },
        "places_data": [
            {"name": "Beach", "types": ["beach"], "lat": 15.4909, "lng": 73.8278},
            {"name": "Market", "types": ["shopping_mall"], "lat": 15.4938, "lng": 73.8274},
        ],
        "days": [
            {
                "day": 1,
                "morning": {"place": "Calangute Beach"},
                "afternoon": {"place": "Beach"},
                "evening": {"place": "Market"}
            },
            {
                "day": 2,
                "morning": {"place": "Beach"},
                "afternoon": {"place": "Beach"},
                "evening": {"place": "Restaurant"}
            },
        ]
    }
    
    # Record the trip
    user.add_trip(sample_trip)
    
    print(f"\n  Added trip to user profile")
    print(f"  Trips count: {user.preferences['trips_count']}")
    
    # Get recommendations
    recs = {
        "interests": user.get_recommended_interests(),
        "budget": user.get_recommended_budget(),
        "duration": user.get_recommended_duration(),
        "pace": user.preferences["travel_patterns"]["travel_pace"],
    }
    
    print(f"\n  Recommendations for next trip:")
    print(f"    Interests: {recs['interests']}")
    print(f"    Budget: ₹{recs['budget']}")
    print(f"    Duration: {recs['duration']} days")
    print(f"    Travel pace: {recs['pace']}")
    
    print("\n✅ User preferences test complete!\n")
    return True


# ============================================================================
# TEST 6: Test Full Optimization Pipeline
# ============================================================================

def test_full_optimization():
    """Test the complete optimization system."""
    print("Testing full optimization pipeline...")
    from optimization_agent import optimize_places_for_trip
    
    # Sample places (as if from Google Places API)
    places = [
        {"name": f"Place {i}", "rating": 3.5 + (i % 5) * 0.3, 
         "user_ratings_total": 500 + i * 100, "types": ["tourist_attraction"],
         "lat": 28.7041 + (i % 4) * 0.01, "lng": 77.1025 + (i % 5) * 0.01,
         "address": f"Delhi {i}"}
        for i in range(20)
    ]
    
    result = optimize_places_for_trip(
        places=places,
        interests=["history", "culture", "food"],
        budget=40000,
        days=4,
        travel_type="couple",
        user_id="test_user"
    )
    
    print(f"\n  Input: {len(places)} places")
    print(f"  Output:")
    print(f"    Optimized places: {len(result['optimized_places'])}")
    print(f"    Day routes: {len(result['day_routes'])} days")
    print(f"    Optimization quality: {result['insights']['optimization_quality']}")
    
    print("\n✅ Full optimization test complete!\n")
    return True


# ============================================================================
# TEST 7: Test via API (Requires running backend)
# ============================================================================

def test_api_call():
    """Test via actual API endpoint."""
    print("Testing via API endpoint...")
    print("  (Requires backend running on http://localhost:8000)\n")
    
    try:
        import httpx
        import asyncio
        
        async def call_api():
            async with httpx.AsyncClient(timeout=30) as client:
                url = "http://localhost:8000/api/plan"
                payload = {
                    "destination": "Jaipur",
                    "days": 3,
                    "budget": 25000,
                    "interests": ["history", "culture", "food"],
                    "travel_type": "couple",
                    "user_id": "test_user_api"
                }
                
                print(f"  POST {url}")
                print(f"  Payload: {payload}\n")
                
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✓ Status: {response.status_code}")
                    print(f"  Result keys: {list(result.keys())}")
                    print(f"  Days generated: {len(result.get('days', []))}")
                    print(f"  Total estimated cost: ₹{result.get('total_estimated_cost', 0)}")
                    print("\n✅ API test complete!\n")
                    return True
                else:
                    print(f"  ✗ Status: {response.status_code}")
                    print(f"  Error: {response.text}\n")
                    return False
        
        # Run async function
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(call_api())
        loop.close()
        return result
        
    except Exception as e:
        print(f"  ⚠ API test skipped: {e}")
        print("  (Backend may not be running)\n")
        return False


# ============================================================================
# MAIN: Run All Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PlanMyTrip - Enhanced System - Test Suite")
    print("=" * 80)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Scoring", test_scoring),
        ("Route Optimization", test_route_optimization),
        ("Constraints", test_constraints),
        ("User Preferences", test_user_preferences),
        ("Full Optimization", test_full_optimization),
        ("API Call", test_api_call),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}\n")
            results[test_name] = False
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("✨ All tests passed! System is ready.\n")
    else:
        print("⚠️  Some tests failed. Check output above.\n")
    
    print("=" * 80)
