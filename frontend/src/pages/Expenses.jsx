import { useState } from 'react'
import { Plus, Edit, Trash2, Filter, Download } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useListings } from '../hooks/useListings'
import { useExpenses, useCreateExpense, useUpdateExpense, useDeleteExpense } from '../hooks/useExpenses'
import { isManagerOrAdmin } from '../utils/roleGuard'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate, getCurrentMonth } from '../utils/dateHelpers'
import { getAllCategories } from '../utils/expenseCategories'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Table from '../components/ui/Table'
import ExpenseForm from '../components/forms/ExpenseForm'

export default function Expenses() {
  const { userProfile } = useAuth()
  const { data: listings } = useListings()

  const [filters, setFilters] = useState({
    listingId: '',
    category: '',
    ...getCurrentMonth(),
  })

  const { data: expenses, isLoading } = useExpenses(filters)
  const createExpense = useCreateExpense()
  const updateExpense = useUpdateExpense()
  const deleteExpense = useDeleteExpense()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingExpense, setEditingExpense] = useState(null)
  const [showFilters, setShowFilters] = useState(false)

  const canManageExpenses = isManagerOrAdmin(userProfile)

  const handleCreate = () => {
    setEditingExpense(null)
    setIsModalOpen(true)
  }

  const handleEdit = (expense) => {
    setEditingExpense(expense)
    setIsModalOpen(true)
  }

  const handleSubmit = async (data) => {
    try {
      if (editingExpense) {
        await updateExpense.mutateAsync({
          id: editingExpense.id,
          listingId: editingExpense.listingId,
          data,
        })
      } else {
        await createExpense.mutateAsync(data)
      }
      setIsModalOpen(false)
      setEditingExpense(null)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleDelete = async (expense) => {
    if (window.confirm('Are you sure you want to delete this expense?')) {
      try {
        await deleteExpense.mutateAsync({
          id: expense.id,
          listingId: expense.listingId,
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
      category: '',
      ...getCurrentMonth(),
    })
  }

  // Calculate total
  const total = expenses?.reduce((sum, exp) => sum + exp.amount, 0) || 0

  const columns = [
    {
      header: 'Date',
      accessor: 'date',
      render: (value) => formatDate(value),
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
      header: 'Category',
      accessor: 'category',
    },
    {
      header: 'Sub-Category',
      accessor: 'subCategory',
      render: (value) => value || '-',
    },
    {
      header: 'Amount',
      accessor: 'amount',
      render: (value) => formatCurrency(value),
    },
    {
      header: 'Receipt Ref',
      accessor: 'receiptRef',
      render: (value) => value || '-',
    },
    {
      header: 'Actions',
      accessor: 'id',
      render: (_, expense) => (
        <div className="flex gap-2">
          {canManageExpenses && (
            <>
              <button
                onClick={() => handleEdit(expense)}
                className="text-primary-600 hover:text-primary-700"
              >
                <Edit size={16} />
              </button>
              <button
                onClick={() => handleDelete(expense)}
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
          <h1 className="text-3xl font-bold text-gray-900">Expenses</h1>
          <p className="text-gray-600 mt-1">Track your property expenses</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowFilters(!showFilters)}>
            <Filter size={20} className="mr-2" />
            Filters
          </Button>
          {canManageExpenses && (
            <Button onClick={handleCreate}>
              <Plus size={20} className="mr-2" />
              Add Expense
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
                Category
              </label>
              <select
                name="category"
                value={filters.category}
                onChange={handleFilterChange}
                className="input-field"
              >
                <option value="">All Categories</option>
                {getAllCategories().map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
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

      {/* Summary Card */}
      <div className="card mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Expenses</p>
            <p className="text-3xl font-bold text-gray-900">{formatCurrency(total)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600 mb-1">Total Records</p>
            <p className="text-2xl font-semibold text-gray-900">{expenses?.length || 0}</p>
          </div>
        </div>
      </div>

      {/* Expenses Table */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <Table
            columns={columns}
            data={expenses || []}
            emptyMessage="No expenses found. Try adjusting your filters or add a new expense."
          />
        )}
      </div>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setEditingExpense(null)
        }}
        title={editingExpense ? 'Edit Expense' : 'Add New Expense'}
        size="lg"
      >
        <ExpenseForm
          initialData={editingExpense}
          onSubmit={handleSubmit}
          onCancel={() => {
            setIsModalOpen(false)
            setEditingExpense(null)
          }}
          isLoading={createExpense.isPending || updateExpense.isPending}
        />
      </Modal>
    </div>
  )
}
