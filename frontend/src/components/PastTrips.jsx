import React, { useEffect, useState } from 'react'

export default function PastTrips({ userId = 'default', onLoad }) {
  const [trips, setTrips] = useState([])
  const [open, setOpen]   = useState(false)

  const fetchTrips = async () => {
    try {
      const res  = await fetch(`/api/trips/${userId}`)
      const data = await res.json()
      setTrips(data.trips || [])
    } catch {}
  }

  useEffect(() => { fetchTrips() }, [userId])

  const loadTrip = async (tripId) => {
    try {
      const res  = await fetch(`/api/trips/load/${tripId}`)
      const data = await res.json()
      onLoad(data)
      setOpen(false)
    } catch {}
  }

  if (trips.length === 0) return null

  return (
    <div className="relative">
      <button
        onClick={() => { setOpen(!open); fetchTrips() }}
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-300 hover:text-white hover:border-purple-500/50 transition"
      >
        💾 Past Trips
        <span className="bg-purple-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          {trips.length}
        </span>
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-50 w-80 card p-4 shadow-2xl space-y-2">
          <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-3">Saved Trips</p>
          {trips.map(t => (
            <button key={t.id} onClick={() => loadTrip(t.id)}
              className="w-full text-left bg-white/5 hover:bg-purple-600/20 border border-white/10 hover:border-purple-500/40 rounded-xl p-3 transition">
              <p className="font-semibold text-white text-sm">{t.destination}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {t.days} days · ₹{Number(t.budget).toLocaleString()} budget · ₹{Number(t.cost).toLocaleString()} est.
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
