# PlanMyTrip: Developer Quick Start

**Time to first working demo: 15 minutes**

---

## Step 1: Start Backend (2 min)

```bash
cd /Users/pandhari/Desktop/PlanMyTrip/backend

# Check Python version (need 3.8+)
python --version

# Install/update dependencies (if needed)
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

✅ Backend ready at: http://localhost:8000

---

## Step 2: Test Single Endpoint (3 min)

In a new terminal, test the HITL endpoints:

```bash
# Test 1: Check API is running
curl http://localhost:8000/

# Test 2: Generate a sample itinerary
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "num_days": 3,
    "budget": 30000,
    "travel_type": "couple",
    "interests": ["beaches", "food"],
    "trip_name": "Test Trip"
  }'
```

**Expected:** 200 OK with `itinerary_id`

✅ API responding correctly

---

## Step 3: Run Full Test Suite (5 min)

```bash
cd /Users/pandhari/Desktop/PlanMyTrip/backend

# Run automated test
python test_human_in_loop_workflow.py
```

Expected output:
```
✅ Test 1: Generate Itinerary... PASS
✅ Test 2: Start Review Session... PASS
✅ Test 3: Get Activity Details... PASS
✅ Test 4: Apply Refinement... PASS
✅ Test 5: Preview Itinerary... PASS
✅ Test 6: Approve Itinerary... PASS
✅ Test 7: Submit Feedback... PASS
✅ Test 8: Get User History... PASS

All tests passed! ✨
```

✅ All core functionality working

---

## Step 4: Start Frontend (3 min)

In a new terminal:

```bash
cd /Users/pandhari/Desktop/PlanMyTrip/frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Expected output:**
```
  VITE v4.4.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

✅ Frontend running at: http://localhost:5173

---

## Step 5: View Interactive Docs (2 min)

In browser, open:
- **http://localhost:8000/docs** (SwaggerUI - interactive API docs)
- **http://localhost:8000/redoc** (ReDoc - alternate API docs)

You can test all endpoints directly in the browser!

---

## 🎯 Now Try the Complete Flow

### 1. Open Frontend
```
Open http://localhost:5173 in browser
```

### 2. Generate Trip
```
- Enter destination, dates, budget
- Click "Plan Trip"
- Wait ~10 seconds
```

### 3. Review (NEW!)
```
- Click "Review & Refine"
- See activities with scores
- Click on alternatives
- Make changes (replace/remove/swap)
```

### 4. Approve
```
- Click "Preview & Approve"
- See cost changes
- Click "Approve & Book"
```

### 5. Feedback (After trip)
```
- Click "Submit Feedback"
- Rate experience
- Add comments
- Submit
```

---

## 📁 Key Files to Know

### Backend
- `main.py` - API endpoints (look for `/api/review/` and `/api/feedback/`)
- `human_in_loop.py` - Review/feedback engine (450 lines)
- `interactive_refinement.py` - Session management (400 lines)
- `test_human_in_loop_workflow.py` - Test suite

### Frontend  
- `src/components/ChatInterface.jsx` - Main interface
- `src/components/ReviewInterface.jsx` - (To be created) Review UI
- `src/components/FeedbackForm.jsx` - (To be created) Feedback UI
- See FRONTEND_INTEGRATION_GUIDE.md for component code

---

## 🔍 Debugging Tips

### Backend not responding?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill if needed
kill -9 <PID>

# Restart
python -m uvicorn main:app --reload --port 8000
```

### Test a specific endpoint?
```bash
# Replace ENDPOINT with actual endpoint
curl http://localhost:8000/ENDPOINT

# E.g., test health check
curl http://localhost:8000/
```

### Check database?
```bash
# View saved user profiles
ls /Users/pandhari/Desktop/PlanMyTrip/backend/user_profiles/

# View saved feedback
ls /Users/pandhari/Desktop/PlanMyTrip/backend/hitl_data/feedback/
```

### View API documentation?
```bash
# Open in browser
http://localhost:8000/docs

# All endpoints listed with examples!
```

---

## 📊 What's Actually Running?

### Backend (8000)
```
FastAPI server with:
├── 6-agent pipeline (LangGraph)
├── Optimization engines
├── Human-in-loop system
└── 7 new HITL endpoints
```

### Frontend (5173)
```
React + Vite with:
├── Chat interface
├── Itinerary display
├── (NEW) Review interface
├── (NEW) Feedback form
└── (NEW) User analytics
```

### Data Storage
```
/backend/
├── user_profiles/          # Saved user preferences
├── hitl_data/
│   ├── sessions/          # Active review sessions
│   └── feedback/          # Post-trip feedback
└── memory_store/          # Agent memory
```

---

## ⚡ Common Tasks

### I want to see the test data
```bash
ls /Users/pandhari/Desktop/PlanMyTrip/backend/user_profiles/
cat /Users/pandhari/Desktop/PlanMyTrip/backend/user_profiles/test_user_001.json
```

### I want to inspect the API calls
```bash
# Browser dev tools → Network tab
# Or use curl with -v flag for verbose
curl -v http://localhost:8000/api/plan ...
```

### I want to reset all data
```bash
# Remove saved profiles and feedback
rm -rf /Users/pandhari/Desktop/PlanMyTrip/backend/user_profiles/*
rm -rf /Users/pandhari/Desktop/PlanMyTrip/backend/hitl_data/feedback/*
```

### I want to see logs
```bash
# Backend logs appear in terminal where you ran uvicorn
# Frontend logs appear in browser console (F12)
```

---

## 🚀 Next Steps

