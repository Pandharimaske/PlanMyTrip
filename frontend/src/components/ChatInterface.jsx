import React, { useState, useRef, useEffect } from 'react'

const SUGGESTIONS = [
  "Replace Day 1 evening with something more adventurous",
  "My budget changed to ₹5000, please adjust",
  "Add more food spots on Day 2",
  "What's the best time to visit these places?",
  "Swap Day 1 and Day 2",
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold
        ${isUser
          ? 'bg-gradient-to-br from-pink-600 to-purple-600'
          : 'bg-gradient-to-br from-purple-700 to-indigo-700'
        }`}>
        {isUser ? '👤' : '✈️'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser
          ? 'bg-gradient-to-br from-pink-600/30 to-purple-600/30 border border-pink-500/20 text-white rounded-tr-sm'
          : 'bg-white/5 border border-white/10 text-gray-200 rounded-tl-sm'
        }`}>
        {msg.content}
        {msg.updated && (
          <span className="block mt-2 text-xs text-green-400 font-semibold">
            ✅ Itinerary updated
          </span>
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

export default function ChatInterface({ itinerary, onItineraryUpdate }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `I'm your travel assistant for this ${itinerary?.destination} trip! Ask me to modify any part of the itinerary, adjust the budget, or answer questions about the plan. 🗺️`
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [hasUpdate, setHasUpdate] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return

    setInput('')
    setLoading(true)

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
        onItineraryUpdate(data.itinerary)
        setHasUpdate(true)
        setTimeout(() => setHasUpdate(false), 3000)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message || 'Done! I updated your itinerary.',
          updated: true,
        }])
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message || 'Got it!',
        }])
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
      }])
    } finally {
      setLoading(false)
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
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full glow-btn flex items-center justify-center text-2xl shadow-2xl"
      >
        {isOpen ? '✕' : '💬'}
        {hasUpdate && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-black" />
        )}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] flex flex-col"
          style={{
            height: '520px',
            background: 'rgba(15,10,30,0.97)',
            border: '1px solid rgba(124,58,237,0.3)',
            borderRadius: '20px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.6), 0 0 40px rgba(124,58,237,0.1)',
            backdropFilter: 'blur(20px)',
          }}>

          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-sm">✈️</div>
            <div>
              <p className="text-sm font-semibold text-white">Trip Assistant</p>
              <p className="text-xs text-gray-500">{itinerary.destination} · {itinerary.total_days} days</p>
            </div>
            <div className="ml-auto w-2 h-2 rounded-full bg-green-400" title="Online" />
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m, i) => <Message key={i} msg={m} />)}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions */}
          {messages.length === 1 && (
            <div className="px-3 pb-2 flex gap-2 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
              {SUGGESTIONS.slice(0,3).map(s => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="flex-shrink-0 text-xs bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded-full px-3 py-1.5 hover:bg-purple-600/40 transition whitespace-nowrap"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-white/10 flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask me to change anything..."
              rows={1}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-purple-500 resize-none"
              style={{ maxHeight: '80px' }}
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || loading}
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-white flex-shrink-0 disabled:opacity-40 transition hover:opacity-90"
            >
              ↑
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); opacity: 0.5; }
          50% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </>
  )
}
