/**
 * Format a number as currency
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code (default: KES)
 * @returns {string} Formatted currency string
 */
export function formatCurrency(amount, currency = 'KES') {
  if (amount === null || amount === undefined) return 'KES 0.00'

  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

/**
 * Parse currency string to number
 * @param {string} currencyString - Currency string to parse
 * @returns {number} Parsed number
 */
export function parseCurrency(currencyString) {
  if (!currencyString) return 0
  return parseFloat(currencyString.replace(/[^0-9.-]+/g, ''))
}

/**
 * Format a number with commas
 * @param {number} num - Number to format
 * @returns {string} Formatted number string
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return new Intl.NumberFormat('en-US').format(num)
}
