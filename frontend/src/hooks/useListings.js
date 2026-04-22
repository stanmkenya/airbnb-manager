import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import toast from 'react-hot-toast'
import { useAuth } from './useAuth'

// Fetch all listings
export function useListings(collectionId = null) {
  const { userProfile } = useAuth()

  return useQuery({
    queryKey: ['listings', collectionId],
    queryFn: async () => {
      // Build query params
      const params = {}
      if (collectionId) {
        params.collectionId = collectionId
      } else if (userProfile?.collectionId) {
        // Use user's collection if available
        params.collectionId = userProfile.collectionId
      }

      const response = await apiClient.get('/listings', { params })
      return response.data
    },
    retry: 1, // Retry once if it fails (for auth timing issues)
    retryDelay: 500, // Wait 500ms before retrying
    staleTime: 30000, // Consider data fresh for 30 seconds
    enabled: !!userProfile, // Only fetch when user profile is loaded
  })
}

// Fetch single listing
export function useListing(id, collectionId = null) {
  const { userProfile } = useAuth()

  return useQuery({
    queryKey: ['listings', id, collectionId],
    queryFn: async () => {
      const params = {}
      if (collectionId) {
        params.collectionId = collectionId
      } else if (userProfile?.collectionId) {
        params.collectionId = userProfile.collectionId
      }

      const response = await apiClient.get(`/listings/${id}`, { params })
      return response.data
    },
    enabled: !!id && !!userProfile,
  })
}

// Create listing
export function useCreateListing() {
  const queryClient = useQueryClient()
  const { userProfile } = useAuth()

  return useMutation({
    mutationFn: async (listingData) => {
      // Build query params
      const params = {}

      // Determine which collection to use
      // Extract collectionId from listingData if provided
      const { collectionId: providedCollectionId, ...data } = listingData

      if (providedCollectionId) {
        params.collectionId = providedCollectionId
      } else if (userProfile?.collectionId) {
        // Collection admin uses their assigned collection
        params.collectionId = userProfile.collectionId
      } else if (userProfile?.role === 'superadmin') {
        // Superadmin MUST specify collectionId
        // Get it from first available collection (temporary solution)
        // TODO: Add collection selector UI for superadmin
        console.warn('[useCreateListing] Superadmin should specify collectionId')
      }

      const response = await apiClient.post('/listings', data, { params })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      toast.success('Listing created successfully!')
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create listing'
      toast.error(errorMessage)
      console.error('[useCreateListing] Error:', errorMessage)
    },
  })
}

// Update listing
export function useUpdateListing() {
  const queryClient = useQueryClient()
  const { userProfile } = useAuth()

  return useMutation({
    mutationFn: async ({ id, data, collectionId }) => {
      const params = {}

      if (collectionId) {
        params.collectionId = collectionId
      } else if (userProfile?.collectionId) {
        params.collectionId = userProfile.collectionId
      }

      const response = await apiClient.put(`/listings/${id}`, data, { params })
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      queryClient.invalidateQueries({ queryKey: ['listings', variables.id] })
      toast.success('Listing updated successfully!')
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update listing'
      toast.error(errorMessage)
    },
  })
}

// Delete listing
export function useDeleteListing() {
  const queryClient = useQueryClient()
  const { userProfile } = useAuth()

  return useMutation({
    mutationFn: async (id) => {
      const params = {}

      // Get collectionId from listing if needed
      if (userProfile?.collectionId) {
        params.collectionId = userProfile.collectionId
      }

      const response = await apiClient.delete(`/listings/${id}`, { params })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      toast.success('Listing deleted successfully!')
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete listing'
      toast.error(errorMessage)
    },
  })
}
