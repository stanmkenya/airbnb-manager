import { format, parseISO, startOfMonth, endOfMonth, startOfYear, endOfYear, subMonths, subYears } from 'date-fns'

/**
 * Format a date string or Date object
 * @param {string|Date} date - Date to format
 * @param {string} formatString - Format string (default: 'MMM dd, yyyy')
 * @returns {string} Formatted date string
 */
export function formatDate(date, formatString = 'MMM dd, yyyy') {
  if (!date) return ''
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return format(dateObj, formatString)
  } catch (error) {
    return ''
  }
}

/**
 * Get today's date in YYYY-MM-DD format
 * @returns {string} Today's date
 */
export function getTodayString() {
  return format(new Date(), 'yyyy-MM-dd')
}

/**
 * Get current month start and end dates
 * @returns {Object} Object with from and to dates
 */
export function getCurrentMonth() {
  const now = new Date()
  return {
    from: format(startOfMonth(now), 'yyyy-MM-dd'),
    to: format(endOfMonth(now), 'yyyy-MM-dd'),
  }
}

/**
 * Get last month start and end dates
 * @returns {Object} Object with from and to dates
 */
export function getLastMonth() {
  const lastMonth = subMonths(new Date(), 1)
  return {
    from: format(startOfMonth(lastMonth), 'yyyy-MM-dd'),
    to: format(endOfMonth(lastMonth), 'yyyy-MM-dd'),
  }
}

/**
 * Get current year start and end dates
 * @returns {Object} Object with from and to dates
 */
export function getCurrentYear() {
  const now = new Date()
  return {
    from: format(startOfYear(now), 'yyyy-MM-dd'),
    to: format(endOfYear(now), 'yyyy-MM-dd'),
  }
}

/**
 * Get last year start and end dates
 * @returns {Object} Object with from and to dates
 */
export function getLastYear() {
  const lastYear = subYears(new Date(), 1)
  return {
    from: format(startOfYear(lastYear), 'yyyy-MM-dd'),
    to: format(endOfYear(lastYear), 'yyyy-MM-dd'),
  }
}

/**
 * Calculate number of nights between two dates
 * @param {string} checkIn - Check-in date (YYYY-MM-DD)
 * @param {string} checkOut - Check-out date (YYYY-MM-DD)
 * @returns {number} Number of nights
 */
export function calculateNights(checkIn, checkOut) {
  if (!checkIn || !checkOut) return 0
  try {
    const start = parseISO(checkIn)
    const end = parseISO(checkOut)
    const diffTime = Math.abs(end - start)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  } catch (error) {
    return 0
  }
}

/**
 * Get a list of month options for dropdowns
 * @returns {Array} Array of month objects
 */
export function getMonthOptions() {
  const months = []
  for (let i = 0; i < 12; i++) {
    const date = subMonths(new Date(), i)
    months.push({
      value: format(date, 'yyyy-MM'),
      label: format(date, 'MMMM yyyy'),
    })
  }
  return months
}
