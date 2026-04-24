import { useAuth } from '../hooks/useAuth'
import { isAdmin, isManagerOrAdmin } from '../utils/roleGuard'

/**
 * Debug component to display current user profile and role permissions
 * Add this to any page to see what the frontend is receiving
 */
export default function DebugUserProfile() {
  const { user, userProfile, loading } = useAuth()

  const canManageListings = isAdmin(userProfile)
  const canManageExpensesBookings = isManagerOrAdmin(userProfile)

  return (
    <div className="fixed bottom-4 right-4 max-w-md bg-yellow-50 border-2 border-yellow-400 rounded-lg shadow-lg p-4 z-50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-yellow-900">🐛 Debug: User Profile</h3>
        <button
          onClick={() => {
            document.querySelector('[data-debug-panel]').remove()
          }}
          className="text-yellow-700 hover:text-yellow-900 text-lg font-bold"
        >
          ×
        </button>
      </div>

      {loading && (
        <div className="text-sm text-yellow-800">Loading user profile...</div>
      )}

      {!loading && !user && (
        <div className="text-sm text-red-600">❌ No user logged in</div>
      )}

      {!loading && user && !userProfile && (
        <div className="text-sm text-red-600">
          ❌ User logged in but userProfile is NULL/undefined
          <br />
          <strong>This is the problem!</strong>
        </div>
      )}

      {!loading && user && userProfile && (
        <div className="space-y-2 text-xs">
          <div>
            <strong className="text-yellow-900">Email:</strong>
            <div className="text-yellow-800 break-all">{user.email}</div>
          </div>

          <div>
            <strong className="text-yellow-900">UID:</strong>
            <div className="text-yellow-800 break-all">{user.uid}</div>
          </div>

          <div>
            <strong className="text-yellow-900">Role:</strong>
            <div className="text-yellow-800">
              {userProfile.role || 'UNDEFINED'}
              {!userProfile.role && (
                <span className="text-red-600 font-bold"> ← MISSING!</span>
              )}
            </div>
          </div>

          <div>
            <strong className="text-yellow-900">Collection ID:</strong>
            <div className="text-yellow-800">
              {userProfile.collectionId || 'None (superadmin)'}
            </div>
          </div>

          <div>
            <strong className="text-yellow-900">Display Name:</strong>
            <div className="text-yellow-800">
              {userProfile.displayName || 'N/A'}
            </div>
          </div>

          <div className="border-t border-yellow-300 pt-2 mt-2">
            <strong className="text-yellow-900 block mb-1">
              Permissions:
            </strong>
            <div className="space-y-1">
              <div
                className={`px-2 py-1 rounded text-xs ${
                  canManageListings
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {canManageListings ? '✅' : '❌'} Can manage listings (add/edit/delete)
              </div>
              <div
                className={`px-2 py-1 rounded text-xs ${
                  canManageExpensesBookings
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {canManageExpensesBookings ? '✅' : '❌'} Can manage expenses/bookings
              </div>
            </div>
          </div>

          <div className="border-t border-yellow-300 pt-2 mt-2">
            <strong className="text-yellow-900 block mb-1">
              Raw userProfile object:
            </strong>
            <pre className="text-xs bg-yellow-100 p-2 rounded overflow-auto max-h-40">
              {JSON.stringify(userProfile, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
