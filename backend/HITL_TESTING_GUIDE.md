# Human-in-the-Loop Testing Guide - End-to-End Workflow

This guide provides complete curl commands and responses to test the entire HITL workflow.

## Prerequisites

```bash
# Ensure backend is running
cd /Users/pandhari/Desktop/PlanMyTrip/backend
python -m uvicorn main:app --reload --port 8000
```

Backend should be at: `http://localhost:8000`

---

## Test Sequence

### Step 1: Generate Initial Itinerary

```bash
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "num_days": 3,
    "budget": 30000,
    "travel_type": "couple",
    "interests": ["beaches", "food", "nightlife"],
    "trip_name": "Goa Beach Getaway"
  }'
```

**Expected Response (200):**
```json
{
  "itinerary_id": "goa_couple_3d_20240115_abc123",
  "destination": "Goa",
  "num_days": 3,
  "budget": 30000,
  "status": "generated",
  "daily_plans": [
    {
      "day": 1,
      "theme": "Arrival & Beach Relaxation",
      "activities": [
        {
          "time": "09:00",
          "activity": "Calangute Beach - Walk & Breakfast",
          "place": "Calangute Beach",
          "duration": "2 hours",
          "cost": 500,
          "category": "beach"
        },
        {
          "time": "12:00",
          "activity": "Seafood Lunch at Fisherman's Wharf",
          "place": "Fisherman's Wharf",
          "duration": "1.5 hours",
          "cost": 1200,
          "category": "food"
        }
      ]
    },
    {
      "day": 2,
      "theme": "Water Sports & Nightlife",
      "activities": [
        {
          "time": "09:00",
          "activity": "Parasailing at Baga Beach",
          "place": "Baga Beach",
          "duration": "1 hour",
          "cost": 2500,
          "category": "water_sports"
        }
      ]
    }
  ],
  "total_estimated_cost": 24500,
  "optimization_data": {
    "optimized_places": [...],
    "day_routes": [...],
    "clustering_info": {...}
  }
}
```

**Save these values:**
- `itinerary_id`: `goa_couple_3d_20240115_abc123`
- `user_id`: Generate: `test_user_001` (for testing)

---

### Step 2: Start Interactive Review Session

```bash
curl -X POST http://localhost:8000/api/review/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "itinerary_id": "goa_couple_3d_20240115_abc123",
    "itinerary": {
      "destination": "Goa",
      "num_days": 3,
      "budget": 30000,
      "daily_plans": [...]
    },
    "optimization_data": {
      "optimized_places": [...],
      "day_routes": [...],
      "clustering_info": {...}
    },
    "places_data": [
      {
        "name": "Calangute Beach",
        "category": "beach",
        "rating": 4.6,
        "score": 0.87,
        "lat": 15.5500,
        "lng": 73.7500
      }
    ]
  }'
```

**Expected Response (200):**
```json
{
  "session_id": "test_user_001_goa_couple_3d_20240115_abc123_0",
  "status": "review_in_progress",
  "step": "1_review",
  "user_id": "test_user_001",
  "itinerary_id": "goa_couple_3d_20240115_abc123",
  "review_points": [
    {
      "day": 1,
      "time_slot": "morning",
      "place_name": "Calangute Beach",
      "activity": "Calangute Beach - Walk & Breakfast",
      "duration": "2 hours",
      "cost": 500,
      "reasoning": "Popular beach destination (4.6⭐) • Perfect for morning beach walks • Good proximity to accommodation",
      "score": 0.87,
      "alternatives": [
        {
          "name": "Baga Beach",
          "rating": 4.5,
          "score": 0.85,
          "reasoning": "Similar beach experience with water sports options"
        },
        {
          "name": "Anjuna Beach",
          "rating": 4.3,
          "score": 0.82,
          "reasoning": "More peaceful beach, famous for flea market"
        }
      ]
    },
    {
      "day": 1,
      "time_slot": "lunch",
      "place_name": "Fisherman's Wharf",
      "activity": "Seafood Lunch at Fisherman's Wharf",
      "duration": "1.5 hours",
      "cost": 1200,
      "reasoning": "Highly rated seafood restaurant (4.7⭐) • matches your food interests • Good pricing",
      "score": 0.91,
      "alternatives": [
        {
          "name": "Pousada by the Beach",
          "rating": 4.5,
          "score": 0.88,
          "reasoning": "Similar beachfront dining experience"
        }
      ]
    }
  ],
  "suggestions": [
    "💡 Your 3-day schedule is well-balanced between activities and relaxation",
    "💰 Using 82% of ₹30,000 budget (₹24,500 estimated cost)",
    "🗺️ Daily travel time optimized - average 40 min between activities"
  ],
  "approval_summary": {
    "destination": "Goa",
    "duration": "3 days",
    "budget": "₹30,000",
    "estimated_cost": "₹24,500",
    "cost_buffer": "₹5,500"
  }
}
```

