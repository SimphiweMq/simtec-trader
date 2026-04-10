# Simtek Trader — React Frontend

React + Vite dashboard for the Simtek Trading signal engine backend.

## Features

- **Dark Theme** — Dark (#0f1117) background with cyan accents
- **Ticker Selector** — JSE stocks & forex pairs
- **Signal Card** — Current signal status (BUY/SELL/HOLD) with metrics
  - Close price, RSI, MACD
  - Signal strength indicator bar
- **Price Chart** — 90-day historical price with:
  - SMA(20) and SMA(50) overlay lines
  - BUY/SELL signal markers
  - Interactive tooltips

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173`

**Note:** Backend must be running on `http://localhost:8001`

## Build

```bash
npm run build
```

Outputs to `dist/`

## Project Structure

```
src/
├── App.jsx              # Main app component
├── App.css
├── main.jsx             # React entry point
├── index.css            # Global styles (dark theme)
└── components/
    ├── TickerSelector.jsx    # Asset picker
    ├── TickerSelector.css
    ├── SignalCard.jsx        # Signal display
    ├── SignalCard.css
    ├── PriceChart.jsx        # 90-day chart
    └── PriceChart.css
```

## Colors

- **Primary Accent**: `#00d4ff` (cyan) — JSE
- **Secondary Accent**: `#ff6b35` (orange) — Forex
- **Buy Signal**: `#3fb950` (green)
- **Sell Signal**: `#f85149` (red)
- **Background**: `#0f1117` (dark)
- **Surface**: `#1a1d26` (lighter dark)

## Dependencies

- **react** — UI library
- **react-dom** — DOM rendering
- **axios** — HTTP client
- **recharts** — Chart components
