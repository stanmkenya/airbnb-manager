import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

// Monthly Summary Report
export function useMonthlySummary(listingId, year) {
  return useQuery({
    queryKey: ['reports', 'monthly-summary', listingId, year],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (listingId) params.append('listingId', listingId)
      if (year) params.append('year', year)

      const response = await apiClient.get(`/reports/monthly-summary?${params.toString()}`)
      return response.data
    },
    enabled: !!year,
  })
}

// Cumulative Daily Report
export function useCumulativeReport(listingId, year, month) {
  return useQuery({
    queryKey: ['reports', 'cumulative', listingId, year, month],
    queryFn: async () => {
      const params = new URLSearchParams({ listingId, year, month })
      const response = await apiClient.get(`/reports/cumulative?${params.toString()}`)
      return response.data
    },
    enabled: !!listingId && !!year && !!month,
  })
}

// P&L Report
export function usePnLReport(fromDate, toDate, listingId) {
  return useQuery({
    queryKey: ['reports', 'pnl', fromDate, toDate, listingId],
    queryFn: async () => {
      const params = new URLSearchParams({ from: fromDate, to: toDate })
      if (listingId) params.append('listingId', listingId)

      const response = await apiClient.get(`/reports/pnl?${params.toString()}`)
      return response.data
    },
    enabled: !!fromDate && !!toDate,
  })
}

// Portfolio P&L Report (Admin only)
export function usePortfolioReport(fromDate, toDate) {
  return useQuery({
    queryKey: ['reports', 'portfolio', fromDate, toDate],
    queryFn: async () => {
      const params = new URLSearchParams({ from: fromDate, to: toDate })
      const response = await apiClient.get(`/reports/portfolio?${params.toString()}`)
      return response.data
    },
    enabled: !!fromDate && !!toDate,
  })
}

// Occupancy Report
export function useOccupancyReport(listingId, year, month) {
  return useQuery({
    queryKey: ['reports', 'occupancy', listingId, year, month],
    queryFn: async () => {
      const params = new URLSearchParams({ listingId, year, month })
      const response = await apiClient.get(`/reports/occupancy?${params.toString()}`)
      return response.data
    },
    enabled: !!listingId && !!year && !!month,
  })
}

// Year-over-Year Report
export function useYoYReport(listingId) {
  return useQuery({
    queryKey: ['reports', 'yoy', listingId],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (listingId) params.append('listingId', listingId)

      const response = await apiClient.get(`/reports/yoy?${params.toString()}`)
      return response.data
    },
  })
}
