import { useAuth } from '../hooks/useAuth'
import { useExpenses } from '../hooks/useExpenses'
import { useBookings } from '../hooks/useIncome'
import { useListings } from '../hooks/useListings'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate, getCurrentMonth } from '../utils/dateHelpers'

export default function Dashboard() {
  const { userProfile, user, loading: authLoading } = useAuth()

  // Fetch data for current month (queries will wait for auth via axios interceptor)
  const currentMonth = getCurrentMonth()
  const { data: expenses, isLoading: expensesLoading, error: expensesError } = useExpenses(currentMonth)
  const { data: bookings, isLoading: bookingsLoading, error: bookingsError } = useBookings(currentMonth)
  const { data: listings, error: listingsError } = useListings()

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Show error if queries failed
  const hasError = expensesError || bookingsError || listingsError
  if (hasError) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <p className="text-red-600 font-semibold mb-2">Error loading dashboard data</p>
          <p className="text-sm text-gray-600 mb-4">
            {expensesError?.message || bookingsError?.message || listingsError?.message || 'Please try signing out and signing in again'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="text-primary-600 hover:text-primary-700 underline"
          >
            Reload Page
          </button>
        </div>
      </div>
    )
  }

  // Calculate totals
  const regularExpenses = expenses?.reduce((sum, exp) => sum + exp.amount, 0) || 0
  const commissionExpenses = bookings?.reduce((sum, booking) => sum + (booking.commissionPaid || 0), 0) || 0
  const totalExpenses = regularExpenses + commissionExpenses
  const totalRevenue = bookings?.reduce((sum, booking) => sum + booking.totalPaid, 0) || 0
  const netIncome = totalRevenue - totalExpenses

  // Get recent items (last 5)
  const recentExpenses = expenses?.slice(0, 5) || []
  const recentBookings = bookings?.slice(0, 5) || []

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Welcome back, {userProfile?.displayName}!
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Stats Cards */}
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
          {bookingsLoading ? (
            <div className="animate-pulse h-8 bg-gray-200 rounded w-24"></div>
          ) : (
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalRevenue)}</p>
          )}
          <p className="text-xs text-green-600 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Expenses</p>
          {expensesLoading ? (
            <div className="animate-pulse h-8 bg-gray-200 rounded w-24"></div>
          ) : (
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalExpenses)}</p>
          )}
          <p className="text-xs text-red-600 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Net Income</p>
          {expensesLoading || bookingsLoading ? (
            <div className="animate-pulse h-8 bg-gray-200 rounded w-24"></div>
          ) : (
            <p className={`text-2xl font-bold ${netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(netIncome)}
            </p>
          )}
          <p className="text-xs text-blue-600 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Active Properties</p>
          <p className="text-2xl font-bold text-gray-900">{listings?.length || 0}</p>
          <p className="text-xs text-gray-600 mt-1">Total listings</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Bookings
          </h2>
          {bookingsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : recentBookings.length > 0 ? (
            <div className="space-y-3">
              {recentBookings.map((booking) => {
                const listing = listings?.find(l => l.id === booking.listingId)
                return (
                  <div key={booking.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div>
                      <p className="font-medium text-gray-900">{booking.guestName}</p>
                      <p className="text-sm text-gray-500">
                        {listing?.name || 'Unknown'} • {formatDate(booking.checkIn)}
                      </p>
                    </div>
                    <p className="font-semibold text-green-600">{formatCurrency(booking.totalPaid)}</p>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No bookings yet</p>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Expenses
          </h2>
          {expensesLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : recentExpenses.length > 0 ? (
            <div className="space-y-3">
              {recentExpenses.map((expense) => {
                const listing = listings?.find(l => l.id === expense.listingId)
                return (
                  <div key={expense.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div>
                      <p className="font-medium text-gray-900">{expense.category}</p>
                      <p className="text-sm text-gray-500">
                        {listing?.name || 'Unknown'} • {formatDate(expense.date)}
                      </p>
                    </div>
                    <p className="font-semibold text-red-600">{formatCurrency(expense.amount)}</p>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No expenses yet</p>
          )}
        </div>
      </div>
    </div>
  )
}
