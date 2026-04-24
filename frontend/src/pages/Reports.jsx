import { useState } from 'react'
import { useExpenses } from '../hooks/useExpenses'
import { useBookings } from '../hooks/useIncome'
import { useListings } from '../hooks/useListings'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate } from '../utils/dateHelpers'

export default function Reports() {
  const [selectedPeriod, setSelectedPeriod] = useState('all')

  const { data: allExpenses, isLoading: expensesLoading } = useExpenses()
  const { data: allBookings, isLoading: bookingsLoading } = useBookings()
  const { data: listings } = useListings()

  if (expensesLoading || bookingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const expenses = allExpenses || []
  const bookings = allBookings || []

  // Calculate totals
  const totalRevenue = bookings.reduce((sum, booking) => sum + (booking.totalPaid || 0), 0)
  const regularExpenses = expenses.reduce((sum, expense) => sum + (expense.amount || 0), 0)
  const commissionExpenses = bookings.reduce((sum, booking) => sum + (booking.commissionPaid || 0), 0)
  const totalExpenses = regularExpenses + commissionExpenses
  const netProfit = totalRevenue - totalExpenses
  const profitMargin = totalRevenue > 0 ? ((netProfit / totalRevenue) * 100).toFixed(1) : 0

  // Revenue by listing
  const revenueByListing = {}
  bookings.forEach(booking => {
    const listingId = booking.listingId
    if (!revenueByListing[listingId]) {
      revenueByListing[listingId] = 0
    }
    revenueByListing[listingId] += booking.totalPaid || 0
  })

  // Expenses by listing (including commission)
  const expensesByListing = {}
  expenses.forEach(expense => {
    const listingId = expense.listingId
    if (!expensesByListing[listingId]) {
      expensesByListing[listingId] = 0
    }
    expensesByListing[listingId] += expense.amount || 0
  })
  // Add commission expenses by listing
  bookings.forEach(booking => {
    const listingId = booking.listingId
    if (booking.commissionPaid) {
      if (!expensesByListing[listingId]) {
        expensesByListing[listingId] = 0
      }
      expensesByListing[listingId] += booking.commissionPaid
    }
  })

  // Expenses by category
  const expensesByCategory = {}
  expenses.forEach(expense => {
    const category = expense.category || 'Other'
    if (!expensesByCategory[category]) {
      expensesByCategory[category] = 0
    }
    expensesByCategory[category] += expense.amount || 0
  })
  // Add commission/fees as a category
  if (commissionExpenses > 0) {
    expensesByCategory['Commission & Fees'] = commissionExpenses
  }

  // Property performance
  const propertyPerformance = (listings || []).map(listing => {
    const revenue = revenueByListing[listing.id] || 0
    const expenses = expensesByListing[listing.id] || 0
    const profit = revenue - expenses
    const bookingCount = bookings.filter(b => b.listingId === listing.id).length

    return {
      id: listing.id,
      name: listing.name,
      revenue,
      expenses,
      profit,
      bookingCount,
      profitMargin: revenue > 0 ? ((profit / revenue) * 100).toFixed(1) : 0
    }
  }).sort((a, b) => b.profit - a.profit)

  // Top categories by expense
  const topCategories = Object.entries(expensesByCategory)
    .map(([category, amount]) => ({ category, amount }))
    .sort((a, b) => b.amount - a.amount)

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="text-gray-600 mt-1">Comprehensive insights and performance metrics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalRevenue)}</p>
          <p className="text-xs text-gray-500 mt-1">{bookings.length} bookings</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Expenses</p>
          <p className="text-2xl font-bold text-red-600">{formatCurrency(totalExpenses)}</p>
          <p className="text-xs text-gray-500 mt-1">{expenses.length} expenses</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Net Profit</p>
          <p className={`text-2xl font-bold ${netProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(netProfit)}
          </p>
          <p className="text-xs text-gray-500 mt-1">All time</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Profit Margin</p>
          <p className={`text-2xl font-bold ${profitMargin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {profitMargin}%
          </p>
          <p className="text-xs text-gray-500 mt-1">Overall performance</p>
        </div>
      </div>

      {/* Property Performance */}
      <div className="card mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Performance</h2>
        {propertyPerformance.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Property
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bookings
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Expenses
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Net Profit
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Margin
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {propertyPerformance.map((property) => (
                  <tr key={property.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{property.name}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{property.bookingCount}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-green-600">{formatCurrency(property.revenue)}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-red-600">{formatCurrency(property.expenses)}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className={`text-sm font-semibold ${property.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(property.profit)}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className={`text-sm font-medium ${property.profitMargin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {property.profitMargin}%
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No property data available</p>
        )}
      </div>

      {/* Expense Breakdown */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Expense Breakdown by Category</h2>
        {topCategories.length > 0 ? (
          <div className="space-y-4">
            {topCategories.map(({ category, amount }) => {
              const percentage = ((amount / totalExpenses) * 100).toFixed(1)
              return (
                <div key={category}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{category}</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(amount)} ({percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No expense data available</p>
        )}
      </div>
    </div>
  )
}
