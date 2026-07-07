import { memo, useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import './SystemHealth.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8002'
const POLL_INTERVAL_MS = 60_000

// Heart-rate monitor / ECG pulse icon (inline SVG, no icon library dependency)
function PulseIcon() {
  return (
    <svg
      className="health-icon"
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="4 12 7 6 10 18 13 9 16 12 20 12" />
    </svg>
  )
}

// Status dot colors map to --fill-* CSS vars; text label carries the meaning for colorblind safety.
const STATUS_LABELS = { success: 'Online', warning: 'Degraded', error: 'Offline' }

function getApiStatus(latencyMs) {
  if (latencyMs < 500) return 'success'
  if (latencyMs < 2000) return 'warning'
  return 'error'
}

function getCacheAgeStatus(lastFetchMin) {
  if (lastFetchMin === null) return 'warning'
  if (lastFetchMin < 30) return 'success'
  if (lastFetchMin < 55) return 'warning'
  return 'error'
}

function getTickersStatus(active) {
  return active > 0 ? 'success' : 'warning'
}

function getLastFetchStatus(min) {
  if (min === null) return 'warning'
  if (min < 5) return 'success'
  if (min < 30) return 'warning'
  return 'error'
}

function StatusDot({ status }) {
  return (
    <span
      className={`status-dot status-dot--${status}`}
      role="img"
      aria-label={STATUS_LABELS[status] ?? status}
    />
  )
}

function HealthRow({ label, statusLevel, valueLine }) {
  return (
    <div className="health-row">
      <StatusDot status={statusLevel} />
      <div className="health-row-text">
        <span className="health-row-label">{label}</span>
        <span className="health-row-value">{valueLine}</span>
      </div>
    </div>
  )
}

function SystemHealth() {
  const [health, setHealth] = useState(null)
  const [fetchError, setFetchError] = useState(false)

  const fetchHealth = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/health`)
      setHealth(res.data)
      setFetchError(false)
    } catch {
      setFetchError(true)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    const id = setInterval(fetchHealth, POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [fetchHealth])

  const loading = !health && !fetchError

  const apiStatus = fetchError ? 'error' : health ? getApiStatus(health.latency_ms) : 'warning'
  const apiValue = fetchError
    ? 'Offline'
    : loading
      ? 'Checking…'
      : `${STATUS_LABELS[apiStatus]} · ${health.latency_ms}ms`

  const cache = health?.cache
  const cacheAgeStatus = getCacheAgeStatus(cache?.last_fetch_min ?? null)
  const cacheAgeValue = loading
    ? 'Checking…'
    : cache
      ? `${cache.last_fetch_min ?? '—'} min / ${cache.ttl_min} min`
      : '—'

  const tickersStatus = getTickersStatus(cache?.tickers_active ?? 0)
  const tickersValue = loading
    ? 'Checking…'
    : cache
      ? `${cache.tickers_active} / ${cache.tickers_total}`
      : '—'

  const lastFetchStatus = getLastFetchStatus(cache?.last_fetch_min ?? null)
  const lastFetchValue = loading
    ? 'Checking…'
    : cache
      ? cache.last_fetch_min !== null
        ? `${cache.last_fetch_min} min ago`
        : 'No data yet'
      : '—'

  return (
    <div className="system-health-card">
      <div className="health-header">
        <PulseIcon />
        <span className="health-title">System health</span>
      </div>

      <div className="health-grid">
        <HealthRow label="API status" statusLevel={apiStatus} valueLine={apiValue} />
        <HealthRow label="Cache age" statusLevel={cacheAgeStatus} valueLine={cacheAgeValue} />
        <HealthRow label="Tickers active" statusLevel={tickersStatus} valueLine={tickersValue} />
        <HealthRow label="Last fetch" statusLevel={lastFetchStatus} valueLine={lastFetchValue} />
      </div>
    </div>
  )
}

export default memo(SystemHealth)
