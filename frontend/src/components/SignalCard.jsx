import { memo } from 'react'
import './SignalCard.css'

function SignalCard({ signal, ticker }) {
  if (!signal) {
    return (
      <div className="signal-card">
        <div className="signal-placeholder">No signal data</div>
      </div>
    )
  }

  const signalValue = signal.current_signal?.signal || 'HOLD'
  const signalColor =
    signalValue === 'BUY'
      ? '#3fb950'
      : signalValue === 'SELL'
        ? '#f85149'
        : '#8b949e'
  const signalBgColor =
    signalValue === 'BUY'
      ? 'rgba(63, 185, 80, 0.1)'
      : signalValue === 'SELL'
        ? 'rgba(248, 81, 73, 0.1)'
        : 'rgba(139, 148, 158, 0.1)'

  const strength = signal.current_signal?.signal_strength || 0
  const close = signal.current_signal?.close?.toFixed(2) || '—'
  const rsi = signal.current_signal?.rsi?.toFixed(1) || '—'
  const macd = signal.current_signal?.macd?.toFixed(4) || '—'

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
        </div>
        <div className="metric">
          <span className="metric-label">MACD</span>
          <span className="metric-value">{macd}</span>
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
