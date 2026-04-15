import { useState, useEffect } from 'react'
import Input from '../ui/Input'
import Button from '../ui/Button'
import { useListings } from '../../hooks/useListings'
import { getAllCategories, getSubCategories } from '../../utils/expenseCategories'
import { getTodayString } from '../../utils/dateHelpers'

export default function ExpenseForm({ initialData, onSubmit, onCancel, isLoading }) {
  const { data: listings } = useListings()

  const [formData, setFormData] = useState({
    listingId: '',
    date: getTodayString(),
    category: '',
    subCategory: '',
    amount: '',
    notes: '',
    receiptRef: '',
  })

  const [errors, setErrors] = useState({})
  const [subCategories, setSubCategories] = useState([])

  useEffect(() => {
    if (initialData) {
      setFormData({
        listingId: initialData.listingId || '',
        date: initialData.date || getTodayString(),
        category: initialData.category || '',
        subCategory: initialData.subCategory || '',
        amount: initialData.amount || '',
        notes: initialData.notes || '',
        receiptRef: initialData.receiptRef || '',
      })
      if (initialData.category) {
        setSubCategories(getSubCategories(initialData.category))
      }
    }
  }, [initialData])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))

    // Update subcategories when category changes
    if (name === 'category') {
      const subs = getSubCategories(value)
      setSubCategories(subs)
      // Reset subcategory if new category is selected
      setFormData((prev) => ({
        ...prev,
        subCategory: '',
      }))
    }

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

    if (!formData.date) {
      newErrors.date = 'Date is required'
    }

    if (!formData.category) {
      newErrors.category = 'Category is required'
    }

    if (!formData.amount || formData.amount <= 0) {
      newErrors.amount = 'Amount must be greater than 0'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Convert amount to number
    const submitData = {
      ...formData,
      amount: parseFloat(formData.amount),
      subCategory: formData.subCategory || null,
      notes: formData.notes || null,
      receiptRef: formData.receiptRef || null,
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

        <Input
          label="Date"
          name="date"
          type="date"
          value={formData.date}
          onChange={handleChange}
          error={errors.date}
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
            Category <span className="text-red-500">*</span>
          </label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            className="input-field"
            required
          >
            <option value="">Select a category</option>
            {getAllCategories().map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          {errors.category && (
            <p className="mt-1 text-sm text-red-600">{errors.category}</p>
          )}
        </div>

        {subCategories.length > 0 && (
          <div>
            <label htmlFor="subCategory" className="block text-sm font-medium text-gray-700 mb-1">
              Sub-Category
            </label>
            <select
              id="subCategory"
              name="subCategory"
              value={formData.subCategory}
              onChange={handleChange}
              className="input-field"
            >
              <option value="">Select a sub-category</option>
              {subCategories.map((subCat) => (
                <option key={subCat} value={subCat}>
                  {subCat}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <Input
        label="Amount"
        name="amount"
        type="number"
        step="0.01"
        min="0"
        value={formData.amount}
        onChange={handleChange}
        error={errors.amount}
        placeholder="0.00"
        required
      />

      <Input
        label="Receipt/Invoice Reference"
        name="receiptRef"
        value={formData.receiptRef}
        onChange={handleChange}
        placeholder="INV-12345"
      />

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
          placeholder="Additional details about this expense..."
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isLoading}>
          {initialData ? 'Update Expense' : 'Add Expense'}
        </Button>
      </div>
    </form>
  )
}
