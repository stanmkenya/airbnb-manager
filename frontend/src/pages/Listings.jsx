import { useState } from 'react'
import { Plus, Edit, Trash2, Home, MapPin, DollarSign, Bed } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useListings, useCreateListing, useUpdateListing, useDeleteListing } from '../hooks/useListings'
import { isAdmin } from '../utils/roleGuard'
import { formatCurrency } from '../utils/formatCurrency'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import ListingForm from '../components/forms/ListingForm'

export default function Listings() {
  const { userProfile } = useAuth()
  const { data: listings, isLoading } = useListings()
  const createListing = useCreateListing()
  const updateListing = useUpdateListing()
  const deleteListing = useDeleteListing()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingListing, setEditingListing] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  const canManageListings = isAdmin(userProfile)

  const handleCreate = () => {
    setEditingListing(null)
    setIsModalOpen(true)
  }

  const handleEdit = (listing) => {
    setEditingListing(listing)
    setIsModalOpen(true)
  }

  const handleSubmit = async (data) => {
    try {
      if (editingListing) {
        await updateListing.mutateAsync({ id: editingListing.id, data })
      } else {
        await createListing.mutateAsync(data)
      }
      setIsModalOpen(false)
      setEditingListing(null)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this listing? This action cannot be undone.')) {
      setDeletingId(id)
      try {
        await deleteListing.mutateAsync(id)
      } catch (error) {
        // Error handled by mutation
      } finally {
        setDeletingId(null)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Listings</h1>
          <p className="text-gray-600 mt-1">Manage your properties</p>
        </div>
        {canManageListings && (
          <Button onClick={handleCreate}>
            <Plus size={20} className="mr-2" />
            Add Listing
          </Button>
        )}
      </div>

      {!listings || listings.length === 0 ? (
        <div className="card text-center py-12">
          <Home size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500 mb-4">No listings yet.</p>
          {canManageListings && (
            <Button onClick={handleCreate}>
              <Plus size={20} className="mr-2" />
              Add Your First Property
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((listing) => (
            <div key={listing.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {listing.name}
                  </h3>
                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <MapPin size={14} className="mr-1" />
                    {listing.address}
                  </div>
                </div>
                {listing.status === 'active' ? (
                  <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                    Active
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                    Inactive
                  </span>
                )}
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-700">
                  <DollarSign size={16} className="mr-2 text-gray-400" />
                  <span className="font-medium">
                    {formatCurrency(listing.defaultRate)} / night
                  </span>
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <Bed size={16} className="mr-2 text-gray-400" />
                  <span>
                    {listing.bedrooms} bed · {listing.bathrooms} bath
                  </span>
                </div>
              </div>

              {listing.airbnbUrl && (
                <a
                  href={listing.airbnbUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary-600 hover:text-primary-700 mb-4 block"
                >
                  View on Airbnb →
                </a>
              )}

              {canManageListings && (
                <div className="flex gap-2 pt-4 border-t border-gray-200">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(listing)}
                    className="flex-1"
                  >
                    <Edit size={16} className="mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(listing.id)}
                    disabled={deletingId === listing.id}
                    className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    {deletingId === listing.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600" />
                    ) : (
                      <>
                        <Trash2 size={16} className="mr-1" />
                        Delete
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setEditingListing(null)
        }}
        title={editingListing ? 'Edit Listing' : 'Add New Listing'}
        size="lg"
      >
        <ListingForm
          initialData={editingListing}
          onSubmit={handleSubmit}
          onCancel={() => {
            setIsModalOpen(false)
            setEditingListing(null)
          }}
          isLoading={createListing.isPending || updateListing.isPending}
        />
      </Modal>
    </div>
  )
}
