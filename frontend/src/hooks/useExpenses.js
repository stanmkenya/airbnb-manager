import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

// Fetch expenses with filters
export function useExpenses(filters = {}) {
  const params = new URLSearchParams()
  if (filters.listingId) params.append('listingId', filters.listingId)
  if (filters.from) params.append('from', filters.from)
  if (filters.to) params.append('to', filters.to)
  if (filters.category) params.append('category', filters.category)

  return useQuery({
    queryKey: ['expenses', filters],
    queryFn: async () => {
      const response = await apiClient.get(`/expenses?${params.toString()}`)
      return response.data
    },
    retry: 1, // Retry once if it fails (for auth timing issues)
    retryDelay: 500, // Wait 500ms before retrying
    staleTime: 30000, // Consider data fresh for 30 seconds
  })
}

// Create expense
export function useCreateExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (expenseData) => {
      const response = await apiClient.post('/expenses', expenseData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast.success('Expense added successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add expense')
    },
  })
}

// Update expense
export function useUpdateExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, listingId, data }) => {
      const response = await apiClient.put(`/expenses/${id}?listingId=${listingId}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast.success('Expense updated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update expense')
    },
  })
}

// Delete expense
export function useDeleteExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, listingId }) => {
      const response = await apiClient.delete(`/expenses/${id}?listingId=${listingId}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast.success('Expense deleted successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete expense')
    },
  })
}
