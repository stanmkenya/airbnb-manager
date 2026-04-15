import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

// Fetch bookings with filters
export function useBookings(filters = {}) {
  const params = new URLSearchParams()
  if (filters.listingId) params.append('listingId', filters.listingId)
  if (filters.from) params.append('from', filters.from)
  if (filters.to) params.append('to', filters.to)
  if (filters.platform) params.append('platform', filters.platform)

  return useQuery({
    queryKey: ['bookings', filters],
    queryFn: async () => {
      const response = await apiClient.get(`/income?${params.toString()}`)
      return response.data
    },
  })
}

// Create booking
export function useCreateBooking() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (bookingData) => {
      const response = await apiClient.post('/income', bookingData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Booking added successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add booking')
    },
  })
}

// Update booking
export function useUpdateBooking() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, listingId, data }) => {
      const response = await apiClient.put(`/income/${id}?listingId=${listingId}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Booking updated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update booking')
    },
  })
}

// Delete booking
export function useDeleteBooking() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, listingId }) => {
      const response = await apiClient.delete(`/income/${id}?listingId=${listingId}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Booking deleted successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete booking')
    },
  })
}
