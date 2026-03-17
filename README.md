# 🌍 PlanMyTrip - AI-Powered Itinerary Planning with Human-in-the-Loop

**The smart travel planner that works WITH you, not FOR you.**

## 📋 What's New: Human-in-the-Loop System ✨

We've added an interactive review workflow that lets users:
- ✅ **Understand** why AI recommends activities (explainable decisions)
- ✅ **Explore** alternatives for each activity
- ✅ **Refine** their itinerary with one-click adjustments
- ✅ **Approve** before committing to any plan
- ✅ **Learn** from feedback for better future recommendations

**Result:** Better user experience, higher satisfaction, more trustworthy AI.

---

## 🚀 Quick Start (15 minutes)

### Choose Your Path:

**[→ I'm new, get me running!](./DEVELOPER_QUICK_START.md)** (15 min)
- Start backend & frontend
- Run test suite
- See the system working

**[→ I'm a frontend developer](./FRONTEND_INTEGRATION_GUIDE.md)** (20 min)
- 7 React components with full code
- CSS styling files
- Integration steps

**[→ I'm a backend developer](./QUICK_REFERENCE.md)** (5 min)
- API endpoints & examples
- Testing procedures
- Error handling

**[→ I work on product/UX](./HUMAN_IN_LOOP_GUIDE.md)** (10 min)
- Complete user flow
- Benefits & metrics
- Real-world scenarios

**[→ I'm a tech lead](./IMPLEMENTATION_SUMMARY.md)** (15 min)
- System architecture
- Feature list
- Timeline & next steps

---

## 📁 Project Structure

```
PlanMyTrip/
├── backend/
│   ├── main.py                      # FastAPI endpoints
│   ├── agent.py                     # 6-agent LangGraph pipeline
│   ├── human_in_loop.py             # Review engine (NEW)
│   ├── interactive_refinement.py    # Session management (NEW)
│   ├── scoring.py                   # 4-factor scoring model
│   ├── route_optimizer.py           # K-Means + TSP optimization
│   ├── constraints.py               # Budget/time validation
│   ├── user_preferences.py          # Profile learning
│   ├── optimization_agent.py        # Orchestration
│   ├── test_*.py                    # Test suites
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── ChatInterface.jsx    # Main conversation
│   │       ├── TripForm.jsx         # Input form
│   │       ├── ItineraryView.jsx    # Results view
│   │       ├── ReviewInterface.jsx  # (To be created)
│   │       ├── ActivityCard.jsx     # (To be created)
│   │       ├── FeedbackForm.jsx     # (To be created)
│   │       └── ...more components
│   ├── index.html
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── Documentation/
│   ├── DEVELOPER_QUICK_START.md         # Start here (15 min)
│   ├── HUMAN_IN_LOOP_GUIDE.md          # User flow guide
│   ├── QUICK_REFERENCE.md              # API quick lookup
│   ├── HITL_TESTING_GUIDE.md           # Testing procedures
│   ├── FRONTEND_INTEGRATION_GUIDE.md   # React components
│   └── IMPLEMENTATION_SUMMARY.md       # System overview
├── docker-compose.yml
├── .gitignore
└── README.md (this file)
```

---

## 🎯 The HITL Workflow (5 Phases)

```
Phase 1: Generate          Phase 2: Review           Phase 3: Refine
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ User provides:   │  →  │ AI shows each    │  →  │ User can:        │
│ • Destination    │     │ activity with:   │     │ • Replace        │
│ • Dates          │     │ • Score (87%)    │     │ • Remove         │
│ • Budget         │     │ • Why selected   │     │ • Move time      │
│ • Interests      │     │ • Alternatives   │     │ • Keep as-is     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                 ↓ (1 click)            ↓
                         Phase 4: Approve     Phase 5: Learn & Improve
                         ┌──────────────────┐ ┌──────────────────┐
                         │ Preview shows:   │ │ After trip:      │
                         │ • Cost changes   │ │ • Collect        │
                         │ • Highlights     │ │   feedback       │
                         │ • Confirm save   │ │ • Update profile │
                         └──────────────────┘ │ • Next trip      │
                                              │   better! 📈     │
                                              └──────────────────┘
```

---

## 🔌 New API Endpoints (7 Total)

### Review Management
```
POST   /api/review/start                 ← Initialize review session
GET    /api/review/{id}/details          ← Get activity + alternatives
POST   /api/review/{id}/refine           ← Apply refinement
GET    /api/review/{id}/preview          ← Final preview
POST   /api/review/{id}/approve          ← Approve & save
```

### Feedback & Learning
```
POST   /api/feedback/submit              ← Submit post-trip feedback
GET    /api/user/{id}/history            ← Get user analytics
```

See **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** for full details.

---

## ✨ System Capabilities

✅ **6-Agent AI Pipeline** (LangGraph)
- Generates complete itineraries in 8-10 seconds
- NLP → Places → Scoring → Optimization → Constraints → Planning

✅ **Intelligent Optimization**
- K-Means++ clustering for geographic grouping
- TSP 2-Opt algorithm for route efficiency
- Haversine distance for accurate travel times

✅ **Preference Scoring** (4-Factor Model)
- 35% Relevance to user interests
- 30% Popularity (ratings & reviews)
- 20% Distance (proximity)
- 15% Opening hours (availability)

✅ **Constraint Validation**
- Time feasibility (realistic daily schedules)
- Budget allocation (smart cost distribution)
- Operating hours (verified activity availability)

✅ **Human-in-Loop Workflow**
- Explainable decisions (reasoning for each pick)
- Alternative suggestions (3-8 per activity)
- Flexible refinements (replace/remove/move)
- Real-time cost updates

✅ **Continuous Learning**
- Post-trip feedback collection
- User profile updates
- Preference learning over time
- Next trip automatically better

---

## 📊 Implementation Status

### ✅ Backend (100% Complete)
- [x] 6-agent LangGraph pipeline
- [x] Scoring system (4-factor model)
- [x] Route optimization (K-Means + TSP)
- [x] Constraint validation
- [x] User profile learning
- [x] Human-in-loop engine
- [x] Interactive refinement API
- [x] Feedback collection
- [x] All endpoints tested ✅

### 🔄 Frontend (Ready for Implementation)
- [x] Chat interface (existing)
- [ ] Review interface ← Build from [guide](./FRONTEND_INTEGRATION_GUIDE.md)
- [ ] Activity cards ← Build from guide
- [ ] Alternatives panel ← Build from guide
- [ ] Feedback form ← Build from guide
- [ ] Integration with backend

### 📚 Documentation (100% Complete)
- [x] User flow guide
- [x] API testing guide
- [x] Frontend integration guide (with code)
- [x] System overview
- [x] Developer quick start
- [x] Quick reference

---

## ⚡ Quick Start Commands

### 1. Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
# ✅ http://localhost:8000
# 📖 http://localhost:8000/docs (API docs)
```

### 2. Frontend
```bash
cd frontend
npm install && npm run dev
# ✅ http://localhost:5173
```

### 3. Run Tests
```bash
cd backend
python test_human_in_loop_workflow.py
# ✅ All 8 tests passing
```

---

## 📖 Documentation Quick Links

| Document | Purpose | Audience | Time |
|----------|---------|----------|------|
| **[DEVELOPER_QUICK_START.md](./DEVELOPER_QUICK_START.md)** | Get running in 15 min | Everyone | 15 min |
| **[HUMAN_IN_LOOP_GUIDE.md](./backend/HUMAN_IN_LOOP_GUIDE.md)** | Complete user flow | Product, UX, QA | 10 min |
| **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** | API quick lookup | Backend devs | 5 min |
| **[HITL_TESTING_GUIDE.md](./backend/HITL_TESTING_GUIDE.md)** | End-to-end testing | QA, Backend | 15 min |
| **[FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md)** | Build React UI | Frontend devs | 20 min |
| **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** | System overview | Tech leads | 15 min |

---

## 🎓 Learning Paths by Role

### Frontend Developer
1. Read [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md) (20 min)
2. Copy 7 components + CSS
3. Connect to backend API
4. Test complete flow

### Backend Developer
1. Read [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) (5 min)
2. Review `human_in_loop.py` & `interactive_refinement.py`
3. Test using [HITL_TESTING_GUIDE.md](./backend/HITL_TESTING_GUIDE.md)
4. Verify all endpoints working

### QA/Tester
1. Read [HUMAN_IN_LOOP_GUIDE.md](./backend/HUMAN_IN_LOOP_GUIDE.md) (10 min)
2. Follow [HITL_TESTING_GUIDE.md](./backend/HITL_TESTING_GUIDE.md)
3. Test all scenarios
4. Verify performance metrics

### Project Manager
1. Read [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) (15 min)
2. Check implementation checklist
3. Plan frontend phase
4. Track team progress

---

## 📊 Success Metrics

### User Satisfaction Target
- Overall rating: 4.5+/5 ⭐
- Cost accuracy: 95%+
- Timing fit: 90%+

### System Performance Target
- Itinerary generation: <10 seconds ✅
- API response time: <1 second
- Refinement application: <200ms

### Business Target
- User retention: 80%+
- Repeat bookings: 70%+
- NPS score: 50+

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PlanMyTrip System                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Frontend (React)        ←→     Backend (FastAPI)       │
│  • Chat Interface              • 6-Agent Pipeline       │
│  • Review Interface            • Scoring (4-factor)     │
│  • Feedback Form               • Optimization (K-Means) │
│  • Analytics                   • Constraints            │
│                                • Human-in-Loop Engine   │
│  Port 5173                     Port 8000               │
└─────────────────────────────────────────────────────────┘
             ↓
    ┌──────────────────┐
    │  Data Storage    │
    ├──────────────────┤
    │ • User profiles  │
    │ • Trips saved    │
    │ • Feedback       │
    │ • Sessions       │
    └──────────────────┘
```

---

## 🔍 Key Files

### Backend Core
- `main.py` - API endpoints
- `human_in_loop.py` - Review engine (450 lines)
- `interactive_refinement.py` - Session management (400 lines)
- `agent.py` - 6-agent pipeline (modified)

### Optimization Engines
- `scoring.py` - 4-factor preference model
- `route_optimizer.py` - K-Means + TSP
- `constraints.py` - Budget/time validation
- `user_preferences.py` - Profile learning

### Tests
- `test_human_in_loop_workflow.py` - Full workflow (8 tests)

---

## ❓ Common Questions

**Q: How long to generate itinerary?**
A: 8-10 seconds for complete 6-agent pipeline.

**Q: Can users skip review?**
A: Yes - approve without refinements (~30 seconds).

**Q: How many alternatives shown?**
A: 3-8 per activity, ranked by relevance score.

**Q: What if exceeds budget?**
A: Warning shown, but user can still approve. Difference tracked for learning.

**Q: How does system improve?**
A: Post-trip feedback updates user profile. Next trip uses learned preferences.

**Q: Is this scalable?**
A: Yes - optimized for 100+ activities with efficient algorithms.

---

## 🆘 Troubleshooting

### Backend won't start?
→ Check port 8000 not in use: `lsof -i :8000`

### API not responding?
→ Check running: `curl http://localhost:8000`

### Tests failing?
→ Make sure backend running: `python -m uvicorn main:app --reload --port 8000`

### Frontend won't connect?
→ Check backend CORS: Should allow `localhost:5173`

---

## 🚀 Next Steps (In Priority Order)

### Week 1: Frontend Implementation
- [ ] Read [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md)
- [ ] Create 7 React components
- [ ] Connect to backend
- [ ] Test complete flow

### Week 2: End-to-End Testing
- [ ] Run all test scenarios
- [ ] Verify cost calculations
- [ ] Test feedback system
- [ ] Performance benchmarks

### Week 3: Deployment Prep
- [ ] Docker setup
- [ ] Database finalization
- [ ] Environment config
- [ ] API documentation

### Week 4: Launch
- [ ] Deploy to staging
- [ ] User testing
- [ ] Production deployment
- [ ] Monitor & optimize

---

## 📞 Support

For questions about:
- **Getting started** → [DEVELOPER_QUICK_START.md](./DEVELOPER_QUICK_START.md)
- **User experience** → [HUMAN_IN_LOOP_GUIDE.md](./backend/HUMAN_IN_LOOP_GUIDE.md)
- **API details** → [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- **Frontend code** → [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md)
- **Testing** → [HITL_TESTING_GUIDE.md](./backend/HITL_TESTING_GUIDE.md)
- **System design** → [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

---

## 👥 Team

| Name | Roll No | Role |
|------|---------|------|
| Pranav Dhebe | 382001 | Backend Lead |
| Pandharinath Maske | 382011 | Full Stack |
| Shubham Dahane | 382015 | QA/Testing |
| Aayush Bokde | 382016 | Frontend |

---

## 📈 Project Status

```
Backend Implementation ..................... ✅ Complete (100%)
Human-in-Loop System ....................... ✅ Complete (100%)
Documentation ............................. ✅ Complete (100%)
Frontend Integration ....................... 🔄 Pending
End-to-End Testing ......................... ⏳ Pending
Deployment ................................ ⏳ Pending
```

---

## 🎉 Ready to Code?

**Start here:** [DEVELOPER_QUICK_START.md](./DEVELOPER_QUICK_START.md)

Everything you need is documented and ready to use. Pick your role from the Learning Paths above and dive in!

**Happy coding! ✨**

---

**Last Updated:** January 2024  
**Version:** 1.0 (Complete)  
**Status:** ✅ Backend Ready | 🔄 Frontend Pending
