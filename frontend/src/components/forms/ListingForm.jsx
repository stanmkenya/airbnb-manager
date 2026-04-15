import { useState, useEffect } from 'react'
import Input from '../ui/Input'
import Button from '../ui/Button'

export default function ListingForm({ initialData, onSubmit, onCancel, isLoading }) {
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    airbnbUrl: '',
    defaultRate: '',
    bedrooms: '',
    bathrooms: '',
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        address: initialData.address || '',
        airbnbUrl: initialData.airbnbUrl || '',
        defaultRate: initialData.defaultRate || '',
        bedrooms: initialData.bedrooms || '',
        bathrooms: initialData.bathrooms || '',
      })
    }
  }, [initialData])

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

    if (!formData.name.trim()) {
      newErrors.name = 'Listing name is required'
    }

    if (!formData.address.trim()) {
      newErrors.address = 'Address is required'
    }

    if (!formData.defaultRate || formData.defaultRate <= 0) {
      newErrors.defaultRate = 'Default rate must be greater than 0'
    }

    if (!formData.bedrooms || formData.bedrooms < 0) {
      newErrors.bedrooms = 'Number of bedrooms is required'
    }

    if (!formData.bathrooms || formData.bathrooms < 0) {
      newErrors.bathrooms = 'Number of bathrooms is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Convert numbers
    const submitData = {
      ...formData,
      defaultRate: parseFloat(formData.defaultRate),
      bedrooms: parseInt(formData.bedrooms),
      bathrooms: parseInt(formData.bathrooms),
    }

    onSubmit(submitData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Listing Name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          error={errors.name}
          placeholder="e.g., Beachfront Villa Unit 4"
          required
        />

        <Input
          label="Default Nightly Rate"
          name="defaultRate"
          type="number"
          step="0.01"
          min="0"
          value={formData.defaultRate}
          onChange={handleChange}
          error={errors.defaultRate}
          placeholder="100.00"
          required
        />
      </div>

      <Input
        label="Address"
        name="address"
        value={formData.address}
        onChange={handleChange}
        error={errors.address}
        placeholder="Full property address"
        required
      />

      <Input
        label="Airbnb URL"
        name="airbnbUrl"
        type="url"
        value={formData.airbnbUrl}
        onChange={handleChange}
        error={errors.airbnbUrl}
        placeholder="https://www.airbnb.com/rooms/..."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Bedrooms"
          name="bedrooms"
          type="number"
          min="0"
          value={formData.bedrooms}
          onChange={handleChange}
          error={errors.bedrooms}
          placeholder="2"
          required
        />

        <Input
          label="Bathrooms"
          name="bathrooms"
          type="number"
          min="0"
          step="0.5"
          value={formData.bathrooms}
          onChange={handleChange}
          error={errors.bathrooms}
          placeholder="1.5"
          required
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isLoading}>
          {initialData ? 'Update Listing' : 'Create Listing'}
        </Button>
      </div>
    </form>
  )
}
