import { useState } from 'react'
import Input from '../ui/Input'
import Button from '../ui/Button'
import { useListings } from '../../hooks/useListings'

const ROLES = [
  { value: 'admin', label: 'Admin', description: 'Full access to all features' },
  { value: 'manager', label: 'Property Manager', description: 'Manage assigned listings' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to assigned listings' },
]

export default function UserInviteForm({ onSubmit, onCancel, isLoading }) {
  const { data: listings } = useListings()

  const [formData, setFormData] = useState({
    email: '',
    displayName: '',
    role: 'viewer',
    assignedListings: {},
  })

  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))

    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: null,
      }))
    }
  }

  const handleListingToggle = (listingId) => {
    setFormData((prev) => ({
      ...prev,
      assignedListings: {
        ...prev.assignedListings,
        [listingId]: !prev.assignedListings[listingId],
      },
    }))
  }

  const validate = () => {
    const newErrors = {}

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email address'
    }

    if (!formData.displayName.trim()) {
      newErrors.displayName = 'Display name is required'
    }

    if (!formData.role) {
      newErrors.role = 'Role is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Filter only selected listings
    const selectedListings = {}
    Object.keys(formData.assignedListings).forEach((key) => {
      if (formData.assignedListings[key]) {
        selectedListings[key] = true
      }
    })

    const submitData = {
      ...formData,
      assignedListings: selectedListings,
    }

    onSubmit(submitData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Email Address"
        name="email"
        type="email"
        value={formData.email}
        onChange={handleChange}
        error={errors.email}
        placeholder="user@example.com"
        required
      />

      <Input
        label="Display Name"
        name="displayName"
        value={formData.displayName}
        onChange={handleChange}
        error={errors.displayName}
        placeholder="John Doe"
        required
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Role <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          {ROLES.map((role) => (
            <label key={role.value} className="flex items-start">
              <input
                type="radio"
                name="role"
                value={role.value}
                checked={formData.role === role.value}
                onChange={handleChange}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">{role.label}</div>
                <div className="text-sm text-gray-500">{role.description}</div>
              </div>
            </label>
          ))}
        </div>
        {errors.role && (
          <p className="mt-1 text-sm text-red-600">{errors.role}</p>
        )}
      </div>

      {formData.role !== 'admin' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Assign Listings
          </label>
          <div className="border border-gray-300 rounded-lg p-4 max-h-48 overflow-y-auto space-y-2">
            {listings && listings.length > 0 ? (
              listings.map((listing) => (
                <label key={listing.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={!!formData.assignedListings[listing.id]}
                    onChange={() => handleListingToggle(listing.id)}
                    className="mr-3"
                  />
                  <span className="text-gray-900">{listing.name}</span>
                </label>
              ))
            ) : (
              <p className="text-sm text-gray-500">No listings available</p>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Select the listings this user can access
          </p>
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          A temporary password will be generated and shown. The user should reset their password after first login.
        </p>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isLoading}>
          Invite User
        </Button>
      </div>
    </form>
  )
}
