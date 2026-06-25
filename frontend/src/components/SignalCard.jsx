import { memo } from 'react'
import './SignalCard.css'

// Colorblind-safe palette — matches PriceChart COLORS constants
const SIGNAL_COLORS = {
  BUY: { fg: '#00BFA5', bg: 'rgba(0, 191, 165, 0.1)' },
  SELL: { fg: '#FF7043', bg: 'rgba(255, 112, 67, 0.1)' },
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
