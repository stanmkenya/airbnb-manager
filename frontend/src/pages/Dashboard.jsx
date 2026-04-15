import { useAuth } from '../hooks/useAuth'

export default function Dashboard() {
  const { userProfile } = useAuth()

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
          <p className="text-2xl font-bold text-gray-900">$0.00</p>
          <p className="text-xs text-green-600 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Expenses</p>
          <p className="text-2xl font-bold text-gray-900">$0.00</p>
          <p className="text-xs text-red-600 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Net Income</p>
          <p className="text-2xl font-bold text-gray-900">$0.00</p>
          <p className="text-xs text-blue-600 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Occupancy Rate</p>
          <p className="text-2xl font-bold text-gray-900">0%</p>
          <p className="text-xs text-gray-600 mt-1">This month</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Bookings
          </h2>
          <p className="text-gray-500 text-center py-8">No bookings yet</p>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Expenses
          </h2>
          <p className="text-gray-500 text-center py-8">No expenses yet</p>
        </div>
      </div>
    </div>
  )
}
