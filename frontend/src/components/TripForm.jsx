import React, { useState } from 'react'

const INTERESTS = [
  { id: 'food', label: '🍜 Food' },
  { id: 'culture', label: '🏛️ Culture' },
  { id: 'adventure', label: '🧗 Adventure' },
  { id: 'shopping', label: '🛍️ Shopping' },
  { id: 'history', label: '🏰 History' },
  { id: 'nature', label: '🌿 Nature' },
  { id: 'nightlife', label: '🌃 Nightlife' },
  { id: 'religious', label: '🕌 Religious' },
  { id: 'art', label: '🎨 Art' },
  { id: 'beaches', label: '🏖️ Beaches' },
  { id: 'temples', label: '🛕 Temples' },
  { id: 'trekking', label: '⛰️ Trekking' },
]

const TRAVEL_TYPES = [
  { id: 'solo', label: '🧑 Solo' },
  { id: 'couple', label: '👫 Couple' },
  { id: 'family', label: '👨‍👩‍👧 Family' },
  { id: 'group', label: '👥 Group' },
]

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    destination: '',
    days: 3,
    budget: 10000,
    interests: [],
    travel_type: 'solo',
  })

  const toggleInterest = (id) => {
    setForm(prev => ({
      ...prev,
      interests: prev.interests.includes(id)
        ? prev.interests.filter(i => i !== id)
        : [...prev.interests, id]
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.destination.trim()) return alert('Enter a destination!')
    if (form.interests.length === 0) return alert('Select at least one interest!')
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="card p-8 space-y-6">
      <div>
        <label className="block text-sm font-semibold text-purple-300 mb-2">📍 Destination</label>
        <input
          type="text"
          placeholder="e.g. Goa, Manali, Jaipur, Paris..."
          value={form.destination}
          onChange={e => setForm({ ...form, destination: e.target.value })}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold text-purple-300 mb-2">📅 Duration (days)</label>
          <input
            type="number" min="1" max="14" value={form.days}
            onChange={e => setForm({ ...form, days: parseInt(e.target.value) })}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-purple-300 mb-2">💰 Budget (₹)</label>
          <input
            type="number" min="1000" step="500" value={form.budget}
            onChange={e => setForm({ ...form, budget: parseInt(e.target.value) })}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-purple-300 mb-2">🧳 Travel Type</label>
        <div className="grid grid-cols-4 gap-2">
          {TRAVEL_TYPES.map(t => (
            <button key={t.id} type="button" onClick={() => setForm({ ...form, travel_type: t.id })}
              className={`py-2.5 rounded-xl text-sm font-medium transition border ${
                form.travel_type === t.id
                  ? 'bg-purple-600 border-purple-500 text-white'
                  : 'bg-white/5 border-white/10 text-gray-400 hover:border-purple-500/50'
              }`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-purple-300 mb-2">
          ✨ Interests <span className="text-gray-500 font-normal">(select all that apply)</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {INTERESTS.map(i => (
            <button key={i.id} type="button" onClick={() => toggleInterest(i.id)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition border ${
                form.interests.includes(i.id)
                  ? 'bg-pink-600 border-pink-500 text-white'
                  : 'bg-white/5 border-white/10 text-gray-400 hover:border-pink-500/50'
              }`}>
              {i.label}
            </button>
          ))}
        </div>
      </div>

      <button type="submit" disabled={loading} className="glow-btn w-full py-4 rounded-xl text-white font-bold text-lg">
        {loading ? (
          <span className="flex items-center justify-center gap-3">
            <span className="loading-spinner inline-block" style={{width:22,height:22,borderWidth:2}} />
            Generating your itinerary...
          </span>
        ) : '✈️ Generate My Trip Plan'}
      </button>
    </form>
  )
}
