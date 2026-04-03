import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Plus, X, TrendingUp, TrendingDown, Users, Zap } from 'lucide-react'

export default function Dashboard() {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [username, setUsername] = useState(localStorage.getItem('username'))

  const [allStocks, setAllStocks] = useState({})
  const [watchlist, setWatchlist] = useState(() => {
    const saved = localStorage.getItem('watchlist')
    return saved ? JSON.parse(saved) : []
  })

  // Telemetry & Metrics State
  const [systemStats, setSystemStats] = useState({ active_wss_connections: 0, total_tracked_symbols: 0 })
  const initialPrices = useRef({}) // For calculating session percentage gains

  const [connected, setConnected] = useState(false)
  const [connectionError, setConnectionError] = useState(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [addingNew, setAddingNew] = useState(false)
  const searchRef = useRef(null)

  const navigate = useNavigate()
  const ws = useRef(null)
  const retryCount = useRef(0)

  // Fetch Telemetry Data
  useEffect(() => {
    if (!token) return

    const fetchStats = async () => {
      try {
        const res = await fetch('https://localhost:8000/api/stats')
        if (res.ok) {
          const data = await res.json()
          setSystemStats(data)
        }
      } catch (err) {
        // Silent failure for telemetry
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 15000)
    return () => clearInterval(interval)
  }, [token])

  useEffect(() => {
    localStorage.setItem('watchlist', JSON.stringify(watchlist))
  }, [watchlist])

  useEffect(() => {
    if (!token) {
      navigate('/login')
    }
  }, [token, navigate])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    setToken(null)
    setUsername(null)
    setAllStocks({})
    setConnected(false)
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    if (ws.current) ws.current.close()
    navigate('/')
  }

  useEffect(() => {
    if (!token) return

    let reconnectTimer;

    const connect = () => {
      ws.current = new WebSocket(`wss://localhost:8000/ws?token=${token}`)

      ws.current.onopen = () => {
        setConnected(true)
        setConnectionError(null)
        retryCount.current = 0
      }

      ws.current.onclose = (e) => {
        setConnected(false)
        if (e.code === 1008) {
          handleLogout()
          setConnectionError("Session expired or invalid token. Please log in again securely.")
        } else {
          const delay = Math.min(1000 * Math.pow(2, retryCount.current), 10000)
          setConnectionError(`Link broken. Reconnecting in ${delay / 1000}s...`)
          retryCount.current += 1
          reconnectTimer = setTimeout(connect, delay)
        }
      }

      ws.current.onerror = () => {}

      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data)

        if (message.type === 'INIT_STATE') {
          const initial = {}
          message.data.forEach(stock => {
            initial[stock.symbol] = stock
            if (!initialPrices.current[stock.symbol]) {
              initialPrices.current[stock.symbol] = stock.price
            }
          })
          setAllStocks(initial)
        } else if (message.type === 'MKT_UPDATE') {
          const { symbol, price } = message.data
          if (!initialPrices.current[symbol]) {
            initialPrices.current[symbol] = price
          }
          setAllStocks(prev => {
            const oldPrice = prev[symbol]?.price || price
            return {
              ...prev,
              [symbol]: {
                ...prev[symbol],
                price,
                symbol,
                isUp: price > oldPrice,
                isDown: price < oldPrice,
                updatedAt: new Date().toISOString()
              }
            }
          })
        }
      }
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer)
      if (ws.current) ws.current.close()
    }
  }, [token])

  const handleSearchChange = (e) => {
    const query = e.target.value.toUpperCase()
    setSearchQuery(query)

    if (query.length === 0) {
      setSearchResults([])
      setShowDropdown(false)
      return
    }

    const matched = Object.keys(allStocks)
      .filter(sym => sym.includes(query) && !watchlist.includes(sym))
    setSearchResults(matched)
    setShowDropdown(true)
  }

  const addToWatchlist = (symbol) => {
    if (!watchlist.includes(symbol)) {
      setWatchlist(prev => [...prev, symbol])
    }
    setSearchQuery('')
    setShowDropdown(false)
  }

  const removeFromWatchlist = (symbol) => {
    setWatchlist(prev => prev.filter(s => s !== symbol))
  }

  const trackNewTicker = async () => {
    if (!searchQuery.trim()) return
    setAddingNew(true)
    try {
      const res = await fetch('https://localhost:8000/api/stocks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: searchQuery.trim().toUpperCase() })
      })
      const data = await res.json()
      if (res.ok) {
        const sym = data.stock.symbol
        if (!initialPrices.current[sym]) {
          initialPrices.current[sym] = data.stock.price
        }
        setAllStocks(prev => ({
          ...prev,
          [sym]: { symbol: sym, price: data.stock.price, updatedAt: new Date().toISOString() }
        }))
        addToWatchlist(sym)
      }
    } catch (err) {
      console.error('Failed to track new ticker:', err)
    } finally {
      setAddingNew(false)
    }
  }

  const displayStocks = watchlist
    .map(sym => allStocks[sym])
    .filter(Boolean)

  // System Metrics & Session Calculations
  let topMover = null;
  let maxPct = -Infinity;
  displayStocks.forEach(s => {
    const initial = initialPrices.current[s.symbol];
    if (initial) {
      const pct = ((s.price - initial) / initial) * 100;
      if (pct > maxPct) {
        maxPct = pct;
        topMover = s.symbol;
      }
    }
  });

  if (!token) return null

  return (
    <div className="app-container">
      <header className="header">
        <div>
          <h1>Real-Time Stock Tracker</h1>
          <p className="welcome-text">Logged in as <strong>{username}</strong></p>
        </div>
        <div className="header-actions">
          <div className={`status-badge ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '● Live' : '○ Connecting...'}
          </div>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {connectionError && <div className="error-banner">{connectionError}</div>}

      {/* Metrics Ribbon */}
      <div className="metrics-ribbon">
        <div className="metric-card glass-effect">
          <div className="metric-icon purple-glow"><TrendingUp size={20} /></div>
          <div className="metric-info">
            <span className="metric-label">Top Session Mover</span>
            <span className="metric-value">{topMover ? topMover : '---'} <span className="metric-sub">{maxPct > -Infinity ? `+${maxPct.toFixed(2)}%` : ''}</span></span>
          </div>
        </div>
        <div className="metric-card glass-effect">
          <div className="metric-icon blue-glow"><Users size={20} /></div>
          <div className="metric-info">
            <span className="metric-label">Active Edges</span>
            <span className="metric-value">{systemStats.active_wss_connections} <span className="metric-sub">Clients</span></span>
          </div>
        </div>
        <div className="metric-card glass-effect">
          <div className="metric-icon orange-glow"><Zap size={20} /></div>
          <div className="metric-info">
            <span className="metric-label">Global Symbols</span>
            <span className="metric-value">{Math.max(systemStats.total_tracked_symbols, Object.keys(allStocks).length)} <span className="metric-sub">Tracked</span></span>
          </div>
        </div>
      </div>

      <div className="search-wrapper" ref={searchRef}>
        <div className="search-bar glass-effect">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search tickers (e.g. AAPL, TSLA)…"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => { if (searchQuery) setShowDropdown(true) }}
            className="search-input"
          />
        </div>

        {showDropdown && (
          <div className="search-dropdown glass-effect">
            {searchResults.length > 0 ? (
              searchResults.map(sym => (
                <button key={sym} className="search-result" onClick={() => addToWatchlist(sym)}>
                  <span className="result-symbol">{sym}</span>
                  <span className="result-price">${allStocks[sym]?.price?.toFixed(2)}</span>
                  <Plus size={16} className="result-add-icon" />
                </button>
              ))
            ) : (
              <div className="search-empty">
                <p>No matching tracked stocks found.</p>
                <button className="track-new-btn" onClick={trackNewTicker} disabled={addingNew}>
                  {addingNew ? 'Adding…' : `Track "${searchQuery}" as new ticker`}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="stock-grid">
        {displayStocks.map(stock => {
          const initial = initialPrices.current[stock.symbol];
          const pct = initial ? (((stock.price - initial) / initial) * 100).toFixed(2) : '0.00';
          return (
            <div
              className={`stock-card ${stock.isUp ? 'flash-up' : ''} ${stock.isDown ? 'flash-down' : ''}`}
              key={`card-${stock.symbol}-${stock.updatedAt}`}
            >
              <button className="remove-btn" onClick={() => removeFromWatchlist(stock.symbol)} title="Remove from dashboard">
                <X size={14} />
              </button>
              <div className="stock-header">
                <h2>{stock.symbol}</h2>
                <span className="stock-time">
                  {stock.updatedAt ? new Date(stock.updatedAt).toLocaleTimeString() : '...'}
                </span>
              </div>
              <div className="stock-price">
                <span className="currency">$</span>
                <span className="value">{stock.price?.toFixed(2)}</span>
              </div>
              <div className={`stock-gains ${pct >= 0 ? 'gains-up' : 'gains-down'}`}>
                {pct >= 0 ? '+' : ''}{pct}% <span>Session</span>
              </div>
            </div>
          )
        })}
      </div>

      {watchlist.length === 0 && !connectionError && (
        <div className="empty-state">
          <Search size={48} className="empty-icon" />
          <h3>Your dashboard is empty</h3>
          <p>Search for a stock ticker above and add it to start tracking in real-time.</p>
        </div>
      )}
    </div>
  )
}
