import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

// Fetch all listings
export function useListings() {
  return useQuery({
    queryKey: ['listings'],
    queryFn: async () => {
      const response = await apiClient.get('/listings')
      return response.data
    },
  })
}

// Fetch single listing
export function useListing(id) {
  return useQuery({
    queryKey: ['listings', id],
    queryFn: async () => {
      const response = await apiClient.get(`/listings/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

// Create listing
export function useCreateListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (listingData) => {
      const response = await apiClient.post('/listings', listingData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      toast.success('Listing created successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create listing')
    },
  })
}

// Update listing
export function useUpdateListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/listings/${id}`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      queryClient.invalidateQueries({ queryKey: ['listings', variables.id] })
      toast.success('Listing updated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update listing')
    },
  })
}

// Delete listing
export function useDeleteListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/listings/${id}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      toast.success('Listing deleted successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete listing')
    },
  })
}
