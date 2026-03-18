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

function SlotCard({ slot, type, index, dayPlaces }) {
  const nextSlot = index < dayPlaces.length - 1 ? dayPlaces[index + 1] : null
  const distance = nextSlot ? Math.round(Math.sqrt(Math.pow(nextSlot.lat - slot.lat, 2) + Math.pow(nextSlot.lng - slot.lng, 2)) * 111) : 0
  const estimatedTravelTime = nextSlot ? Math.ceil(distance / 15) : 0
  
  return (
    <div className={`slot-card p-4 bg-gradient-to-br ${SLOT_COLORS[type]}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{SLOT_ICONS[type]}</span>
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{SLOT_LABELS[type]}</span>
        <span className="ml-auto text-xs font-semibold text-green-400">₹{slot.cost?.toLocaleString()}</span>
      </div>
      <p className="font-semibold text-white text-sm mb-1">{slot.place}</p>
      <p className="text-gray-400 text-xs mb-1">{slot.activity}</p>
      <p className="text-gray-500 text-xs mb-2">⏱ {slot.duration}</p>
      
      {/* Cost Breakdown */}
      <div className="bg-black/20 rounded px-2 py-1.5 mb-2 text-xs space-y-0.5 border-l-2 border-yellow-500/50">
        <div className="flex justify-between text-gray-300">
          <span>💳 Entry:</span>
          <span className="text-yellow-300">₹{Math.round(slot.cost * 0.4)}</span>
        </div>
        <div className="flex justify-between text-gray-300">
          <span>🍽 Food:</span>
          <span className="text-yellow-300">₹{Math.round(slot.cost * 0.35)}</span>
        </div>
        <div className="flex justify-between text-gray-300">
          <span>🚕 Transport:</span>
          <span className="text-yellow-300">₹{Math.round(slot.cost * 0.25)}</span>
        </div>
      </div>
      
      {/* Travel to next */}
      {nextSlot && (
        <div className="text-xs text-orange-300 bg-orange-500/10 rounded px-2 py-1 border border-orange-500/20">
          → Next: {distance}km ({estimatedTravelTime}min)
        </div>
      )}
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
            {(() => {
              const slots = [
                { slot: day.morning, type: 'morning' },
                { slot: day.afternoon, type: 'afternoon' },
                { slot: day.evening, type: 'evening' },
              ].filter(s => s.slot)
              return slots.map((s, idx) => (
                <SlotCard 
                  key={s.type} 
                  slot={s.slot} 
                  type={s.type}
                  index={idx}
                  dayPlaces={slots.map(x => x.slot)}
                />
              ))
            })()}
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

export default function ItineraryView({ data, onReset, userId }) {
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
      {/* Sticky Back Button */}
      <div className="flex items-center gap-2 mb-4">
        <button onClick={onReset}
          className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/30 hover:border-purple-500/60 rounded-lg text-sm text-purple-300 hover:text-purple-200 transition font-semibold">
          ← Back to Home
        </button>
        <p className="text-xs text-gray-500 ml-auto">Viewing trip details • Use chat on right to modify</p>
      </div>

      <div className="card p-6">
        <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
          <div>
            <h2 className="text-2xl font-bold gradient-text">{destination}</h2>
            <p className="text-gray-400 text-sm mt-1">{total_days}-day itinerary · {data.travel_type || 'Trip'}</p>
            {(data.start_date || data.end_date) && (
              <p className="text-gray-500 text-xs mt-2">
                📅 {data.start_date ? new Date(data.start_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Start'} 
                {data.end_date && ` - ${new Date(data.end_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}`}
              </p>
            )}
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

      <MapView itinerary={data} />

      {data.hotels && data.hotels.length > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold text-white mb-4">🏨 Accommodation Options</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.hotels.map((hotel, idx) => (
              <div 
                key={idx}
                className={`p-4 rounded-lg border-2 transition cursor-pointer $
                  idx === 1 
                    ? 'bg-gradient-to-br from-purple-600/20 to-pink-600/20 border-purple-500/50'
                    : 'bg-white/5 border-white/10 hover:border-white/30'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-white text-sm">{hotel.name}</p>
                    <p className="text-xs text-gray-400">{hotel.type}</p>
                  </div>
                  <span className="text-lg">⭐ {hotel.rating}</span>
                </div>
                <p className="text-xs text-gray-400 mb-2">{hotel.description}</p>
                <p className="text-xs text-gray-500 mb-3">📍 {hotel.location}</p>
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-400">
                    <p>₹{hotel.price_per_night?.toLocaleString()}/night</p>
                    <p className="text-green-400 font-semibold">Total: ₹{(hotel.price_per_night * total_days)?.toLocaleString()}</p>
                  </div>
                  <div className="flex flex-wrap gap-1 justify-end">
                    {hotel.amenities?.slice(0, 2).map((amenity, i) => (
                      <span key={i} className="text-xs bg-white/10 px-2 py-1 rounded text-gray-300">{amenity}</span>
                    ))}
                  </div>
                </div>
                {idx === 1 && <p className="mt-2 text-xs text-purple-300">✓ Recommended</p>}
              </div>
            ))}
          </div>
          {data.accommodation_cost && (
            <div className="mt-4 p-3 bg-purple-600/10 border border-purple-500/20 rounded-lg">
              <p className="text-xs text-gray-400">Recommended accommodation cost:</p>
              <p className="font-bold text-lg text-purple-300">₹{data.accommodation_cost?.toLocaleString()}</p>
            </div>
          )}
        </div>
      )}

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
          {days?.map((day, i) => (
        <DayCard key={day.day} day={day} index={i} />
      ))}
        </div>
      </div>

      {packing_tips?.length > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold text-white mb-4 text-lg">🎒 Smart Packing List</h3>
          <div className="space-y-3">
            {packing_tips.map((tip, i) => {
              const [icon, content] = tip.includes(':') ? [tip.split(':')[0], tip.split(':')[1]?.trim()] : ['📦', tip]
              return (
                <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-3">
                  <p className="font-semibold text-sm text-white mb-1">{icon}</p>
                  <p className="text-sm text-gray-300 leading-relaxed">{content || tip}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