**Save:**
- `session_id`: `test_user_001_goa_couple_3d_20240115_abc123_0`

---

### Step 3: Review Activity Details with Alternatives

```bash
curl -X GET "http://localhost:8000/api/review/test_user_001_goa_couple_3d_20240115_abc123_0/details?day=1&time_slot=morning"
```

**Expected Response (200):**
```json
{
  "day": 1,
  "time_slot": "morning",
  "current_selection": {
    "place": "Calangute Beach",
    "activity": "Calangute Beach - Walk & Breakfast",
    "cost": 500,
    "duration": "2 hours",
    "reasoning": "Popular beach destination (4.6⭐) • Perfect for morning beach walks • Good proximity to accommodation",
    "score": 0.87,
    "score_breakdown": {
      "relevance": 0.95,
      "popularity": 0.90,
      "distance": 0.75,
      "opening_hours": 1.0
    }
  },
  "alternatives": [
    {
      "name": "Baga Beach",
      "rating": 4.5,
      "score": 0.85,
      "cost_estimate": 500,
      "why_similar": "Similar beach experience with water sports options nearby",
      "pros": ["Water sports available", "Good infrastructure"],
      "cons": ["More crowded"]
    },
    {
      "name": "Anjuna Beach",
      "rating": 4.3,
      "score": 0.82,
      "cost_estimate": 500,
      "why_similar": "More peaceful beach alternative",
      "pros": ["Quieter atmosphere", "Flea market on weekends"],
      "cons": ["Farther from accommodation"]
    },
    {
      "name": "Miramar Beach",
      "rating": 4.2,
      "score": 0.78,
      "cost_estimate": 400,
      "why_similar": "Close alternative beach",
      "pros": ["Closest to North Goa", "Budget-friendly"],
      "cons": ["Smaller, less famous"]
    }
  ],
  "actions": {
    "can_replace": true,
    "can_remove": true,
    "can_swap_time_slot": ["afternoon", "evening"],
    "recommendations": [
      "⭐ Current choice is best match for your interests",
      "💡 If you prefer quieter vibe, try Anjuna Beach alternative"
    ]
  }
}
```

---

### Step 4A: Apply Refinement - REPLACE Activity

```bash
curl -X POST http://localhost:8000/api/review/test_user_001_goa_couple_3d_20240115_abc123_0/refine \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "itinerary_id": "goa_couple_3d_20240115_abc123",
    "request_type": "replace",
    "day": 1,
    "time_slot": "morning",
    "details": {
      "place_name": "Anjuna Beach",
      "activity": "Anjuna Beach - Walk & Breakfast",
      "cost": 500
    },
    "reason": "Prefer quieter beach atmosphere"
  }'
```

**Expected Response (200):**
```json
{
  "status": "refinement_applied",
  "refinement_type": "replace",
  "session_id": "test_user_001_goa_couple_3d_20240115_abc123_0",
  "message": "✅ Activity replaced successfully: Calangute Beach → Anjuna Beach",
  "refinement_details": {
    "day": 1,
    "time_slot": "morning",
    "old_place": "Calangute Beach",
    "new_place": "Anjuna Beach",
    "cost_change": 0,
    "reason": "Prefer quieter beach atmosphere"
  },
  "updated_total_cost": 24500,
  "refinements_count": 1,
  "refinement_history": [
    {
      "type": "replace",
      "day": 1,
      "time_slot": "morning"
    }
  ]
}
```

---

### Step 4B: Apply Refinement - REMOVE Activity

