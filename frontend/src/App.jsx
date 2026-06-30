import { useState, useCallback } from 'react'
import axios from 'axios'
import TickerSelector from './components/TickerSelector'
import SignalCard from './components/SignalCard'
import PriceChart from './components/PriceChart'
import SystemHealth from './components/SystemHealth'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8002'

export default function App() {
  const [selectedAsset, setSelectedAsset] = useState(null)
  const [signalData, setSignalData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleLoad = useCallback(async (asset) => {
    setIsLoading(true)
    setError(null)
    setSignalData(null)

    try {
      let endpoint
      let displayTicker

      if (asset.type === 'jse') {
        endpoint = `/signal/${asset.ticker}`
        displayTicker = `${asset.ticker}.JO`
      } else {
        endpoint = `/signal/forex/${asset.from}/${asset.to}`
        displayTicker = `${asset.from}/${asset.to}`
      }

      const response = await axios.get(`${API_BASE}${endpoint}`)
      setSelectedAsset({
        ...asset,
        displayTicker,
      })
      setSignalData(response.data)
    } catch (err) {
      console.error('Error fetching signal data:', err)
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to fetch signal data'
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>SIMTEK TRADER</h1>
          <p className="subtitle">Signal Engine Dashboard</p>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <TickerSelector onLoad={handleLoad} isLoading={isLoading} />
          <SystemHealth />

          {error && (
            <div className="error-alert">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {signalData && selectedAsset && (
            <>
              <SignalCard
                signal={signalData}
                ticker={selectedAsset.displayTicker}
              />
              <PriceChart historyData={signalData.history} />
            </>
          )}

          {!signalData && !isLoading && !error && (
            <div className="welcome-msg">
              <p>👈 Select a ticker and load data to get started</p>
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>Simteknologies Trading Signal Engine • Phase 1</p>
      </footer>
    </div>
  )
}
