import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { UserPlus, Edit2, Trash2, UserCheck, UserX, FolderOpen } from 'lucide-react'
import api from '../api/client'

export default function Users() {
  const { userProfile } = useAuth()
  const [users, setUsers] = useState([])
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)

  // Fetch users
  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/users')
      setUsers(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  // Fetch collections (superadmin only)
  const fetchCollections = async () => {
    if (userProfile?.role === 'superadmin') {
      try {
        const response = await api.get('/collections')
        setCollections(response.data)
      } catch (err) {
        console.error('Failed to load collections:', err)
      }
    }
  }

  useEffect(() => {
    fetchUsers()
    fetchCollections()
  }, [userProfile])

  const getCollectionName = (collectionId) => {
    if (!collectionId) return 'No Collection'
    const collection = collections.find(c => c.id === collectionId)
    return collection?.name || collectionId
  }

  const getRoleBadgeColor = (role) => {
    switch(role) {
      case 'superadmin': return 'bg-purple-100 text-purple-700'
      case 'collection_admin': return 'bg-blue-100 text-blue-700'
      case 'manager': return 'bg-green-100 text-green-700'
      case 'viewer': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const handleDeactivate = async (uid) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return

    try {
      await api.put(`/users/${uid}/deactivate`)
      fetchUsers()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to deactivate user')
    }
  }

  const handleActivate = async (uid) => {
    try {
      await api.put(`/users/${uid}/activate`)
      fetchUsers()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to activate user')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Loading users...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
        <p className="mt-2 text-gray-600">
          {userProfile?.role === 'superadmin'
            ? 'Manage all users across all collections'
            : 'Manage users in your collection'}
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="mb-6 flex gap-3">
        <button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
        >
          <UserPlus size={20} />
          Invite User
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role
              </th>
              {userProfile?.role === 'superadmin' && (
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection
                </th>
              )}
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.uid} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      {user.photoURL ? (
                        <img className="h-10 w-10 rounded-full" src={user.photoURL} alt="" />
                      ) : (
                        <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                          {user.email?.[0].toUpperCase()}
                        </div>
                      )}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {user.displayName || user.email}
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                    {user.role?.replace('_', ' ') || 'viewer'}
                  </span>
                </td>
                {userProfile?.role === 'superadmin' && (
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2 text-sm text-gray-900">
                      <FolderOpen size={16} className="text-gray-400" />
                      {getCollectionName(user.collectionId)}
                    </div>
                  </td>
                )}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    user.isActive === false
                      ? 'bg-red-100 text-red-700'
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {user.isActive === false ? 'Inactive' : 'Active'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setEditingUser(user)}
                      className="text-blue-600 hover:text-blue-900"
                      title="Edit user"
                    >
                      <Edit2 size={18} />
                    </button>

                    {user.isActive === false ? (
                      <button
                        onClick={() => handleActivate(user.uid)}
                        className="text-green-600 hover:text-green-900"
                        title="Activate user"
                      >
                        <UserCheck size={18} />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleDeactivate(user.uid)}
                        className="text-orange-600 hover:text-orange-900"
                        title="Deactivate user"
                      >
                        <UserX size={18} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Invite User Modal */}
      {showInviteModal && (
        <InviteUserModal
          collections={collections}
          isSuperadmin={userProfile?.role === 'superadmin'}
          onClose={() => setShowInviteModal(false)}
          onSuccess={() => {
            setShowInviteModal(false)
            fetchUsers()
          }}
        />
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <EditUserModal
          user={editingUser}
          collections={collections}
          isSuperadmin={userProfile?.role === 'superadmin'}
          onClose={() => setEditingUser(null)}
          onSuccess={() => {
            setEditingUser(null)
            fetchUsers()
          }}
        />
      )}
    </div>
  )
}

// Invite User Modal Component
function InviteUserModal({ collections, isSuperadmin, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    email: '',
    displayName: '',
    role: 'viewer',
    collectionId: collections[0]?.id || ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [inviteResult, setInviteResult] = useState(null)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const response = await api.post('/users/invite', formData)
      setInviteResult(response.data)
      // Don't close immediately - show the password reset link
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to invite user')
      setSubmitting(false)
    }
  }

  const handleCopyLink = () => {
    if (inviteResult?.passwordResetLink) {
      navigator.clipboard.writeText(inviteResult.passwordResetLink)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleFinish = () => {
    setInviteResult(null)
    onSuccess()
    onClose()
  }

  // Show success screen with password reset link
  if (inviteResult) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
          <div className="text-center mb-4">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">User Invited Successfully!</h2>
            <p className="text-gray-600 mb-4">
              {inviteResult.emailStatus === 'sent' ? (
                <>An invitation email has been sent to <strong>{inviteResult.email}</strong></>
              ) : (
                <>Please send the password reset link to <strong>{inviteResult.email}</strong></>
              )}
            </p>
          </div>

          {inviteResult.passwordResetLink && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password Reset Link
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={inviteResult.passwordResetLink}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm font-mono"
                  onClick={(e) => e.target.select()}
                />
                <button
                  onClick={handleCopyLink}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors whitespace-nowrap"
                >
                  {copied ? '✓ Copied!' : 'Copy Link'}
                </button>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                This link will expire in 1 hour. The user can use it to set their password and sign in.
              </p>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Instructions:</h3>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Copy the password reset link above</li>
              <li>Send it to {inviteResult.email} via email or your preferred method</li>
              <li>The user will click the link to set their password</li>
              <li>After setting their password, they can sign in to the platform</li>
            </ol>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleFinish}
              className="px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Show invite form
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-4">Invite New User</h2>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Display Name
            </label>
            <input
              type="text"
              required
              value={formData.displayName}
              onChange={(e) => setFormData({...formData, displayName: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {isSuperadmin && <option value="superadmin">Super Admin</option>}
              <option value="collection_admin">Collection Admin</option>
              <option value="manager">Manager</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          {isSuperadmin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Collection
              </label>
              <select
                value={formData.collectionId}
                onChange={(e) => setFormData({...formData, collectionId: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="">Select Collection</option>
                {collections.map((collection) => (
                  <option key={collection.id} value={collection.id}>
                    {collection.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {submitting ? 'Inviting...' : 'Invite User'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Edit User Modal Component
function EditUserModal({ user, collections, isSuperadmin, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    role: user.role || 'viewer',
    collectionId: user.collectionId || ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      // Update role
      await api.put(`/users/${user.uid}/role`, { role: formData.role })

      // Update collection if superadmin and collection changed
      if (isSuperadmin && formData.collectionId !== user.collectionId) {
        await api.put(`/users/${user.uid}/collection`, { collectionId: formData.collectionId })
      }

      onSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-4">Edit User</h2>
        <p className="text-sm text-gray-600 mb-4">{user.email}</p>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {isSuperadmin && <option value="superadmin">Super Admin</option>}
              <option value="collection_admin">Collection Admin</option>
              <option value="manager">Manager</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          {isSuperadmin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Collection
              </label>
              <select
                value={formData.collectionId}
                onChange={(e) => setFormData({...formData, collectionId: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">No Collection (Superadmin only)</option>
                {collections.map((collection) => (
                  <option key={collection.id} value={collection.id}>
                    {collection.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {submitting ? 'Updating...' : 'Update User'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