```bash
curl -X POST http://localhost:8000/api/review/test_user_001_goa_couple_3d_20240115_abc123_0/refine \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "itinerary_id": "goa_couple_3d_20240115_abc123",
    "request_type": "remove",
    "day": 2,
    "time_slot": "afternoon",
    "details": {},
    "reason": "Too tired after morning activities"
  }'
```

**Expected Response (200):**
```json
{
  "status": "refinement_applied",
  "refinement_type": "remove",
  "session_id": "test_user_001_goa_couple_3d_20240115_abc123_0",
  "message": "✅ Activity removed: Parasailing at Baga Beach",
  "refinement_details": {
    "day": 2,
    "time_slot": "afternoon",
    "activity": "Parasailing at Baga Beach",
    "cost_removed": 2500,
    "reason": "Too tired after morning activities"
  },
  "updated_total_cost": 22000,
  "refinements_count": 2,
  "time_freed_up": "1 hour",
  "suggestion": "💡 This frees up 1 hour in afternoon. Would you like to add relaxation time or another activity?"
}
```

---

### Step 4C: Apply Refinement - SWAP Activity

```bash
curl -X POST http://localhost:8000/api/review/test_user_001_goa_couple_3d_20240115_abc123_0/refine \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "itinerary_id": "goa_couple_3d_20240115_abc123",
    "request_type": "swap",
    "day": 3,
    "time_slot": "evening",
    "details": {
      "target_day": 2,
      "target_time_slot": "evening",
      "place_name": "Cafe Tato - Night Music & Dinner"
    },
    "reason": "Want nightlife on Day 2 instead"
  }'
```

**Expected Response (200):**
```json
{
  "status": "refinement_applied",
  "refinement_type": "swap",
  "session_id": "test_user_001_goa_couple_3d_20240115_abc123_0",
  "message": "✅ Activity swapped successfully",
  "refinement_details": {
    "old": {
      "day": 3,
      "time_slot": "evening",
      "activity": "Cafe Tato - Night Music & Dinner"
    },
    "new": {
      "day": 2,
      "time_slot": "evening",
      "activity": "Cafe Tato - Night Music & Dinner"
    }
  },
  "travel_time_impact": "Reduced by 15 minutes",
  "refinements_count": 3
}
```

---

### Step 5: Preview Final Itinerary

```bash
curl -X GET "http://localhost:8000/api/review/test_user_001_goa_couple_3d_20240115_abc123_0/preview"
```

**Expected Response (200):**
```json
{
  "session_id": "test_user_001_goa_couple_3d_20240115_abc123_0",
  "original_cost": 24500,
  "updated_cost": 22000,
  "cost_change": "₹-2,500 ✅",
  "cost_change_percentage": -10.2,
  "within_budget": true,
  "budget_utilization": 73.3,
  "changes_made": {
    "refinements_count": 3,
    "refinement_types": {
      "replace": 1,
      "remove": 1,
      "swap": 1
    }
  },
  "final_summary": {
    "destination": "Goa",
    "duration": "3 days 2 nights",
    "daily_highlights": [
      {
        "day": 1,
        "theme": "Beach & Relaxation",
        "activities_count": 3,
        "highlights": [
          "Anjuna Beach (replaced from Calangute)",
          "Seafood Lunch at Fisherman's Wharf",
          "Evening food tour at Panjim market"
        ],
        "estimated_cost": 2200,
        "travel_time": "2.5 hours between activities"
      },
      {
        "day": 2,
        "theme": "Water Sports & Nightlife",
        "activities_count": 2,
        "highlights": [
          "Jet Ski at Baga Beach",
          "Cafe Tato - Night Music & Dinner (moved from Day 3)"
        ],
        "estimated_cost": 3700,
        "travel_time": "1.5 hours between activities"
      },
      {
        "day": 3,
        "theme": "Relaxation & Departure",
        "activities_count": 2,
        "highlights": [
          "Yoga at beach",
          "Departure"
        ],
        "estimated_cost": 800,
        "travel_time": "0.5 hours"
      }
    ],
    "ready_to_finalize": true,
    "feedback": "✨ Your itinerary looks great! Ready to approve & book?"
  },
  "cost_breakdown": {
    "accommodation": 0,
    "food": 8500,
    "activities": 11000,
    "transport": 2500
  },
  "confidence_score": 0.94
}
```

---

