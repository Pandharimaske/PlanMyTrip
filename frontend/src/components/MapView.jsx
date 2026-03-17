import React, { useEffect, useRef } from 'react'

const SLOT_COLORS = { morning: '#f59e0b', afternoon: '#3b82f6', evening: '#8b5cf6' }

function buildMarkers(days) {
  const markers = []
  days?.forEach((day) => {
    ;['morning','afternoon','evening'].forEach(slot => {
      const s = day[slot]
      if (s?.lat && s?.lng) {
        markers.push({
          lat: s.lat, lng: s.lng,
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

export default function MapView({ itinerary, googleMapsKey }) {
  const mapRef = useRef(null)

  useEffect(() => {
    if (!itinerary?.days?.length || !googleMapsKey) return
    const markers = buildMarkers(itinerary.days)
    if (!markers.length) return

    const scriptId = 'google-maps-script'
    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script')
      script.id = scriptId
      script.src = `https://maps.googleapis.com/maps/api/js?key=${googleMapsKey}`
      script.async = true
      script.onload = () => initMap(markers)
      document.head.appendChild(script)
    } else if (window.google) {
      initMap(markers)
    }
  }, [itinerary, googleMapsKey])

  function initMap(markers) {
    if (!mapRef.current || !window.google) return
    const map = new window.google.maps.Map(mapRef.current, {
      center: { lat: markers[0].lat, lng: markers[0].lng },
      zoom: 12,
      styles: [
        { elementType: 'geometry', stylers: [{ color: '#1a0a2e' }] },
        { elementType: 'labels.text.fill', stylers: [{ color: '#a78bfa' }] },
        { elementType: 'labels.text.stroke', stylers: [{ color: '#1a0a2e' }] },
        { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#2d1b69' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0f0a1e' }] },
      ],
    })

    const bounds = new window.google.maps.LatLngBounds()
    const infoWindow = new window.google.maps.InfoWindow()

    markers.forEach(m => {
      const marker = new window.google.maps.Marker({
        position: { lat: m.lat, lng: m.lng },
        map,
        title: m.place,
        label: { text: m.label.slice(-1), color: '#fff', fontWeight: 'bold', fontSize: '11px' },
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 18,
          fillColor: m.color,
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
        },
      })
      marker.addListener('click', () => {
        infoWindow.setContent(`
          <div style="font-family:Inter,sans-serif;padding:4px">
            <b style="color:#7c3aed">${m.label}</b><br/>
            <span style="font-size:13px">${m.place}</span>
          </div>
        `)
        infoWindow.open(map, marker)
      })
      bounds.extend(marker.position)
    })
    map.fitBounds(bounds)
  }

  if (!googleMapsKey) return null

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-white/10 flex items-center gap-3">
        <span className="text-base font-semibold text-white">🗺️ Map View</span>
        <div className="flex gap-3 ml-auto text-xs text-gray-400">
          {Object.entries(SLOT_COLORS).map(([s, c]) => (
            <span key={s} className="flex items-center gap-1">
              <span style={{ background: c, width:10, height:10, borderRadius:'50%', display:'inline-block' }} />
              {s.charAt(0).toUpperCase()+s.slice(1)}
            </span>
          ))}
        </div>
      </div>
      <div ref={mapRef} style={{ height: '380px', width: '100%', background: '#1a0a2e' }} />
    </div>
  )
}
