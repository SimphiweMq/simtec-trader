import { memo, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceDot,
  ResponsiveContainer,
} from 'recharts'
import './PriceChart.css'

// Module-level constant — no new object reference on each render
const COLORS = {
  close: '#00d4ff',
  // Colorblind-safe BUY/SELL: teal vs orange distinguishable in deuteranopia
  buySignal: '#00BFA5',
  sellSignal: '#FF7043',
}

const LEGEND_CONTENT_STYLE = {
  backgroundColor: 'var(--surface-light)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
}

const LEGEND_WRAPPER_STYLE = { paddingTop: '20px' }

// Defined outside component — stable reference, no remount on every render
function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null
  const data = payload[0].payload
  return (
    <div className="custom-tooltip">
      <p className="date">{data.date}</p>
      <p style={{ color: COLORS.close }}>Close: {data.close.toFixed(2)}</p>
      {data.rsi && (
        <p style={{ color: COLORS.close }}>RSI: {data.rsi.toFixed(1)}</p>
      )}
      {data.macd && (
        <p style={{ color: '#ff6b35' }}>MACD: {data.macd.toFixed(4)}</p>
      )}
      {data.signal && (
        <p
          style={{
            color: data.signal === 'BUY' ? COLORS.buySignal : COLORS.sellSignal,
            fontWeight: 'bold',
          }}
        >
          Signal: {data.signal}
        </p>
      )}
    </div>
  )
}

function PriceChart({ historyData }) {
  if (!historyData || historyData.length === 0) {
    return (
      <div className="price-chart-container">
        <div className="chart-placeholder">No chart data available</div>
      </div>
    )
  }

  // Memoized — only recomputes when historyData reference changes
  const chartData = useMemo(
    () =>
      historyData.map((row) => ({
        date: new Date(row.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        close: parseFloat(row.close),
        signal: row.signal,
        rsi: parseFloat(row.rsi) || null,
        macd: parseFloat(row.macd) || null,
      })),
    [historyData]
  )

  // Memoized signal dot arrays — single pass, not two separate map calls
  const { buyDots, sellDots } = useMemo(() => {
    const buys = []
    const sells = []
    for (const item of chartData) {
      if (item.signal === 'BUY') buys.push(item)
      else if (item.signal === 'SELL') sells.push(item)
    }
    return { buyDots: buys, sellDots: sells }
  }, [chartData])

  return (
    <div className="price-chart-container">
      <h3>Price History &amp; Signals (90 Days)</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <defs>
            <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.close} stopOpacity={0.8} />
              <stop offset="95%" stopColor={COLORS.close} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="date"
            stroke="var(--text-muted)"
            style={{ fontSize: '0.8rem' }}
          />
          <YAxis
            stroke="var(--text-muted)"
            style={{ fontSize: '0.8rem' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={LEGEND_WRAPPER_STYLE}
            contentStyle={LEGEND_CONTENT_STYLE}
          />

          <Line
            type="monotone"
            dataKey="close"
            stroke={COLORS.close}
            dot={false}
            strokeWidth={2}
            name="Close Price"
            isAnimationActive={false}
          />

          {buyDots.map((data, index) => (
            <ReferenceDot
              key={`buy-${index}`}
              x={data.date}
              y={data.close}
              r={6}
              fill={COLORS.buySignal}
              stroke={COLORS.buySignal}
              strokeWidth={2}
            />
          ))}

          {sellDots.map((data, index) => (
            <ReferenceDot
              key={`sell-${index}`}
              x={data.date}
              y={data.close}
              r={6}
              fill={COLORS.sellSignal}
              stroke={COLORS.sellSignal}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="legend-info">
        <span className="legend-item">
          <span className="dot" style={{ backgroundColor: COLORS.close }}></span>
          Close Price
        </span>
        <span className="legend-item">
          <span className="dot" style={{ backgroundColor: COLORS.buySignal }}></span>
          BUY Signal
        </span>
        <span className="legend-item">
          <span className="dot" style={{ backgroundColor: COLORS.sellSignal }}></span>
          SELL Signal
        </span>
      </div>
    </div>
  )
}

export default memo(PriceChart)
