import { useState, useEffect } from 'react'
import Input from '../ui/Input'
import Button from '../ui/Button'
import { useListings } from '../../hooks/useListings'
import { calculateNights, getTodayString } from '../../utils/dateHelpers'
import { formatCurrency } from '../../utils/formatCurrency'

const PLATFORMS = ['Airbnb', 'Booking.com', 'Direct', 'VRBO', 'Other']

export default function BookingForm({ initialData, onSubmit, onCancel, isLoading }) {
  const { data: listings } = useListings()

  const [formData, setFormData] = useState({
    listingId: '',
    guestName: '',
    guestEmail: '',
    guestPhone: '',
    checkIn: '',
    checkOut: '',
    nightlyRate: '',
    totalPaid: '',
    platform: 'Airbnb',
    commissionPaid: '0',
    notes: '',
  })

  const [errors, setErrors] = useState({})
  const [nights, setNights] = useState(0)
  const [netIncome, setNetIncome] = useState(0)

  useEffect(() => {
    if (initialData) {
      setFormData({
        listingId: initialData.listingId || '',
        guestName: initialData.guestName || '',
        guestEmail: initialData.guestEmail || '',
        guestPhone: initialData.guestPhone || '',
        checkIn: initialData.checkIn || '',
        checkOut: initialData.checkOut || '',
        nightlyRate: initialData.nightlyRate || '',
        totalPaid: initialData.totalPaid || '',
        platform: initialData.platform || 'Airbnb',
        commissionPaid: initialData.commissionPaid || '0',
        notes: initialData.notes || '',
      })
    }
  }, [initialData])

  // Auto-calculate nights when check-in/out changes
  useEffect(() => {
    if (formData.checkIn && formData.checkOut) {
      const calculatedNights = calculateNights(formData.checkIn, formData.checkOut)
      setNights(calculatedNights)

      // Auto-calculate total if nightly rate is set and totalPaid is not manually set
      if (formData.nightlyRate && !formData.totalPaid) {
        const autoTotal = calculatedNights * parseFloat(formData.nightlyRate)
        setFormData((prev) => ({
          ...prev,
          totalPaid: autoTotal.toString(),
        }))
      }
    }
  }, [formData.checkIn, formData.checkOut, formData.nightlyRate])

  // Calculate net income
  useEffect(() => {
    const total = parseFloat(formData.totalPaid) || 0
    const commission = parseFloat(formData.commissionPaid) || 0
    setNetIncome(total - commission)
  }, [formData.totalPaid, formData.commissionPaid])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: null,
      }))
    }
  }

  const validate = () => {
    const newErrors = {}

    if (!formData.listingId) {
      newErrors.listingId = 'Listing is required'
    }

    if (!formData.guestName.trim()) {
      newErrors.guestName = 'Guest name is required'
    }

    if (!formData.checkIn) {
      newErrors.checkIn = 'Check-in date is required'
    }

    if (!formData.checkOut) {
      newErrors.checkOut = 'Check-out date is required'
    }

    if (formData.checkIn && formData.checkOut && formData.checkIn >= formData.checkOut) {
      newErrors.checkOut = 'Check-out must be after check-in'
    }

    if (!formData.nightlyRate || formData.nightlyRate <= 0) {
      newErrors.nightlyRate = 'Nightly rate must be greater than 0'
    }

    if (!formData.platform) {
      newErrors.platform = 'Platform is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Prepare submit data
    const submitData = {
      ...formData,
      nightlyRate: parseFloat(formData.nightlyRate),
      totalPaid: formData.totalPaid ? parseFloat(formData.totalPaid) : null,
      commissionPaid: parseFloat(formData.commissionPaid),
      guestEmail: formData.guestEmail || null,
      guestPhone: formData.guestPhone || null,
      notes: formData.notes || null,
    }

    onSubmit(submitData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="listingId" className="block text-sm font-medium text-gray-700 mb-1">
            Listing <span className="text-red-500">*</span>
          </label>
          <select
            id="listingId"
            name="listingId"
            value={formData.listingId}
            onChange={handleChange}
            className="input-field"
            required
            disabled={!!initialData?.listingId}
          >
            <option value="">Select a listing</option>
            {listings?.map((listing) => (
              <option key={listing.id} value={listing.id}>
                {listing.name}
              </option>
            ))}
          </select>
          {errors.listingId && (
            <p className="mt-1 text-sm text-red-600">{errors.listingId}</p>
          )}
        </div>

        <div>
          <label htmlFor="platform" className="block text-sm font-medium text-gray-700 mb-1">
            Platform <span className="text-red-500">*</span>
          </label>
          <select
            id="platform"
            name="platform"
            value={formData.platform}
            onChange={handleChange}
            className="input-field"
            required
          >
            {PLATFORMS.map((platform) => (
              <option key={platform} value={platform}>
                {platform}
              </option>
            ))}
          </select>
          {errors.platform && (
            <p className="mt-1 text-sm text-red-600">{errors.platform}</p>
          )}
        </div>
      </div>

      <Input
        label="Guest Name"
        name="guestName"
        value={formData.guestName}
        onChange={handleChange}
        error={errors.guestName}
        placeholder="John Doe"
        required
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Guest Email"
          name="guestEmail"
          type="email"
          value={formData.guestEmail}
          onChange={handleChange}
          placeholder="guest@example.com"
        />

        <Input
          label="Guest Phone"
          name="guestPhone"
          type="tel"
          value={formData.guestPhone}
          onChange={handleChange}
          placeholder="+1234567890"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Check-In Date"
          name="checkIn"
          type="date"
          value={formData.checkIn}
          onChange={handleChange}
          error={errors.checkIn}
          required
        />

        <Input
          label="Check-Out Date"
          name="checkOut"
          type="date"
          value={formData.checkOut}
          onChange={handleChange}
          error={errors.checkOut}
          required
        />
      </div>

      {nights > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Nights:</strong> {nights}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Nightly Rate"
          name="nightlyRate"
          type="number"
          step="0.01"
          min="0"
          value={formData.nightlyRate}
          onChange={handleChange}
          error={errors.nightlyRate}
          placeholder="100.00"
          required
        />

        <Input
          label="Total Paid (auto-calculated)"
          name="totalPaid"
          type="number"
          step="0.01"
          min="0"
          value={formData.totalPaid}
          onChange={handleChange}
          placeholder="Auto-calculated from nights × rate"
          helperText="Leave blank to auto-calculate"
        />
      </div>

      <Input
        label="Commission Paid"
        name="commissionPaid"
        type="number"
        step="0.01"
        min="0"
        value={formData.commissionPaid}
        onChange={handleChange}
        placeholder="0.00"
        helperText="Platform commission/fee"
      />

      {formData.totalPaid && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <p className="text-sm text-green-800">
            <strong>Net Income:</strong> {formatCurrency(netIncome)}
          </p>
        </div>
      )}

      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows="3"
          className="input-field"
          placeholder="Additional details about this booking..."
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isLoading}>
          {initialData ? 'Update Booking' : 'Add Booking'}
        </Button>
      </div>
    </form>
  )
}
