import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const SLOT_COLORS = { morning: '#f59e0b', afternoon: '#3b82f6', evening: '#8b5cf6' }

function buildMarkers(days) {
  const markers = []
  days?.forEach((day) => {
    ;['morning', 'afternoon', 'evening'].forEach(slot => {
      const s = day[slot]
      if (s?.lat && s?.lng) {
        markers.push({
          lat: s.lat,
          lng: s.lng,
          label: `Day ${day.day} ${slot.charAt(0).toUpperCase()}`,
          place: s.place,
          slot,
          color: SLOT_COLORS[slot],
        })
      }
    })
  })
  return markers
}

export default function MapView({ itinerary }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  useEffect(() => {
    if (!itinerary?.days?.length) return
    const markers = buildMarkers(itinerary.days)
    if (!markers.length) return

    // Initialize map if not already done
    if (!mapInstanceRef.current && mapRef.current) {
      const map = L.map(mapRef.current).setView([markers[0].lat, markers[0].lng], 12)

      // Add OpenStreetMap tile layer (completely free, no API key needed)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map)

      mapInstanceRef.current = map
    }

    const map = mapInstanceRef.current
    if (!map) return

    // Remove old markers
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        map.removeLayer(layer)
      }
    })

    // Add new markers
    const group = new L.FeatureGroup()
    markers.forEach(m => {
      const marker = L.circleMarker([m.lat, m.lng], {
        radius: 12,
        fillColor: m.color,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 1,
      })
        .bindPopup(`<div style="font-family:Inter,sans-serif"><b style="color:#7c3aed">${m.label}</b><br/><span style="font-size:13px">${m.place}</span></div>`)
        .addTo(map)

      group.addLayer(marker)
    })

    // Fit bounds to show all markers
    if (group.getLayers().length > 0) {
      map.fitBounds(group.getBounds().pad(0.1))
    }
  }, [itinerary])

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-white/10 flex items-center gap-3">
        <span className="text-base font-semibold text-white">🗺️ Map View</span>
        <div className="flex gap-3 ml-auto text-xs text-gray-400">
          {Object.entries(SLOT_COLORS).map(([s, c]) => (
            <span key={s} className="flex items-center gap-1">
              <span style={{ background: c, width: 10, height: 10, borderRadius: '50%', display: 'inline-block' }}/>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </span>
          ))}
        </div>
      </div>
      <div
        ref={mapRef}
        className="map-container"
        style={{
          height: '400px',
          background: '#1a0a2e',
          borderTopLeftRadius: '8px',
          borderTopRightRadius: '8px',
        }}
      />
    </div>
  )
}
