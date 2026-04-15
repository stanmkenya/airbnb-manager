import { useState } from 'react'
import { Plus, Edit, Trash2, Filter, Users } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useListings } from '../hooks/useListings'
import { useBookings, useCreateBooking, useUpdateBooking, useDeleteBooking } from '../hooks/useIncome'
import { isManagerOrAdmin } from '../utils/roleGuard'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate, getCurrentMonth } from '../utils/dateHelpers'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Table from '../components/ui/Table'
import BookingForm from '../components/forms/BookingForm'

const PLATFORMS = ['Airbnb', 'Booking.com', 'Direct', 'VRBO', 'Other']

export default function Income() {
  const { userProfile } = useAuth()
  const { data: listings } = useListings()

  const [filters, setFilters] = useState({
    listingId: '',
    platform: '',
    ...getCurrentMonth(),
  })

  const { data: bookings, isLoading } = useBookings(filters)
  const createBooking = useCreateBooking()
  const updateBooking = useUpdateBooking()
  const deleteBooking = useDeleteBooking()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingBooking, setEditingBooking] = useState(null)
  const [showFilters, setShowFilters] = useState(false)

  const canManageBookings = isManagerOrAdmin(userProfile)

  const handleCreate = () => {
    setEditingBooking(null)
    setIsModalOpen(true)
  }

  const handleEdit = (booking) => {
    setEditingBooking(booking)
    setIsModalOpen(true)
  }

  const handleSubmit = async (data) => {
    try {
      if (editingBooking) {
        await updateBooking.mutateAsync({
          id: editingBooking.id,
          listingId: editingBooking.listingId,
          data,
        })
      } else {
        await createBooking.mutateAsync(data)
      }
      setIsModalOpen(false)
      setEditingBooking(null)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleDelete = async (booking) => {
    if (window.confirm('Are you sure you want to delete this booking?')) {
      try {
        await deleteBooking.mutateAsync({
          id: booking.id,
          listingId: booking.listingId,
        })
      } catch (error) {
        // Error handled by mutation
      }
    }
  }

  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const clearFilters = () => {
    setFilters({
      listingId: '',
      platform: '',
      ...getCurrentMonth(),
    })
  }

  // Calculate totals
  const totalRevenue = bookings?.reduce((sum, b) => sum + (b.totalPaid || 0), 0) || 0
  const totalCommission = bookings?.reduce((sum, b) => sum + (b.commissionPaid || 0), 0) || 0
  const totalNetIncome = bookings?.reduce((sum, b) => sum + (b.netIncome || 0), 0) || 0

  const columns = [
    {
      header: 'Check-In',
      accessor: 'checkIn',
      render: (value) => formatDate(value),
    },
    {
      header: 'Guest',
      accessor: 'guestName',
    },
    {
      header: 'Listing',
      accessor: 'listingId',
      render: (value) => {
        const listing = listings?.find((l) => l.id === value)
        return listing?.name || 'Unknown'
      },
    },
    {
      header: 'Nights',
      accessor: 'nights',
    },
    {
      header: 'Platform',
      accessor: 'platform',
      render: (value) => (
        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
          {value}
        </span>
      ),
    },
    {
      header: 'Total Paid',
      accessor: 'totalPaid',
      render: (value) => formatCurrency(value),
    },
    {
      header: 'Commission',
      accessor: 'commissionPaid',
      render: (value) => formatCurrency(value),
    },
    {
      header: 'Net Income',
      accessor: 'netIncome',
      render: (value) => (
        <span className="font-semibold text-green-600">
          {formatCurrency(value)}
        </span>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      render: (_, booking) => (
        <div className="flex gap-2">
          {canManageBookings && (
            <>
              <button
                onClick={() => handleEdit(booking)}
                className="text-primary-600 hover:text-primary-700"
              >
                <Edit size={16} />
              </button>
              <button
                onClick={() => handleDelete(booking)}
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 size={16} />
              </button>
            </>
          )}
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Income & Bookings</h1>
          <p className="text-gray-600 mt-1">Track your bookings and revenue</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowFilters(!showFilters)}>
            <Filter size={20} className="mr-2" />
            Filters
          </Button>
          {canManageBookings && (
            <Button onClick={handleCreate}>
              <Plus size={20} className="mr-2" />
              Add Booking
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Listing
              </label>
              <select
                name="listingId"
                value={filters.listingId}
                onChange={handleFilterChange}
                className="input-field"
              >
                <option value="">All Listings</option>
                {listings?.map((listing) => (
                  <option key={listing.id} value={listing.id}>
                    {listing.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Platform
              </label>
              <select
                name="platform"
                value={filters.platform}
                onChange={handleFilterChange}
                className="input-field"
              >
                <option value="">All Platforms</option>
                {PLATFORMS.map((platform) => (
                  <option key={platform} value={platform}>
                    {platform}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                From Date
              </label>
              <input
                type="date"
                name="from"
                value={filters.from}
                onChange={handleFilterChange}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To Date
              </label>
              <input
                type="date"
                name="to"
                value={filters.to}
                onChange={handleFilterChange}
                className="input-field"
              />
            </div>
          </div>
          <div className="mt-4">
            <Button variant="secondary" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalRevenue)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Commission Paid</p>
          <p className="text-2xl font-bold text-orange-600">{formatCurrency(totalCommission)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Net Income</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalNetIncome)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Bookings</p>
          <p className="text-2xl font-bold text-gray-900">{bookings?.length || 0}</p>
        </div>
      </div>

      {/* Bookings Table */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <Table
            columns={columns}
            data={bookings || []}
            emptyMessage="No bookings found. Try adjusting your filters or add a new booking."
          />
        )}
      </div>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setEditingBooking(null)
        }}
        title={editingBooking ? 'Edit Booking' : 'Add New Booking'}
        size="lg"
      >
        <BookingForm
          initialData={editingBooking}
          onSubmit={handleSubmit}
          onCancel={() => {
            setIsModalOpen(false)
            setEditingBooking(null)
          }}
          isLoading={createBooking.isPending || updateBooking.isPending}
        />
      </Modal>
    </div>
  )
}
