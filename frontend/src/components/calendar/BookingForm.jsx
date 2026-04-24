import { useState } from 'react'
import { X } from 'lucide-react'
import Button from '../ui/Button'
import { formatCurrency } from '../../utils/formatCurrency'

export default function BookingForm({
  selectedDates,
  onSubmit,
  onCancel,
  isLoading,
  defaultRate
}) {
  const [formData, setFormData] = useState({
    guestName: '',
    totalPaid: '',
    commissionPaid: '',
    platform: 'Airbnb',
    notes: ''
  })

  // Calculate date range
  const sortedDates = [...selectedDates].sort()
  const checkIn = sortedDates[0]
  const nights = sortedDates.length

  // Calculate check-out date (day after last night)
  const lastNight = new Date(sortedDates[sortedDates.length - 1])
  lastNight.setDate(lastNight.getDate() + 1)
  const checkOut = lastNight.toISOString().split('T')[0]

  // Calculate suggested total based on default rate
  const suggestedTotal = defaultRate ? defaultRate * nights : 0

  const handleSubmit = (e) => {
    e.preventDefault()

    const totalPaid = parseFloat(formData.totalPaid) || 0
    const commissionPaid = parseFloat(formData.commissionPaid) || 0
    const nightlyRate = nights > 0 ? totalPaid / nights : defaultRate || 0
    const netIncome = totalPaid - commissionPaid

    onSubmit({
      checkIn,
      checkOut,
      guestName: formData.guestName,
      totalPaid,
      commissionPaid,
      nightlyRate,
      platform: formData.platform,
      netIncome,
      notes: formData.notes || ''
    })
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Create Booking</h3>
        <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
          <X size={20} />
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Check-in</p>
            <p className="font-semibold text-gray-900">{checkIn}</p>
          </div>
          <div>
            <p className="text-gray-600">Check-out</p>
            <p className="font-semibold text-gray-900">{checkOut}</p>
          </div>
          <div>
            <p className="text-gray-600">Nights</p>
            <p className="font-semibold text-gray-900">{nights}</p>
          </div>
          {defaultRate && (
            <div>
              <p className="text-gray-600">Suggested Total</p>
              <p className="font-semibold text-gray-900">{formatCurrency(suggestedTotal)}</p>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="guestName" className="block text-sm font-medium text-gray-700 mb-1">
            Guest Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="guestName"
            name="guestName"
            value={formData.guestName}
            onChange={handleChange}
            className="input-field"
            placeholder="John Doe"
            required
          />
        </div>

        <div>
          <label htmlFor="totalPaid" className="block text-sm font-medium text-gray-700 mb-1">
            Total Amount Paid <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="totalPaid"
            name="totalPaid"
            value={formData.totalPaid}
            onChange={handleChange}
            className="input-field"
            placeholder={suggestedTotal ? suggestedTotal.toString() : "0.00"}
            step="0.01"
            min="0"
            required
          />
        </div>

        <div>
          <label htmlFor="commissionPaid" className="block text-sm font-medium text-gray-700 mb-1">
            Commission/Fees Paid
          </label>
          <input
            type="number"
            id="commissionPaid"
            name="commissionPaid"
            value={formData.commissionPaid}
            onChange={handleChange}
            className="input-field"
            placeholder="0.00"
            step="0.01"
            min="0"
          />
        </div>

        <div>
          <label htmlFor="platform" className="block text-sm font-medium text-gray-700 mb-1">
            Booking Platform <span className="text-red-500">*</span>
          </label>
          <select
            id="platform"
            name="platform"
            value={formData.platform}
            onChange={handleChange}
            className="input-field"
            required
          >
            <option value="Airbnb">Airbnb</option>
            <option value="Booking.com">Booking.com</option>
            <option value="VRBO">VRBO</option>
            <option value="Direct">Direct Booking</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
            Notes (Optional)
          </label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            className="input-field"
            rows="3"
            placeholder="Additional booking details..."
          />
        </div>

        <div className="flex gap-2 pt-4">
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading ? 'Creating...' : 'Create Booking'}
          </Button>
        </div>
      </form>
    </div>
  )
}
