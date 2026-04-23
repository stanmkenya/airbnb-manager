/**
 * Check if user has the required role
 * @param {Object} userProfile - User profile object
 * @param {string|Array} requiredRole - Required role(s)
 * @returns {boolean} True if user has required role
 */
export function hasRole(userProfile, requiredRole) {
  if (!userProfile) return false

  const userRole = userProfile.role

  if (Array.isArray(requiredRole)) {
    return requiredRole.includes(userRole)
  }

  return userRole === requiredRole
}

/**
 * Check if user is admin (collection_admin or superadmin)
 * @param {Object} userProfile - User profile object
 * @returns {boolean} True if user is admin
 */
export function isAdmin(userProfile) {
  return hasRole(userProfile, ['collection_admin', 'superadmin'])
}

/**
 * Check if user is manager or admin
 * @param {Object} userProfile - User profile object
 * @returns {boolean} True if user is manager or admin
 */
export function isManagerOrAdmin(userProfile) {
  return hasRole(userProfile, ['collection_admin', 'superadmin', 'manager'])
}

/**
 * Check if user has access to a specific listing
 * @param {Object} userProfile - User profile object
 * @param {string} listingId - Listing ID to check
 * @returns {boolean} True if user has access
 */
export function hasListingAccess(userProfile, listingId) {
  if (!userProfile || !listingId) return false

  // Admins have access to all listings
  if (isAdmin(userProfile)) return true

  // Check if listing is in user's assigned listings
  const assignedListings = userProfile.assignedListings || {}
  return assignedListings[listingId] === true
}
