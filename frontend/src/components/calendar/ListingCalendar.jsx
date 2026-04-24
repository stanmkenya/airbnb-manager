import { useState } from 'react'
import { ChevronLeft, ChevronRight, X, CalendarPlus, Lock } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency'
import Button from '../ui/Button'
import BookingForm from './BookingForm'

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

export default function ListingCalendar({
  listingId,
  listing,
  bookings = [],
  blockedDates = [],
  onBlockDate,
  onUnblockDate,
  onCreateBooking,
  canManage = false
}) {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDates, setSelectedDates] = useState([])
  const [isBlocking, setIsBlocking] = useState(false)
  const [mode, setMode] = useState('view') // 'view', 'block', 'book'
  const [showBookingForm, setShowBookingForm] = useState(false)

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()

  const firstDayOfMonth = new Date(year, month, 1)
  const lastDayOfMonth = new Date(year, month + 1, 0)
  const startingDayOfWeek = firstDayOfMonth.getDay()
  const daysInMonth = lastDayOfMonth.getDate()

  const previousMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1))
  }

  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1))
  }

  const formatDateKey = (date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const isDateBooked = (date) => {
    const dateKey = formatDateKey(date)
    return bookings.some(booking => {
      const checkIn = new Date(booking.checkIn)
      const checkOut = new Date(booking.checkOut)
      const currentDate = new Date(dateKey)
      return currentDate >= checkIn && currentDate < checkOut
    })
  }

  const isDateBlocked = (date) => {
    const dateKey = formatDateKey(date)
    return blockedDates.some(blocked => blocked.date === dateKey)
  }

  const isDateSelected = (date) => {
    const dateKey = formatDateKey(date)
    return selectedDates.includes(dateKey)
  }

  const getBookingForDate = (date) => {
    const dateKey = formatDateKey(date)
    return bookings.find(booking => {
      const checkIn = new Date(booking.checkIn)
      const checkOut = new Date(booking.checkOut)
      const currentDate = new Date(dateKey)
      return currentDate >= checkIn && currentDate < checkOut
    })
  }

  const handleDateClick = (day) => {
    if (!canManage || mode === 'view') return

    const date = new Date(year, month, day)
    const dateKey = formatDateKey(date)

    // Can't select booked dates
    if (isDateBooked(date)) return

    // For booking mode, can't select blocked dates
    if (mode === 'book' && isDateBlocked(date)) return

    setSelectedDates(prev => {
      if (prev.includes(dateKey)) {
        return prev.filter(d => d !== dateKey)
      } else {
        return [...prev, dateKey]
      }
    })
  }

  const handleCreateBooking = async (bookingData) => {
    if (!onCreateBooking) return

    setIsBlocking(true)
    try {
      await onCreateBooking(bookingData)
      setSelectedDates([])
      setShowBookingForm(false)
      setMode('view')
    } catch (error) {
      console.error('Error creating booking:', error)
    } finally {
      setIsBlocking(false)
    }
  }

  const handleCancelBooking = () => {
    setShowBookingForm(false)
    setSelectedDates([])
  }

  const handleBlockDates = async () => {
    if (selectedDates.length === 0 || !onBlockDate) return

    setIsBlocking(true)
    try {
      await Promise.all(selectedDates.map(date => onBlockDate(date)))
      setSelectedDates([])
    } catch (error) {
      console.error('Error blocking dates:', error)
    } finally {
      setIsBlocking(false)
    }
  }

  const handleUnblockDates = async () => {
    if (selectedDates.length === 0 || !onUnblockDate) return

    setIsBlocking(true)
    try {
      await Promise.all(selectedDates.map(date => onUnblockDate(date)))
      setSelectedDates([])
    } catch (error) {
      console.error('Error unblocking dates:', error)
    } finally {
      setIsBlocking(false)
    }
  }

  const renderCalendarDays = () => {
    const days = []

    // Empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(
        <div key={`empty-${i}`} className="aspect-square p-2"></div>
      )
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day)
      const isToday = formatDateKey(new Date()) === formatDateKey(date)
      const isBooked = isDateBooked(date)
      const isBlocked = isDateBlocked(date)
      const isSelected = isDateSelected(date)
      const isPast = date < new Date(new Date().setHours(0, 0, 0, 0))
      const booking = getBookingForDate(date)

      let bgColor = 'bg-white hover:bg-gray-50'
      let textColor = 'text-gray-900'
      let cursor = canManage ? 'cursor-pointer' : 'cursor-default'
      let border = 'border border-gray-200'

      if (isPast) {
        bgColor = 'bg-gray-50'
        textColor = 'text-gray-400'
        cursor = 'cursor-not-allowed'
      } else if (isBooked) {
        bgColor = 'bg-green-100'
        textColor = 'text-green-900'
        cursor = 'cursor-default'
      } else if (isBlocked) {
        bgColor = 'bg-red-100'
        textColor = 'text-red-900'
      } else if (isSelected) {
        bgColor = 'bg-primary-100'
        textColor = 'text-primary-900'
        border = 'border-2 border-primary-500'
      }

      if (isToday && !isBooked && !isBlocked) {
        border = 'border-2 border-blue-500'
      }

      days.push(
        <div
          key={day}
          onClick={() => !isPast && handleDateClick(day)}
          className={`aspect-square p-2 rounded-lg ${bgColor} ${border} ${cursor} transition-colors relative group`}
          title={
            isBooked
              ? `Booked: ${booking?.guestName || 'Guest'}`
              : isBlocked
              ? 'Blocked by manager'
              : formatDateKey(date)
          }
        >
          <div className="flex flex-col h-full">
            <span className={`text-sm font-medium ${textColor}`}>{day}</span>
            {isBooked && booking && (
              <div className="mt-1 text-xs text-green-700 truncate">
                {booking.guestName}
              </div>
            )}
            {isBlocked && (
              <div className="mt-1 text-xs text-red-700">
                <X size={12} className="inline" />
              </div>
            )}
          </div>
        </div>
      )
    }

    return days
  }

  const allSelectedAreBlocked = selectedDates.every(dateKey => {
    const [year, month, day] = dateKey.split('-')
    const date = new Date(year, parseInt(month) - 1, day)
    return isDateBlocked(date)
  })

  return (
    <div className="bg-white rounded-lg">
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          {MONTHS[month]} {year}
        </h3>
        <div className="flex gap-2">
          <button
            onClick={previousMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            onClick={nextMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-100 border border-green-200 rounded"></div>
          <span className="text-gray-600">Booked</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-100 border border-red-200 rounded"></div>
          <span className="text-gray-600">Blocked</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-white border-2 border-blue-500 rounded"></div>
          <span className="text-gray-600">Today</span>
        </div>
        {canManage && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-primary-100 border-2 border-primary-500 rounded"></div>
            <span className="text-gray-600">Selected</span>
          </div>
        )}
      </div>

      {/* Day Headers */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {DAYS.map(day => (
          <div key={day} className="text-center text-sm font-medium text-gray-600 py-2">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-2 mb-4">
        {renderCalendarDays()}
      </div>

      {/* Mode Selection */}
      {canManage && mode === 'view' && (
        <div className="flex gap-2 pt-4 border-t border-gray-200">
          <Button
            onClick={() => setMode('book')}
            variant="outline"
            className="flex-1"
          >
            <CalendarPlus size={18} className="mr-2" />
            Create Booking
          </Button>
          <Button
            onClick={() => setMode('block')}
            variant="outline"
            className="flex-1"
          >
            <Lock size={18} className="mr-2" />
            Block Dates
          </Button>
        </div>
      )}

      {/* Blocking Mode Actions */}
      {canManage && mode === 'block' && (
        <div className="pt-4 border-t border-gray-200 space-y-3">
          <p className="text-sm text-gray-600 text-center">
            Select dates to block them from bookings
          </p>
          {selectedDates.length > 0 ? (
            <div className="flex gap-2">
              <Button
                onClick={handleUnblockDates}
                disabled={isBlocking || !allSelectedAreBlocked}
                variant="ghost"
                className="flex-1"
              >
                Unblock {selectedDates.length} date{selectedDates.length > 1 ? 's' : ''}
              </Button>
              <Button
                onClick={handleBlockDates}
                disabled={isBlocking || allSelectedAreBlocked}
                className="flex-1"
              >
                {isBlocking ? 'Blocking...' : `Block ${selectedDates.length} date${selectedDates.length > 1 ? 's' : ''}`}
              </Button>
            </div>
          ) : (
            <Button
              onClick={() => setMode('view')}
              variant="ghost"
              className="w-full"
            >
              Cancel
            </Button>
          )}
        </div>
      )}

      {/* Booking Mode Actions */}
      {canManage && mode === 'book' && (
        <div className="pt-4 border-t border-gray-200 space-y-3">
          {!showBookingForm ? (
            <>
              <p className="text-sm text-gray-600 text-center">
                Select dates for the guest's stay
              </p>
              {selectedDates.length > 0 ? (
                <div className="flex gap-2">
                  <Button
                    onClick={() => setMode('view')}
                    variant="ghost"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => setShowBookingForm(true)}
                    className="flex-1"
                  >
                    Continue ({selectedDates.length} night{selectedDates.length > 1 ? 's' : ''})
                  </Button>
                </div>
              ) : (
                <Button
                  onClick={() => setMode('view')}
                  variant="ghost"
                  className="w-full"
                >
                  Cancel
                </Button>
              )}
            </>
          ) : (
            <BookingForm
              selectedDates={selectedDates}
              onSubmit={handleCreateBooking}
              onCancel={handleCancelBooking}
              isLoading={isBlocking}
              defaultRate={listing?.defaultRate}
            />
          )}
        </div>
      )}
    </div>
  )
}
