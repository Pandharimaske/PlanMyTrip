import React, { useState } from 'react'
import TripForm from './components/TripForm'
import ItineraryView from './components/ItineraryView'
import PastTrips from './components/PastTrips'
import ChatInterface from './components/ChatInterface'

const GOOGLE_MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY || ''

export default function App() {
  const [itinerary, setItinerary] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [userId]                  = useState('default')

  const handleSubmit = async (formData) => {
    setLoading(true)
    setError(null)
    setItinerary(null)
    try {
      const res = await fetch('/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, user_id: userId }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Something went wrong')
      }
      const data = await res.json()
      setItinerary({ ...data, travel_type: formData.travel_type })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #0f0f0f 0%, #1a0a2e 50%, #0f0f0f 100%)' }}>
      <nav className="border-b border-white/5 px-6 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-sm">
          ✈️
        </div>
        <span className="font-bold text-lg gradient-text">PlanMyTrip</span>
        <span className="ml-2 text-xs text-gray-600 hidden sm:block">AI-Powered Travel Planner</span>
        <div className="ml-4 hidden md:flex gap-1">
          {['Weather','Places','Planner','Constraint','Explanation'].map(a => (
            <span key={a} className="text-xs bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded-full px-2 py-0.5">
              {a}
            </span>
          ))}
        </div>
        <div className="ml-auto">
          <PastTrips userId={userId} onLoad={(trip) => setItinerary(trip)} />
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-10">
        {!itinerary ? (
          <>
            <div className="text-center mb-8">
              <h1 className="text-4xl font-extrabold gradient-text mb-3">Plan Your Dream Trip</h1>
              <p className="text-gray-400 text-base">5 AI agents collaborate to build your personalized itinerary</p>
              <div className="flex items-center justify-center gap-1 mt-4 flex-wrap">
                {['🌤 Weather','📍 Places','📅 Planner','✅ Constraint','✨ Explanation'].map((a, i, arr) => (
                  <React.Fragment key={a}>
                    <span className="text-xs bg-white/5 border border-white/10 rounded-full px-3 py-1 text-gray-400">{a}</span>
                    {i < arr.length - 1 && <span className="text-gray-600 text-xs">→</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>
            <TripForm onSubmit={handleSubmit} loading={loading} />
            {error && (
              <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
                ⚠️ {error}
              </div>
            )}
          </>
        ) : (
          <>
            <ItineraryView
              data={itinerary}
              onReset={() => setItinerary(null)}
              googleMapsKey={GOOGLE_MAPS_KEY}
              userId={userId}
            />
            <ChatInterface
              itinerary={itinerary}
              onItineraryUpdate={(updated) => setItinerary({ ...updated, travel_type: itinerary.travel_type })}
            />
          </>
        )}
      </div>
    </div>
  )
}
