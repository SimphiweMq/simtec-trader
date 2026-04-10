import { useState, useEffect } from 'react'
import axios from 'axios'
import './TickerSelector.css'

export default function TickerSelector({ onLoad, isLoading }) {
  const [tickers, setTickers] = useState({})
  const [selectedTicker, setSelectedTicker] = useState('NPN')
  const [isForex, setIsForex] = useState(false)
  const [fromCurrency, setFromCurrency] = useState('ZAR')
  const [toCurrency, setToCurrency] = useState('USD')
  const [loadingTickers, setLoadingTickers] = useState(true)

  useEffect(() => {
    const fetchTickers = async () => {
      try {
        const response = await axios.get('http://localhost:8001/tickers')
        setTickers(response.data.tickers || {})
      } catch (error) {
        console.error('Error fetching tickers:', error)
      } finally {
        setLoadingTickers(false)
      }
    }
    fetchTickers()
  }, [])

  const handleLoad = () => {
    if (isForex) {
      onLoad({ type: 'forex', from: fromCurrency, to: toCurrency })
    } else {
      onLoad({ type: 'jse', ticker: selectedTicker })
    }
  }

  return (
    <div className="ticker-selector">
      <div className="selector-header">
        <h2>Signal Dashboard</h2>
      </div>

      <div className="selector-tabs">
        <button
          className={`tab ${!isForex ? 'active' : ''}`}
          onClick={() => setIsForex(false)}
        >
          JSE Stocks
        </button>
        <button
          className={`tab ${isForex ? 'active' : ''}`}
          onClick={() => setIsForex(true)}
        >
          Forex
        </button>
      </div>

      <div className="selector-content">
        {!isForex ? (
          <div className="jse-controls">
            <label>Select Stock:</label>
            <select
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              disabled={loadingTickers}
            >
              {loadingTickers ? (
                <option>Loading tickers...</option>
              ) : (
                Object.entries(tickers).map(([ticker, name]) => (
                  <option key={ticker} value={ticker}>
                    {ticker} - {name}
                  </option>
                ))
              )}
            </select>
          </div>
        ) : (
          <div className="forex-controls">
            <div className="currency-pair">
              <input
                type="text"
                maxLength="3"
                placeholder="From"
                value={fromCurrency}
                onChange={(e) => setFromCurrency(e.target.value.toUpperCase())}
              />
              <span className="sep">/</span>
              <input
                type="text"
                maxLength="3"
                placeholder="To"
                value={toCurrency}
                onChange={(e) => setToCurrency(e.target.value.toUpperCase())}
              />
            </div>
          </div>
        )}
      </div>

      <button
        className="load-btn"
        onClick={handleLoad}
        disabled={isLoading}
      >
        {isLoading ? '⏳ Loading...' : '📊 Load'}
      </button>
    </div>
  )
}
