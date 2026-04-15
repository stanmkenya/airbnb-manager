import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

// Fetch all users (Admin only)
export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await apiClient.get('/users')
      return response.data
    },
  })
}

// Invite user (Admin only)
export function useInviteUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (userData) => {
      const response = await apiClient.post('/users/invite', userData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User invited successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to invite user')
    },
  })
}

// Update user role (Admin only)
export function useUpdateUserRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ uid, role }) => {
      const response = await apiClient.put(`/users/${uid}/role`, { role })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User role updated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update user role')
    },
  })
}

// Update user listings (Admin only)
export function useUpdateUserListings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ uid, assignedListings }) => {
      const response = await apiClient.put(`/users/${uid}/listings`, { assignedListings })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User listings updated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update user listings')
    },
  })
}

// Deactivate user (Admin only)
export function useDeactivateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (uid) => {
      const response = await apiClient.put(`/users/${uid}/deactivate`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User deactivated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to deactivate user')
    },
  })
}

// Activate user (Admin only)
export function useActivateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (uid) => {
      const response = await apiClient.put(`/users/${uid}/activate`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User activated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to activate user')
    },
  })
}
