import React, { useState } from 'react'
import MapView from './MapView'

const SLOT_COLORS = {
  morning:   'from-yellow-500/10 to-orange-500/5 border-yellow-500/20',
  afternoon: 'from-blue-500/10 to-cyan-500/5 border-blue-500/20',
  evening:   'from-purple-500/10 to-pink-500/5 border-purple-500/20',
}
const SLOT_ICONS  = { morning: '🌅', afternoon: '☀️', evening: '🌆' }
const SLOT_LABELS = { morning: 'Morning', afternoon: 'Afternoon', evening: 'Evening' }

function WeatherBadge({ weather }) {
  if (!weather?.temp) return null
  return (
    <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm">
      {weather.icon && <img src={`https://openweathermap.org/img/wn/${weather.icon}.png`} alt="" className="w-8 h-8" />}
      <span className="text-gray-300">{weather.temp}°C · {weather.description}</span>
    </div>
  )
}

function SlotCard({ slot, type }) {
  return (
    <div className={`slot-card p-4 bg-gradient-to-br ${SLOT_COLORS[type]}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{SLOT_ICONS[type]}</span>
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{SLOT_LABELS[type]}</span>
        <span className="ml-auto text-xs font-semibold text-green-400">₹{slot.cost?.toLocaleString()}</span>
      </div>
      <p className="font-semibold text-white text-sm mb-1">{slot.place}</p>
      <p className="text-gray-400 text-xs mb-1">{slot.activity}</p>
      <p className="text-gray-500 text-xs">⏱ {slot.duration}</p>
    </div>
  )
}

function DayCard({ day, index }) {
  const [open, setOpen] = useState(index === 0)
  return (
    <div className="day-card overflow-hidden fade-in" style={{ animationDelay: `${index * 0.08}s` }}>
      <button className="w-full flex items-center justify-between px-6 py-4 text-left" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-sm font-bold">
            {day.day}
          </div>
          <div>
            <p className="font-semibold text-white">{day.theme}</p>
            <p className="text-xs text-gray-500">Day {day.day} · Total: ₹{day.day_total_cost?.toLocaleString()}</p>
          </div>
        </div>
        <span className="text-gray-500">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-6 pb-6 space-y-3">
          <div className="grid gap-3">
            {['morning','afternoon','evening'].map(s => day[s] && <SlotCard key={s} slot={day[s]} type={s} />)}
          </div>
          {day.tip && (
            <div className="flex gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl p-3">
              <span className="text-amber-400 text-sm">💡</span>
              <p className="text-amber-300 text-xs">{day.tip}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ItineraryView({ data, onReset, googleMapsKey, userId }) {
  const [saving, setSaving]       = useState(false)
  const [saved, setSaved]         = useState(false)
  const [exporting, setExporting] = useState(false)

  if (!data) return null

  const { destination, total_days, total_budget, total_estimated_cost,
    weather_note, days, budget_breakdown, packing_tips, weather, similar_past_trips } = data

  const budgetUsed = total_estimated_cost
    ? Math.min(Math.round((total_estimated_cost / total_budget) * 100), 100) : 0

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await fetch('/api/trips/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itinerary: data, user_id: userId || 'default' }),
      })
      if (res.ok) setSaved(true)
    } catch {}
    setSaving(false)
  }

  const handlePDF = async () => {
    setExporting(true)
    try {
      const res = await fetch('/api/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (res.ok) {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `PlanMyTrip_${destination || 'trip'}.pdf`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch {}
    setExporting(false)
  }

  return (
    <div className="space-y-5 fade-in">
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
          <div>
            <h2 className="text-2xl font-bold gradient-text">{destination}</h2>
            <p className="text-gray-400 text-sm mt-1">{total_days}-day itinerary · {data.travel_type || 'Trip'}</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <button onClick={handleSave} disabled={saving || saved}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-300 hover:border-green-500/50 hover:text-green-400 transition disabled:opacity-50">
              {saved ? '✅ Saved' : saving ? '...' : '💾 Save Trip'}
            </button>
            <button onClick={handlePDF} disabled={exporting}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-300 hover:border-pink-500/50 hover:text-pink-400 transition disabled:opacity-50">
              {exporting ? '⏳ Generating...' : '📄 Export PDF'}
            </button>
            <button onClick={onReset}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-400 hover:text-white hover:border-white/30 transition">
              ← New Trip
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <WeatherBadge weather={weather} />
          {weather_note && (
            <div className="text-xs text-gray-400 bg-white/5 border border-white/10 rounded-xl px-4 py-2 flex items-center gap-2">
              <span>🌤</span> {weather_note}
            </div>
          )}
        </div>
        {similar_past_trips?.length > 0 && (
          <div className="mt-3 flex gap-2 flex-wrap">
            <span className="text-xs text-gray-500">Similar saved trips:</span>
            {similar_past_trips.map(t => (
              <span key={t.id} className="text-xs bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded-full px-3 py-1">
                {t.destination} · {t.days}d
              </span>
            ))}
          </div>
        )}
      </div>

      {googleMapsKey && <MapView itinerary={data} googleMapsKey={googleMapsKey} />}

      <div className="card p-6">
        <h3 className="font-semibold text-white mb-4">💰 Budget Overview</h3>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-gray-400">Estimated</span>
          <span className="font-bold text-white">₹{total_estimated_cost?.toLocaleString()}</span>
        </div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-400">Your Budget</span>
          <span className="font-bold text-green-400">₹{total_budget?.toLocaleString()}</span>
        </div>
        <div className="w-full bg-white/10 rounded-full h-2 mb-4">
          <div className={`h-2 rounded-full transition-all ${budgetUsed > 90 ? 'bg-red-500' : 'bg-gradient-to-r from-purple-500 to-pink-500'}`}
            style={{ width: `${budgetUsed}%` }} />
        </div>
        {budget_breakdown && (
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(budget_breakdown).map(([k, v]) => (
              <div key={k} className="bg-white/5 rounded-xl p-3">
                <p className="text-xs text-gray-500 capitalize">{k}</p>
                <p className="font-semibold text-white text-sm">₹{v?.toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="font-semibold text-white mb-3 px-1">📅 Day-wise Itinerary</h3>
        <div className="space-y-3">
          {days?.map((day, i) => <DayCard key={day.day} day={day} index={i} />)}
        </div>
      </div>

      {packing_tips?.length > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold text-white mb-3">🎒 Packing Tips</h3>
          <ul className="space-y-2">
            {packing_tips.map((tip, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-400">
                <span className="text-purple-400">→</span> {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
