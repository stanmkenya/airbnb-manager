import { useState, useMemo } from 'react'
import { Search, Users, Mail, Phone, Calendar } from 'lucide-react'
import { useBookings } from '../hooks/useIncome'
import { useListings } from '../hooks/useListings'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate } from '../utils/dateHelpers'
import Table from '../components/ui/Table'

export default function GuestDirectory() {
  const { data: bookings, isLoading } = useBookings({})
  const { data: listings } = useListings()
  const [searchQuery, setSearchQuery] = useState('')

  // Aggregate guests from bookings
  const guests = useMemo(() => {
    if (!bookings) return []

    const guestMap = new Map()

    bookings.forEach((booking) => {
      const key = booking.guestEmail || booking.guestName

      if (!guestMap.has(key)) {
        guestMap.set(key, {
          name: booking.guestName,
          email: booking.guestEmail,
          phone: booking.guestPhone,
          bookings: [],
          totalBookings: 0,
          totalRevenue: 0,
        })
      }

      const guest = guestMap.get(key)
      guest.bookings.push(booking)
      guest.totalBookings++
      guest.totalRevenue += booking.netIncome || 0
    })

    return Array.from(guestMap.values()).sort((a, b) => b.totalBookings - a.totalBookings)
  }, [bookings])

  // Filter guests by search query
  const filteredGuests = useMemo(() => {
    if (!searchQuery.trim()) return guests

    const query = searchQuery.toLowerCase()
    return guests.filter(
      (guest) =>
        guest.name?.toLowerCase().includes(query) ||
        guest.email?.toLowerCase().includes(query) ||
        guest.phone?.toLowerCase().includes(query)
    )
  }, [guests, searchQuery])

  const columns = [
    {
      header: 'Guest Name',
      accessor: 'name',
      render: (value) => (
        <div className="flex items-center">
          <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold mr-3">
            {value?.[0]?.toUpperCase() || '?'}
          </div>
          <span className="font-medium text-gray-900">{value || 'Unknown'}</span>
        </div>
      ),
    },
    {
      header: 'Contact',
      accessor: 'email',
      render: (value, guest) => (
        <div className="space-y-1">
          {value && (
            <div className="flex items-center text-sm text-gray-600">
              <Mail size={14} className="mr-2" />
              {value}
            </div>
          )}
          {guest.phone && (
            <div className="flex items-center text-sm text-gray-600">
              <Phone size={14} className="mr-2" />
              {guest.phone}
            </div>
          )}
        </div>
      ),
    },
    {
      header: 'Total Bookings',
      accessor: 'totalBookings',
      render: (value) => (
        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
          {value} booking{value !== 1 ? 's' : ''}
        </span>
      ),
    },
    {
      header: 'Total Revenue',
      accessor: 'totalRevenue',
      render: (value) => (
        <span className="font-semibold text-green-600">{formatCurrency(value)}</span>
      ),
    },
    {
      header: 'Last Booking',
      accessor: 'bookings',
      render: (bookings) => {
        const lastBooking = bookings.sort((a, b) => b.checkIn.localeCompare(a.checkIn))[0]
        return (
          <div className="text-sm text-gray-600">
            <div>{formatDate(lastBooking.checkIn)}</div>
            <div className="text-xs text-gray-500">
              {listings?.find((l) => l.id === lastBooking.listingId)?.name || 'Unknown listing'}
            </div>
          </div>
        )
      },
    },
  ]

  // Expandable row details
  const [expandedGuestEmail, setExpandedGuestEmail] = useState(null)

  const handleRowClick = (guest) => {
    const key = guest.email || guest.name
    setExpandedGuestEmail(expandedGuestEmail === key ? null : key)
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Guest Directory</h1>
        <p className="text-gray-600 mt-1">View all your guests and their booking history</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Guests</p>
              <p className="text-2xl font-bold text-gray-900">{guests.length}</p>
            </div>
            <Users size={40} className="text-primary-600 opacity-50" />
          </div>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Bookings</p>
          <p className="text-2xl font-bold text-gray-900">
            {guests.reduce((sum, g) => sum + g.totalBookings, 0)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Revenue from Guests</p>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(guests.reduce((sum, g) => sum + g.totalRevenue, 0))}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="card mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search guests by name, email, or phone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-10"
          />
        </div>
      </div>

      {/* Guests Table */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <>
            <Table
              columns={columns}
              data={filteredGuests}
              emptyMessage="No guests found."
              onRowClick={handleRowClick}
            />

            {/* Expanded Booking History */}
            {filteredGuests.map((guest) => {
              const key = guest.email || guest.name
              if (expandedGuestEmail !== key) return null

              return (
                <div key={key} className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Calendar size={20} className="mr-2" />
                    Booking History for {guest.name}
                  </h3>
                  <div className="space-y-3">
                    {guest.bookings
                      .sort((a, b) => b.checkIn.localeCompare(a.checkIn))
                      .map((booking) => (
                        <div
                          key={booking.id}
                          className="bg-white p-3 rounded border border-gray-200 flex items-center justify-between"
                        >
                          <div>
                            <div className="font-medium text-gray-900">
                              {listings?.find((l) => l.id === booking.listingId)?.name || 'Unknown listing'}
                            </div>
                            <div className="text-sm text-gray-600">
                              {formatDate(booking.checkIn)} - {formatDate(booking.checkOut)}
                              {' · '}
                              {booking.nights} night{booking.nights !== 1 ? 's' : ''}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold text-green-600">
                              {formatCurrency(booking.netIncome)}
                            </div>
                            <div className="text-xs text-gray-500">{booking.platform}</div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )
            })}
          </>
        )}
      </div>
    </div>
  )
}
