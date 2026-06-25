import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import SignalCard from '../components/SignalCard'

const makeSignal = (signalValue, strength = 0.75) => ({
  current_signal: {
    signal: signalValue,
    signal_strength: strength,
    close: 102.34,
    rsi: 54.2,
    macd: 0.0041,
    timestamp: '2024-01-15T10:00:00Z',
  },
})

describe('SignalCard', () => {
  it('renders placeholder when signal is null', () => {
    render(<SignalCard signal={null} ticker="NPN" />)
    expect(screen.getByText('No signal data')).toBeInTheDocument()
  })

  it('renders ticker name', () => {
    render(<SignalCard signal={makeSignal('BUY')} ticker="NPN.JO" />)
    expect(screen.getByText('NPN.JO')).toBeInTheDocument()
  })

  it('displays BUY signal', () => {
    render(<SignalCard signal={makeSignal('BUY')} ticker="NPN" />)
    expect(screen.getByText('BUY')).toBeInTheDocument()
  })

  it('displays SELL signal', () => {
    render(<SignalCard signal={makeSignal('SELL')} ticker="NPN" />)
    expect(screen.getByText('SELL')).toBeInTheDocument()
  })

  it('displays HOLD as default when signal is missing', () => {
    const signal = { current_signal: {} }
    render(<SignalCard signal={signal} ticker="NPN" />)
    expect(screen.getByText('HOLD')).toBeInTheDocument()
  })

  it('displays formatted price, RSI, and MACD metrics', () => {
    render(<SignalCard signal={makeSignal('BUY')} ticker="NPN" />)
    expect(screen.getByText('102.34')).toBeInTheDocument()
    expect(screen.getByText('54.2')).toBeInTheDocument()
    expect(screen.getByText('0.0041')).toBeInTheDocument()
  })

  it('displays signal strength percentage', () => {
    render(<SignalCard signal={makeSignal('BUY', 0.75)} ticker="NPN" />)
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('does not re-mount when re-rendered with same props', () => {
    const signal = makeSignal('BUY')
    const { rerender } = render(<SignalCard signal={signal} ticker="NPN" />)
    const badge = screen.getByText('BUY')
    rerender(<SignalCard signal={signal} ticker="NPN" />)
    expect(screen.getByText('BUY')).toBe(badge)
  })
})
