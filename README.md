# PlanMyTrip — AI-Based Personalized Travel Planner

## Project Structure

```
PlanMyTrip/
├── backend/
│   ├── main.py          # FastAPI app + all endpoints
│   ├── agent.py         # LangGraph 5-agent pipeline
│   ├── chat.py          # Conversational replanning agent
│   ├── tools.py         # Weather + Google Places API
│   ├── memory.py        # FAISS vector DB memory
│   ├── pdf_export.py    # ReportLab PDF generator
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── TripForm.jsx        # Input form
│   │       ├── ItineraryView.jsx   # Results display
│   │       ├── MapView.jsx         # Google Maps embed
│   │       ├── PastTrips.jsx       # Saved trips sidebar
│   │       └── ChatInterface.jsx   # Floating chat bubble
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Agent Pipeline

```
User Input
    ↓
[WeatherAgent]     → OpenWeatherMap API
    ↓
[PlacesAgent]      → Google Places API (scored by interests)
    ↓
[PlannerAgent]     → LLaMA3-70B generates day-wise plan
    ↓
[ConstraintAgent]  → Validates budget, fixes costs
    ↓
[ExplanationAgent] → Adds tips, packing list, weather note
    ↓
Final Itinerary + Map + Chat
```

---

## Setup (Local Dev)

### Prerequisites
- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (pip install uv)

### 1. Backend
```bash
cd backend

# Install dependencies using uv
uv sync

# Copy and configure environment
cp .env.example .env
# Fill in .env with your API keys:
#   GROQ_API_KEY=...
#   GOOGLE_MAPS_API_KEY=...
#   OPENWEATHER_API_KEY=...

# Run the server (uv automatically uses .venv)
.venv/bin/uvicorn main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend

# Copy and configure environment
cp .env.example .env
# Fill in .env:
#   VITE_GOOGLE_MAPS_KEY=...

# Install and run
npm install
npm run dev
# → http://localhost:5173
```

### Running Both Simultaneously
**Terminal 1 (Backend):**
```bash
cd backend
.venv/bin/uvicorn main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

---

## Setup (Docker)

```bash
# Root level — copy and fill both env files
cp backend/.env.example backend/.env
cp .env.example .env

# Build and run
docker-compose up --build

# → http://localhost:3000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/plan | Generate itinerary (5 agents) |
| POST | /api/chat | Conversational replanning |
| POST | /api/trips/save | Save to FAISS memory |
| GET  | /api/trips/{user_id} | List saved trips |
| GET  | /api/trips/load/{trip_id} | Load a trip |
| POST | /api/export/pdf | Download PDF |

Swagger UI: http://localhost:8000/docs

---

## Team

| Name | Roll No | PRN |
|---|---|---|
| Pranav Dhebe | 382001 | 22310012 |
| Pandharinath Maske | 382011 | 22310246 |
| Shubham Dahane | 382015 | 22310312 |
| Aayush Bokde | 382016 | 22310316 |
