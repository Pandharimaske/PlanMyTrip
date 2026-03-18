import React, { useState, useRef, useEffect } from 'react'

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold
        ${isUser
          ? 'bg-gradient-to-br from-pink-600 to-purple-600'
          : 'bg-gradient-to-br from-purple-700 to-indigo-700'
        }`}>
        {isUser ? '👤' : '✈️'}
      </div>

      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed break-words
        ${isUser
          ? 'bg-gradient-to-br from-pink-600/30 to-purple-600/30 border border-pink-500/20 text-white rounded-tr-sm'
          : 'bg-white/5 border border-white/10 text-gray-200 rounded-tl-sm'
        }`}>
        {msg.content}
        {msg.updated && (
          <span className="block mt-2 text-xs text-green-400 font-semibold animate-pulse">
            ✅ Itinerary updated
          </span>
        )}
        {msg.changes && msg.changes.length > 0 && (
          <div className="mt-2 pt-2 border-t border-white/10 text-xs text-gray-300">
            <span className="font-semibold text-green-400">Changes:</span>
            <div className="mt-1 space-y-1">
              {msg.changes.map((change, i) => (
                <div key={i} className="text-green-300/80">• {change}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-700 to-indigo-700 flex items-center justify-center text-sm">✈️</div>
      <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
        {[0,1,2].map(i => (
          <div key={i} className="w-2 h-2 rounded-full bg-purple-400"
            style={{ animation: `bounce 1.2s ease-in-out ${i*0.2}s infinite` }} />
        ))}
      </div>
    </div>
  )
}

function getSmartSuggestions(itinerary) {
  if (!itinerary) return []
  
  const suggestions = [
    `Change hotel to ${itinerary.hotels?.[0]?.type || 'luxury option'}`,
    `Adjust my budget to something more affordable`,
    `Show me other accommodation options`,
    `Add more ${itinerary.interests?.[0] || 'fun'} activities`,
  ]
  return suggestions
}

export default function ChatInterface({ itinerary, onItineraryUpdate }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [hasUpdate, setHasUpdate] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Initialize suggestions when itinerary or chat opens
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setSuggestions(getSmartSuggestions(itinerary))
      setMessages([{
        role: 'assistant',
        content: `Ready to refine your ${itinerary?.destination} itinerary! Tell me what you'd like to change. 🎯`
      }])
    }
  }, [isOpen, itinerary])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const detectChanges = (oldItin, newItin) => {
    const changes = []
    
    if (oldItin.total_budget !== newItin.total_budget) {
      changes.push(`Budget: ₹${oldItin.total_budget} → ₹${newItin.total_budget}`)
    }
    
    if (oldItin.total_estimated_cost !== newItin.total_estimated_cost) {
      changes.push(`Cost: ₹${oldItin.total_estimated_cost} → ₹${newItin.total_estimated_cost}`)
    }
    
    if (oldItin.selected_hotel?.name !== newItin.selected_hotel?.name) {
      changes.push(`Hotel: ${newItin.selected_hotel?.name}`)
    }
    
    if (oldItin.accommodation_cost !== newItin.accommodation_cost) {
      changes.push(`Accommodation: ₹${oldItin.accommodation_cost} → ₹${newItin.accommodation_cost}`)
    }
    
    if (JSON.stringify(oldItin.days) !== JSON.stringify(newItin.days)) {
      const updatedDays = []
      for (let i = 0; i < Math.min(oldItin.days.length, newItin.days.length); i++) {
        if (JSON.stringify(oldItin.days[i]) !== JSON.stringify(newItin.days[i])) {
          updatedDays.push(i + 1)
        }
      }
      if (updatedDays.length > 0) {
        changes.push(`Day${updatedDays.length > 1 ? 's' : ''} updated: ${updatedDays.join(', ')}`)
      }
    }
    
    return changes
  }

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return

    setInput('')
    setLoading(true)
    setSuggestions([])

    const newMessages = [...messages, { role: 'user', content: msg }]
    setMessages(newMessages)

    try {
      const history = newMessages.slice(0, -1).map(m => ({
        role: m.role,
        content: m.content,
      }))

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          itinerary: itinerary,
          history,
        }),
      })

      const data = await res.json()

      if (data.type === 'update' && data.itinerary) {
        const changes = detectChanges(itinerary, data.itinerary)
        onItineraryUpdate(data.itinerary)
        setHasUpdate(true)
        setTimeout(() => setHasUpdate(false), 4000)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message || '✅ Done! I updated your itinerary.',
          updated: true,
          changes: changes,
        }])
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message || 'Got it!',
        }])
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Something went wrong. Please try again.',
      }])
    } finally {
      setLoading(false)
      setSuggestions(getSmartSuggestions(itinerary))
      inputRef.current?.focus()
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  if (!itinerary) return null

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full glow-btn flex items-center justify-center text-2xl shadow-2xl hover:scale-110 transition-transform"
      >
        {isOpen ? '✕' : '💬'}
        {hasUpdate && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-slate-950 animate-pulse" />
        )}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] flex flex-col"
          style={{
            height: '580px',
            background: 'rgba(15,10,30,0.98)',
            border: '1px solid rgba(124,58,237,0.4)',
            borderRadius: '20px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.7), 0 0 40px rgba(124,58,237,0.15)',
            backdropFilter: 'blur(20px)',
          }}>

          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-gradient-to-r from-purple-600/10 to-pink-600/10">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-sm">✈️</div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">Trip Refinement</p>
              <p className="text-xs text-gray-400">{itinerary.destination} • {itinerary.total_days} days</p>
            </div>
            <div className="w-2 h-2 rounded-full bg-green-400" title="Ready to refine" />
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m, i) => <Message key={i} msg={m} />)}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="px-3 pb-3 flex flex-col gap-2">
              <p className="text-xs text-gray-500 px-1">Try asking:</p>
              <div className="space-y-2">
                {suggestions.slice(0, 2).map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => send(s)}
                    className="w-full text-xs text-left bg-purple-600/15 border border-purple-500/30 text-purple-200 rounded-lg px-3 py-2 hover:bg-purple-600/30 transition line-clamp-2"
                  >
                    💡 {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-white/10 bg-gradient-to-r from-purple-600/5 to-pink-600/5 flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value.slice(0, 500))}
              onKeyDown={handleKey}
              placeholder="Ask me anything..."
              className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 resize-none"
              rows="3"
            />
            <button
              onClick={() => send()}
              disabled={loading || !input.trim()}
              className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-lg hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}
