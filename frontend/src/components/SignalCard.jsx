import { memo } from 'react'
import './SignalCard.css'

// Trading-native palette. Color is NEVER the sole signal — text labels (BUY/SELL/HOLD) carry the meaning.
const SIGNAL_COLORS = {
  BUY: { fg: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  SELL: { fg: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  HOLD: { fg: '#8b949e', bg: 'rgba(139, 148, 158, 0.1)' },
}

function SignalCard({ signal, ticker }) {
  if (!signal) {
    return (
      <div className="signal-card">
        <div className="signal-placeholder">No signal data</div>
      </div>
    )
  }

  const signalValue = signal.current_signal?.signal || 'HOLD'
  const { fg: signalColor, bg: signalBgColor } =
    SIGNAL_COLORS[signalValue] ?? SIGNAL_COLORS.HOLD

  const strength = signal.current_signal?.signal_strength || 0
  const closeRaw = signal.current_signal?.close
  const close = closeRaw?.toFixed(2) || '—'
  const rsiRaw = signal.current_signal?.rsi
  const rsi = rsiRaw?.toFixed(1) || '—'
  const macdRaw = signal.current_signal?.macd
  const macd = macdRaw?.toFixed(4) || '—'

  const rsiTrend =
    rsiRaw == null ? null
    : rsiRaw > 70 ? { label: '▲ OB', cls: 'metric-trend--bearish' }
    : rsiRaw < 30 ? { label: '▼ OS', cls: 'metric-trend--bullish' }
    : null

  const macdTrend =
    macdRaw == null ? null
    : macdRaw > 0 ? { label: '▲', cls: 'metric-trend--bullish' }
    : { label: '▼', cls: 'metric-trend--bearish' }

  return (
    <div className="signal-card">
      <div className="signal-header">
        <h3>{ticker}</h3>
        <span className="timestamp">
          {signal.current_signal?.timestamp
            ? new Date(signal.current_signal.timestamp).toLocaleDateString()
            : '—'}
        </span>
      </div>

      <div className="signal-badge-container">
        <div
          className="signal-badge"
          style={{
            backgroundColor: signalBgColor,
            borderColor: signalColor,
          }}
        >
          <span
            className="signal-value"
            style={{ color: signalColor }}
          >
            {signalValue}
          </span>
        </div>
      </div>

      <div className="signal-metrics">
        <div className="metric">
          <span className="metric-label">Price</span>
          <span className="metric-value">{close}</span>
        </div>
        <div className="metric">
          <span className="metric-label">RSI(14)</span>
          <span className="metric-value">{rsi}</span>
          {rsiTrend && (
            <span className={`metric-trend ${rsiTrend.cls}`}>{rsiTrend.label}</span>
          )}
        </div>
        <div className="metric">
          <span className="metric-label">MACD</span>
          <span className="metric-value">{macd}</span>
          {macdTrend && (
            <span className={`metric-trend ${macdTrend.cls}`}>{macdTrend.label}</span>
          )}
        </div>
      </div>

      <div className="strength-container">
        <span className="strength-label">Signal Strength</span>
        <div className="strength-bar">
          <div
            className="strength-fill"
            style={{
              width: `${strength * 100}%`,
              backgroundColor: signalColor,
            }}
          />
        </div>
        <span className="strength-value">{(strength * 100).toFixed(0)}%</span>
      </div>
    </div>
  )
}

export default memo(SignalCard)
