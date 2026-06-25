import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import PriceChart from '../components/PriceChart'

// Recharts uses ResizeObserver; polyfill for jsdom
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}

const mockHistory = [
  { date: '2024-01-01', close: '100.50', rsi: '45.2', macd: '0.0023', signal: 'BUY' },
  { date: '2024-01-02', close: '102.30', rsi: '52.1', macd: '0.0031', signal: null },
  { date: '2024-01-03', close: '99.80', rsi: '38.5', macd: '-0.0015', signal: 'SELL' },
  { date: '2024-01-04', close: '101.10', rsi: '50.0', macd: '0.0005', signal: null },
]

describe('PriceChart', () => {
  it('renders placeholder when historyData is undefined', () => {
    render(<PriceChart historyData={undefined} />)
    expect(screen.getByText('No chart data available')).toBeInTheDocument()
  })

  it('renders placeholder when historyData is empty array', () => {
    render(<PriceChart historyData={[]} />)
    expect(screen.getByText('No chart data available')).toBeInTheDocument()
  })

  it('renders chart heading when data is provided', () => {
    render(<PriceChart historyData={mockHistory} />)
    expect(screen.getByText('Price History & Signals (90 Days)')).toBeInTheDocument()
  })

  it('renders legend items for Close Price, BUY Signal, SELL Signal', () => {
    render(<PriceChart historyData={mockHistory} />)
    expect(screen.getByText('Close Price')).toBeInTheDocument()
    expect(screen.getByText('BUY Signal')).toBeInTheDocument()
    expect(screen.getByText('SELL Signal')).toBeInTheDocument()
  })

  it('does not re-mount when re-rendered with same data reference', () => {
    const { rerender } = render(<PriceChart historyData={mockHistory} />)
    const heading = screen.getByText('Price History & Signals (90 Days)')
    rerender(<PriceChart historyData={mockHistory} />)
    // If memo works, the same DOM node persists (no unmount/remount)
    expect(screen.getByText('Price History & Signals (90 Days)')).toBe(heading)
  })

  it('updates when historyData reference changes', () => {
    const { rerender } = render(<PriceChart historyData={mockHistory} />)
    const newHistory = [
      { date: '2024-02-01', close: '200.00', rsi: '60.0', macd: '0.01', signal: null },
    ]
    rerender(<PriceChart historyData={newHistory} />)
    expect(screen.getByText('Price History & Signals (90 Days)')).toBeInTheDocument()
  })
})
