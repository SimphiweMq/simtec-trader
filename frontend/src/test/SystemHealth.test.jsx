import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import React from 'react'
import SystemHealth from '../components/SystemHealth'

// Explicit factory so axios.get is always a vi.fn()
vi.mock('axios', () => ({
  default: { get: vi.fn() },
}))

import axios from 'axios'

const HEALTH_OK = {
  status: 'ok',
  version: '0.1.0',
  latency_ms: 12.5,
  cache: {
    tickers_active: 3,
    tickers_total: 8,
    ttl_min: 60,
    last_fetch_min: 5.2,
    oldest_fetch_min: 15.0,
  },
}

afterEach(() => {
  vi.clearAllMocks()
  vi.useRealTimers()
})

describe('SystemHealth', () => {
  it('renders header with title', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    expect(screen.getByText('System health')).toBeInTheDocument()
  })

  it('shows checking state before data loads', () => {
    axios.get.mockReturnValue(new Promise(() => {})) // never resolves
    render(<SystemHealth />)
    expect(screen.getAllByText('Checking…').length).toBeGreaterThan(0)
  })

  it('renders all four health row labels after data loads', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText('API status')).toBeInTheDocument()
      expect(screen.getByText('Cache age')).toBeInTheDocument()
      expect(screen.getByText('Tickers active')).toBeInTheDocument()
      expect(screen.getByText('Last fetch')).toBeInTheDocument()
    })
  })

  it('displays latency in API status when online', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText(/Online · 12\.5ms/)).toBeInTheDocument()
    })
  })

  it('displays tickers active / total', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText('3 / 8')).toBeInTheDocument()
    })
  })

  it('displays cache age with TTL', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText('5.2 min / 60 min')).toBeInTheDocument()
    })
  })

  it('displays last fetch in minutes', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText('5.2 min ago')).toBeInTheDocument()
    })
  })

  it('shows Offline when API request fails', async () => {
    axios.get.mockRejectedValue(new Error('Network error'))
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument()
    })
  })

  it('shows "No data yet" when last_fetch_min is null', async () => {
    axios.get.mockResolvedValue({
      data: {
        ...HEALTH_OK,
        cache: { ...HEALTH_OK.cache, last_fetch_min: null },
      },
    })
    render(<SystemHealth />)
    await waitFor(() => {
      expect(screen.getByText('No data yet')).toBeInTheDocument()
    })
  })

  it('status dots have accessible aria-labels', async () => {
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => {
      const dots = screen.getAllByRole('img')
      expect(dots.length).toBeGreaterThan(0)
      dots.forEach((dot) => {
        expect(dot).toHaveAttribute('aria-label')
      })
    })
  })

  it('polls again after 60 seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    axios.get.mockResolvedValue({ data: HEALTH_OK })
    render(<SystemHealth />)
    await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1))
    await act(async () => {
      vi.advanceTimersByTime(60_000)
    })
    await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(2))
  })
})
