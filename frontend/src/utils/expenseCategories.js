// Expense categories as defined in requirements
export const EXPENSE_CATEGORIES = {
  'Rent': [],
  'Cleaning': [],
  'Breakfast Shopping': [
    'Coffee',
    'Sugar',
    'Oil',
    'Salt',
    'Tea Leaves',
    'Sweets',
    'Other'
  ],
  'Detergents': [
    'Utensil Cleaner',
    'Floor Cleaner',
    'Bath/Toilet'
  ],
  'Utilities': [
    'Gas',
    'Electricity',
    'Water Bill',
    'Wi-Fi',
    'Water Refill'
  ],
  'Waste': [],
  'Maintenance & Other': [
    'Repairs',
    'Furniture',
    'Appliances',
    'Renovations',
    'Other'
  ]
}

export function getSubCategories(category) {
  return EXPENSE_CATEGORIES[category] || []
}

export function getAllCategories() {
  return Object.keys(EXPENSE_CATEGORIES)
}
