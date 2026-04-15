import { useState } from 'react'
import { Plus, Edit, UserX, UserCheck, Shield } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useUsers, useInviteUser, useUpdateUserRole, useUpdateUserListings, useDeactivateUser, useActivateUser } from '../hooks/useUsers'
import { useListings } from '../hooks/useListings'
import { isAdmin } from '../utils/roleGuard'
import { formatDate } from '../utils/dateHelpers'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Table from '../components/ui/Table'
import UserInviteForm from '../components/forms/UserInviteForm'

export default function Admin() {
  const { userProfile } = useAuth()
  const { data: users, isLoading } = useUsers()
  const { data: listings } = useListings()
  const inviteUser = useInviteUser()
  const updateRole = useUpdateUserRole()
  const updateListings = useUpdateUserListings()
  const deactivateUser = useDeactivateUser()
  const activateUser = useActivateUser()

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [tempPassword, setTempPassword] = useState(null)

  // Redirect if not admin
  if (!isAdmin(userProfile)) {
    return (
      <div className="card text-center py-12">
        <Shield size={48} className="mx-auto text-gray-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
        <p className="text-gray-600">You need admin privileges to access this page.</p>
      </div>
    )
  }

  const handleInvite = async (data) => {
    try {
      const result = await inviteUser.mutateAsync(data)
      setTempPassword(result.tempPassword)
      setIsInviteModalOpen(false)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleEditUser = (user) => {
    setEditingUser(user)
    setIsEditModalOpen(true)
  }

  const handleUpdateRole = async (uid, newRole) => {
    try {
      await updateRole.mutateAsync({ uid, role: newRole })
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleToggleListing = async (user, listingId) => {
    const currentListings = user.assignedListings || {}
    const newListings = {
      ...currentListings,
      [listingId]: !currentListings[listingId],
    }

    // Filter out false values
    const filteredListings = {}
    Object.keys(newListings).forEach((key) => {
      if (newListings[key]) {
        filteredListings[key] = true
      }
    })

    try {
      await updateListings.mutateAsync({
        uid: user.uid,
        assignedListings: filteredListings,
      })
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleToggleActive = async (user) => {
    if (user.isActive) {
      if (window.confirm(`Are you sure you want to deactivate ${user.displayName || user.email}?`)) {
        try {
          await deactivateUser.mutateAsync(user.uid)
        } catch (error) {
          // Error handled by mutation
        }
      }
    } else {
      try {
        await activateUser.mutateAsync(user.uid)
      } catch (error) {
        // Error handled by mutation
      }
    }
  }

  const getRoleBadge = (role) => {
    const styles = {
      admin: 'bg-purple-100 text-purple-800',
      manager: 'bg-blue-100 text-blue-800',
      viewer: 'bg-gray-100 text-gray-800',
    }

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${styles[role]}`}>
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </span>
    )
  }

  const columns = [
    {
      header: 'User',
      accessor: 'displayName',
      render: (value, user) => (
        <div>
          <div className="font-medium text-gray-900">{value || user.email}</div>
          <div className="text-sm text-gray-500">{user.email}</div>
        </div>
      ),
    },
    {
      header: 'Role',
      accessor: 'role',
      render: (value) => getRoleBadge(value),
    },
    {
      header: 'Assigned Listings',
      accessor: 'assignedListings',
      render: (value, user) => {
        if (user.role === 'admin') {
          return <span className="text-sm text-gray-500">All listings</span>
        }
        const count = value ? Object.keys(value).filter((k) => value[k]).length : 0
        return <span className="text-sm text-gray-600">{count} listing(s)</span>
      },
    },
    {
      header: 'Status',
      accessor: 'isActive',
      render: (value) =>
        value ? (
          <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
            Active
          </span>
        ) : (
          <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
            Inactive
          </span>
        ),
    },
    {
      header: 'Created',
      accessor: 'createdAt',
      render: (value) => (value ? formatDate(new Date(value), 'MMM dd, yyyy') : '-'),
    },
    {
      header: 'Actions',
      accessor: 'uid',
      render: (_, user) => (
        <div className="flex gap-2">
          <button
            onClick={() => handleEditUser(user)}
            className="text-primary-600 hover:text-primary-700"
            title="Edit user"
          >
            <Edit size={16} />
          </button>
          {user.uid !== userProfile.uid && (
            <button
              onClick={() => handleToggleActive(user)}
              className={user.isActive ? 'text-red-600 hover:text-red-700' : 'text-green-600 hover:text-green-700'}
              title={user.isActive ? 'Deactivate user' : 'Activate user'}
            >
              {user.isActive ? <UserX size={16} /> : <UserCheck size={16} />}
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600 mt-1">Manage users, roles, and system settings</p>
        </div>
        <Button onClick={() => setIsInviteModalOpen(true)}>
          <Plus size={20} className="mr-2" />
          Invite User
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Users</p>
          <p className="text-2xl font-bold text-gray-900">{users?.length || 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Admins</p>
          <p className="text-2xl font-bold text-purple-600">
            {users?.filter((u) => u.role === 'admin').length || 0}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Managers</p>
          <p className="text-2xl font-bold text-blue-600">
            {users?.filter((u) => u.role === 'manager').length || 0}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Active Users</p>
          <p className="text-2xl font-bold text-green-600">
            {users?.filter((u) => u.isActive).length || 0}
          </p>
        </div>
      </div>

      {/* Users Table */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <Table columns={columns} data={users || []} emptyMessage="No users found." />
        )}
      </div>

      {/* Invite User Modal */}
      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        title="Invite New User"
        size="lg"
      >
        <UserInviteForm
          onSubmit={handleInvite}
          onCancel={() => setIsInviteModalOpen(false)}
          isLoading={inviteUser.isPending}
        />
      </Modal>

      {/* Temporary Password Modal */}
      {tempPassword && (
        <Modal
          isOpen={true}
          onClose={() => setTempPassword(null)}
          title="User Invited Successfully"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-gray-700">
              The user has been invited. Here is their temporary password:
            </p>
            <div className="bg-gray-100 border border-gray-300 rounded-lg p-4">
              <code className="text-lg font-mono text-gray-900">{tempPassword}</code>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                Make sure to copy this password and share it securely with the user. They should change it on first login.
              </p>
            </div>
            <div className="flex justify-end">
              <Button onClick={() => setTempPassword(null)}>Close</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false)
            setEditingUser(null)
          }}
          title={`Edit User: ${editingUser.displayName || editingUser.email}`}
          size="lg"
        >
          <div className="space-y-6">
            {/* Role Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
              <select
                value={editingUser.role}
                onChange={(e) => handleUpdateRole(editingUser.uid, e.target.value)}
                className="input-field"
                disabled={editingUser.uid === userProfile.uid}
              >
                <option value="admin">Admin</option>
                <option value="manager">Property Manager</option>
                <option value="viewer">Viewer</option>
              </select>
              {editingUser.uid === userProfile.uid && (
                <p className="mt-1 text-sm text-gray-500">You cannot change your own role</p>
              )}
            </div>

            {/* Listing Assignment */}
            {editingUser.role !== 'admin' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Assigned Listings
                </label>
                <div className="border border-gray-300 rounded-lg p-4 max-h-48 overflow-y-auto space-y-2">
                  {listings && listings.length > 0 ? (
                    listings.map((listing) => (
                      <label key={listing.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={!!(editingUser.assignedListings || {})[listing.id]}
                          onChange={() => handleToggleListing(editingUser, listing.id)}
                          className="mr-3"
                        />
                        <span className="text-gray-900">{listing.name}</span>
                      </label>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No listings available</p>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-end">
              <Button
                onClick={() => {
                  setIsEditModalOpen(false)
                  setEditingUser(null)
                }}
              >
                Done
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
