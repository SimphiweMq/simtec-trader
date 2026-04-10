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

export default function PriceChart({ historyData }) {
  if (!historyData || historyData.length === 0) {
    return (
      <div className="price-chart-container">
        <div className="chart-placeholder">No chart data available</div>
      </div>
    )
  }

  // Prepare data with signal markers
  const chartData = historyData.map((row) => ({
    date: new Date(row.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    close: parseFloat(row.close),
    signal: row.signal,
    rsi: parseFloat(row.rsi) || null,
    macd: parseFloat(row.macd) || null,
  }))

  // Colors
  const colors = {
    close: '#00d4ff',
    sma20: '#00d4ff',
    sma50: '#ff6b35',
    buySignal: '#3fb950',
    sellSignal: '#f85149',
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="custom-tooltip">
          <p className="date">{data.date}</p>
          <p style={{ color: colors.close }}>
            Close: {data.close.toFixed(2)}
          </p>
          {data.rsi && (
            <p style={{ color: colors.sma20 }}>
              RSI: {data.rsi.toFixed(1)}
            </p>
          )}
          {data.macd && (
            <p style={{ color: colors.sma50 }}>
              MACD: {data.macd.toFixed(4)}
            </p>
          )}
          {data.signal && (
            <p style={{
              color: data.signal === 'BUY' ? colors.buySignal : colors.sellSignal,
              fontWeight: 'bold',
            }}>
              Signal: {data.signal}
            </p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="price-chart-container">
      <h3>Price History & Signals (90 Days)</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <defs>
            <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.close} stopOpacity={0.8} />
              <stop offset="95%" stopColor={colors.close} stopOpacity={0} />
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
            wrapperStyle={{ paddingTop: '20px' }}
            contentStyle={{
              backgroundColor: 'var(--surface-light)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
            }}
          />

          <Line
            type="monotone"
            dataKey="close"
            stroke={colors.close}
            dot={false}
            strokeWidth={2}
            name="Close Price"
            isAnimationActive={false}
          />

          {/* BUY signals */}
          {chartData.map((data, index) =>
            data.signal === 'BUY' ? (
              <ReferenceDot
                key={`buy-${index}`}
                x={data.date}
                y={data.close}
                r={6}
                fill={colors.buySignal}
                stroke={colors.buySignal}
                strokeWidth={2}
              />
            ) : null
          )}

          {/* SELL signals */}
          {chartData.map((data, index) =>
            data.signal === 'SELL' ? (
              <ReferenceDot
                key={`sell-${index}`}
                x={data.date}
                y={data.close}
                r={6}
                fill={colors.sellSignal}
                stroke={colors.sellSignal}
                strokeWidth={2}
              />
            ) : null
          )}
        </LineChart>
      </ResponsiveContainer>
      <div className="legend-info">
        <span className="legend-item">
          <span className="dot" style={{ backgroundColor: colors.close }}></span>
          Close Price
        </span>
        <span className="legend-item">
          <span className="dot" style={{ backgroundColor: colors.buySignal }}></span>
          BUY Signal
        </span>
        <span className="legend-item">
          <span className="dot" style={{ backgroundColor: colors.sellSignal }}></span>
          SELL Signal
        </span>
      </div>
    </div>
  )
}