### For Backend Developers
1. ✅ Verify backend tests pass
2. Review `human_in_loop.py` (how reviews work)
3. Review `interactive_refinement.py` (how sessions work)
4. Inspect `main.py` (how endpoints called)
5. Optimize performance if needed

### For Frontend Developers
1. ✅ Verify frontend starts
2. Read FRONTEND_INTEGRATION_GUIDE.md
3. Copy 7 React components from guide
4. Update ChatInterface to call new endpoints
5. Test complete flow

### For QA/Testing
1. ✅ Run test suite (all tests pass)
2. Follow HITL_TESTING_GUIDE.md
3. Test with real user data
4. Check error scenarios
5. Verify performance metrics

---

## 📞 Quick Help

### Backend won't start?
```bash
# Error: Port already in use
# Solution: Use different port
python -m uvicorn main:app --reload --port 8001

# Error: Module not found
# Solution: Install dependencies
pip install -r requirements.txt

# Error: Python version too old
# Solution: Use Python 3.8+
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start?
```bash
# Error: npm command not found
# Solution: Install Node.js from nodejs.org

# Error: Port already in use
# Solution: Use different port
npm run dev -- --port 5174

# Error: Dependencies not installed
# Solution:
npm install
npm run dev
```

### Tests not passing?
```bash
# Make sure backend is running
python -m uvicorn main:app --reload --port 8000

# Then run tests in separate terminal
cd /Users/pandhari/Desktop/PlanMyTrip/backend
python test_human_in_loop_workflow.py

# If failing, check backend logs for errors
```

---

## 📚 Documentation Roadmap

```
START HERE
    ↓
1. This file (first 5 minutes)
    ↓
2. QUICK_REFERENCE.md (API details)
    ↓
3. HUMAN_IN_LOOP_GUIDE.md (user flow)
    ↓
4. FRONTEND_INTEGRATION_GUIDE.md (React code)
    ↓
5. HITL_TESTING_GUIDE.md (detailed testing)
    ↓
DEEP DIVE
    ↓
6. Source code in modules:
   - main.py
   - human_in_loop.py
   - interactive_refinement.py
```

---

## ✨ Success Criteria

After 15 minutes, you should have:

- ✅ Backend running locally (port 8000)
- ✅ Frontend running locally (port 5173)  
- ✅ All 8 tests passing
- ✅ API interactive docs accessible
- ✅ Can generate sample itinerary
- ✅ Can start review session
- ✅ Understand the complete flow

---

## 🎓 Learning Path

### Day 1: Setup & Basics
- [ ] Get backend + frontend running
- [ ] Run full test suite  
- [ ] Read HUMAN_IN_LOOP_GUIDE.md
- [ ] Try example curl commands

### Day 2: Implementation Details
- [ ] Review human_in_loop.py code
- [ ] Review interactive_refinement.py code
- [ ] Review main.py endpoints
- [ ] Understand data flow

### Day 3: Frontend Integration
- [ ] Read FRONTEND_INTEGRATION_GUIDE.md
- [ ] Create 7 React components
- [ ] Connect to backend endpoints
- [ ] Test UI flow

### Day 4: Testing & QA
- [ ] Follow HITL_TESTING_GUIDE.md
- [ ] Test all scenarios
- [ ] Performance testing
- [ ] Error handling

---

## 🔗 Useful Links

| Location | Purpose |
|----------|---------|
| http://localhost:8000 | Backend API root |
| http://localhost:8000/docs | Interactive API docs |
| http://localhost:5173 | Frontend app |
| /backend/main.py | API code |
| /backend/human_in_loop.py | HITL engine |
| /backend/interactive_refinement.py | Session manager |

---

## 🎯 One-Command Test

Want to verify everything in one go?

```bash
# Run this in backend directory
python -c "
import requests
print('🧪 Testing PlanMyTrip HITL System...')

# Test 1: Server running
resp = requests.get('http://localhost:8000')
assert resp.status_code == 200, 'Server not responding'
print('✅ Backend running')

# Test 2: Generate itinerary
resp = requests.post('http://localhost:8000/api/plan', json={
    'destination': 'Goa',
    'num_days': 3,
    'budget': 30000,
    'travel_type': 'couple',
    'interests': ['beaches', 'food'],
    'trip_name': 'Test'
})
assert resp.status_code == 200, 'Plan failed'
itinerary_id = resp.json()['itinerary_id']
print(f'✅ Itinerary generated: {itinerary_id}')

# Test 3: Start review
resp = requests.post('http://localhost:8000/api/review/start', json={
    'user_id': 'test_user',
    'itinerary_id': itinerary_id,
    'itinerary': resp.json(),
    'optimization_data': {}
})
assert resp.status_code == 200, 'Review start failed'
session_id = resp.json()['session_id']
print(f'✅ Review session started: {session_id}')

print('\\n🎉 All systems operational!')
"
```

---

## 📌 Remember

- **Backend runs on 8000** → http://localhost:8000
- **Frontend runs on 5173** → http://localhost:5173
- **All APIs documented** → http://localhost:8000/docs
- **Tests are your friend** → python test_*.py
- **Read the guides!** → 5 comprehensive markdown files created
- **Check source code** → Best documentation is working code

---

## 🚀 You're Ready!

Everything you need is set up and documented. 

**Now go build something amazing! ✨**

---

**Questions?** Check QUICK_REFERENCE.md or look at the source code.  
**Stuck?** See the "Quick Help" section above.  
**Want details?** Read the comprehensive guides in the root directory.

---

**Happy coding! 🎉**

Last Updated: January 2024  
Version: 1.0