### Step 6: Approve & Finalize Itinerary

```bash
curl -X POST http://localhost:8000/api/review/test_user_001_goa_couple_3d_20240115_abc123_0/approve \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "itinerary_id": "goa_couple_3d_20240115_abc123",
    "approved": true,
    "final_itinerary": {
      "destination": "Goa",
      "num_days": 3,
      "budget": 30000,
      "daily_plans": [...]
    }
  }'
```

**Expected Response (200):**
```json
{
  "status": "approved",
  "message": "✨ Itinerary approved and saved!",
  "itinerary_id": "goa_couple_3d_20240115_abc123",
  "user_id": "test_user_001",
  "approval_timestamp": "2024-01-15T14:30:00Z",
  "refinements_applied": [
    {
      "type": "replace",
      "day": 1,
      "time_slot": "morning",
      "from": "Calangute Beach",
      "to": "Anjuna Beach"
    },
    {
      "type": "remove",
      "day": 2,
      "time_slot": "afternoon",
      "activity": "Parasailing at Baga Beach"
    },
    {
      "type": "swap",
      "activity": "Cafe Tato - Night Music & Dinner",
      "from": "Day 3 evening",
      "to": "Day 2 evening"
    }
  ],
  "final_details": {
    "destination": "Goa",
    "duration": "3 days 2 nights",
    "total_cost": 22000,
    "budget_remaining": 8000,
    "activities_count": 7
  },
  "action_items": [
    "📱 Share itinerary with travel companions (link: goa_3d_2024_sharelink_abc123)",
    "🎫 Book Parasailing in advance (if adding on Day 3)",
    "🏨 Confirm hotel reservations for all 2 nights",
    "🚗 Reserve car for Day 2 transport",
    "📍 Download offline map of Goa"
  ],
  "saved_location": "user_profiles/test_user_001/trips/goa_couple_3d_20240115_abc123.json"
}
```

---

### Step 7: Submit Post-Trip Feedback

*[After user completes the trip]*

```bash
curl -X POST http://localhost:8000/api/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "itinerary_id": "goa_couple_3d_20240115_abc123",
    "overall_satisfaction": 5,
    "timing_fit": 5,
    "cost_accuracy": 4,
    "place_variety": 5,
    "comments": "Amazing trip! Everything went smoothly. The personalized recommendations were spot-on.",
    "what_went_well": [
      "Perfect balance between activities and relaxation",
      "Cost estimates were very accurate (actual: ₹21,800)",
      "Great mix of beaches and food experiences",
      "Timing was perfect - not rushed at all"
    ],
    "what_could_improve": [
      "Could have included one more cultural site",
      "Beach safety information would be helpful"
    ],
    "would_revisit": true,
    "would_use_planner_again": true,
    "actual_expenses": {
      "accommodation": 0,
      "food": 8200,
      "activities": 10800,
      "transport": 2800
    }
  }'
```

**Expected Response (200):**
```json
{
  "status": "feedback_saved",
  "message": "🙏 Thank you for your feedback!",
  "feedback_id": "feedback_goa_couple_3d_20240115_abc123",
  "user_id": "test_user_001",
  "itinerary_id": "goa_couple_3d_20240115_abc123",
  "accuracy_metrics": {
    "cost_accuracy": 99.1,
    "feedback": "Excellent! Our cost estimates were 99% accurate"
  },
  "insights": {
    "trips_completed": 1,
    "average_overall_satisfaction": 5.0,
    "average_cost_accuracy": 4.0,
    "average_timing_fit": 5.0,
    "behavioral_insights": [
      "✨ Very satisfied traveler - consistently positive feedback",
      "💰 Budget-conscious - actual spending within 0.9% of estimate",
      "⏰ Prefers relaxed pace - high satisfaction with timing",
      "🎯 Trusts recommendations - minimal refinements, highly satisfied"
    ]
  },
  "recommendations_for_next_trip": [
    "🎯 Include cultural sites (user noted this)",
    "📚 Provide safety information alongside beach activities",
    "⏰ Continue moderate travel pace - works well for this user",
    "🍜 They love food experiences - suggest more culinary activities"
  ],
  "profile_updates": {
    "interest_boost": ["beaches", "food"],
    "travel_pace": "moderate",
    "budget_preference": "conservative",
    "revisit_likelihood": "very_high"
  },
  "next_trip_suggestions": {
    "recommended_duration": "4-5 days",
    "recommended_budget": 35000,
    "destinations_to_suggest": [
      "Kerala (backwaters + beaches + food)",
      "Rajasthan (cultural + architecture)",
      "Tamil Nadu (beaches + temples + culture)"
    ]
  }
}
```

