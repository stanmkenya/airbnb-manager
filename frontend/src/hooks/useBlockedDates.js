import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

export function useBlockedDates(listingId) {
  return useQuery({
    queryKey: ['blocked-dates', listingId],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (listingId) {
        params.append('listing_id', listingId)
      }
      const response = await apiClient.get(`/blocked-dates?${params.toString()}`)
      return response.data
    },
    staleTime: 30000,
  })
}

export function useBlockDate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ listingId, date, reason }) => {
      const response = await apiClient.post('/blocked-dates', {
        listingId,
        date,
        reason: reason || 'Blocked by manager'
      })
      return response.data
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blocked-dates', variables.listingId] })
      queryClient.invalidateQueries({ queryKey: ['blocked-dates'] })
      toast.success('Date blocked successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to block date')
    }
  })
}

export function useUnblockDate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ listingId, date }) => {
      const response = await apiClient.delete(`/blocked-dates/${listingId}/${date}`)
      return response.data
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blocked-dates', variables.listingId] })
      queryClient.invalidateQueries({ queryKey: ['blocked-dates'] })
      toast.success('Date unblocked successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to unblock date')
    }
  })
}