---

### Step 8: Get User History & Analytics

```bash
curl -X GET "http://localhost:8000/api/user/test_user_001/history"
```

**Expected Response (200):**
```json
{
  "user_id": "test_user_001",
  "total_trips_planned": 1,
  "trips_completed": 1,
  "overall_satisfaction": 5.0,
  "profile_summary": {
    "travel_interests": ["beaches", "food", "nightlife"],
    "preferred_duration": "3-5 days",
    "preferred_budget_range": "20000-40000",
    "travel_pace": "moderate",
    "travel_companion_type": "couple"
  },
  "trip_history": [
    {
      "trip_id": "goa_couple_3d_20240115_abc123",
      "destination": "Goa",
      "dates": "2024-01-20 to 2024-01-22",
      "duration": 3,
      "budget": 30000,
      "actual_cost": 21800,
      "satisfaction": 5,
      "status": "completed"
    }
  ],
  "behavioral_insights": [
    "✨ Very satisfied traveler (5/5 rating)",
    "💰 Budget-conscious planner - spends 73% of budget",
    "⏰ Prefers moderate pace - avoids rushing",
    "🤖 Trusts AI recommendations - made minimal refinements"
  ],
  "learning_outcomes": {
    "preferred_interests": ["beaches", "food"],
    "interests_to_explore": ["cultural_sites", "safety_information"],
    "travel_style": "relaxed",
    "refinement_pattern": "minimal_changes",
    "satisfaction_drivers": [
      "Accurate cost estimation",
      "Comfortable pace",
      "Diverse activities"
    ]
  },
  "next_trip_readiness": {
    "ready_for_next_trip": true,
    "personalization_confidence": "high",
    "recommendations": [
      "Try 4-5 day trips (user likely to be more satisfied)",
      "Include cultural/historical sites (noted as improvement item)",
      "Add more food experiences (shown interest)",
      "Beach destinations likely to please (high satisfaction)"
    ]
  }
}
```

---

## Success Criteria Checklist

After completing all 8 steps, verify:

- ✅ Step 1: Itinerary generated with optimization data
- ✅ Step 2: Review session created with review points and alternatives
- ✅ Step 3: Activity details retrieved with reasoning and alternatives
- ✅ Step 4A: Replace refinement applied successfully
- ✅ Step 4B: Remove refinement applied successfully  
- ✅ Step 4C: Swap refinement applied successfully
- ✅ Step 5: Final preview shows cost changes and impact
- ✅ Step 6: Itinerary approved and saved with action items
- ✅ Step 7: Feedback submitted and insights generated
- ✅ Step 8: User history updated with learning outcomes

## Error Scenarios

### Invalid Session ID
```bash
curl -X GET "http://localhost:8000/api/review/invalid_session/details?day=1&time_slot=morning"
# Expected: 404 Not Found
# Response: {"detail": "Review session not found"}
```

### Refinement on Invalid Day
```bash
curl -X POST http://localhost:8000/api/review/session_id/refine \
  -H "Content-Type: application/json" \
  -d '{"day": 10, "time_slot": "morning", ...}'
# Expected: 400 Bad Request
# Response: {"detail": "Day 10 exceeds trip duration (3 days)"}
```

### Cost Exceeds Budget
```
If refinement would exceed budget:
# Expected: 400 Bad Request
# Response: {"detail": "Refinement would exceed budget by ₹2500. Budget buffer: ₹5500"}
```

---

## Performance Testing

```bash
# Test review session startup time
time curl -X POST http://localhost:8000/api/review/start \
  -H "Content-Type: application/json" \
  -d '{...}'

# Expected: < 500ms for session creation
```

---

## Automated Test Run

```bash
# Run the test suite
cd /Users/pandhari/Desktop/PlanMyTrip/backend
python test_human_in_loop_workflow.py
```

This will automatically execute all steps and verify responses.

