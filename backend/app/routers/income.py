from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.core.collection_helpers import get_user_collection_id
from app.core.auth import get_current_user, require_manager_or_admin
from app.core.firestore_helpers import (
    get_subcollection_documents, get_document, add_document,
    update_document, delete_document
)
import time
from datetime import datetime

router = APIRouter()


class BookingCreate(BaseModel):
    listingId: str
    guestName: str
    guestPhone: Optional[str] = None
    guestEmail: Optional[str] = None
    checkIn: str  # YYYY-MM-DD
    checkOut: str  # YYYY-MM-DD
    nightlyRate: float
    totalPaid: Optional[float] = None
    platform: str  # Airbnb, Booking.com, Direct, VRBO, Other
    commissionPaid: float = 0
    notes: Optional[str] = None


class BookingUpdate(BaseModel):
    guestName: Optional[str] = None
    guestPhone: Optional[str] = None
    guestEmail: Optional[str] = None
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    nightlyRate: Optional[float] = None
    totalPaid: Optional[float] = None
    platform: Optional[str] = None
    commissionPaid: Optional[float] = None
    notes: Optional[str] = None


def calculate_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between check-in and check-out"""
    date1 = datetime.strptime(check_in, '%Y-%m-%d')
    date2 = datetime.strptime(check_out, '%Y-%m-%d')
    return (date2 - date1).days


@router.get("")
async def get_bookings(
    listingId: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    platform: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get bookings with optional filters
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    all_bookings = []

    # Determine which listings to query
    if current_user['role'] in ['collection_admin', 'superadmin']:
        if listingId:
            listing_ids = [listingId]
        else:
            all_listings = get_subcollection_documents('collections', collection_id, 'listings')
            listing_ids = [listing['id'] for listing in all_listings]
    else:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId:
            if listingId not in assigned_listings:
                raise HTTPException(status_code=403, detail="Access denied to this listing")
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Fetch all bookings from the collection
    all_collection_bookings = get_subcollection_documents('collections', collection_id, 'bookings')

    # Filter bookings by listing IDs and other criteria
    for booking in all_collection_bookings:
        booking_listing_id = booking.get('listingId')

        # Check if booking belongs to one of the allowed listings
        if booking_listing_id not in listing_ids:
            continue

        # Apply date filters
        if from_date and booking.get('checkIn', '') < from_date:
            continue
        if to_date and booking.get('checkOut', '') > to_date:
            continue

        # Apply platform filter
        if platform and booking.get('platform') != platform:
            continue

        all_bookings.append(booking)

    # Sort by check-in date descending
    all_bookings.sort(key=lambda x: x.get('checkIn', ''), reverse=True)

    return all_bookings


@router.post("")
async def create_booking(
    booking: BookingCreate,
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Create a new booking
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    listing_id = booking.listingId

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listing_id not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied to this listing")

    # Calculate nights and totals
    nights = calculate_nights(booking.checkIn, booking.checkOut)
    total_paid = booking.totalPaid if booking.totalPaid is not None else (nights * booking.nightlyRate)
    net_income = total_paid - booking.commissionPaid
    commission_pct = (booking.commissionPaid / total_paid * 100) if total_paid > 0 else 0

    # Create booking
    booking_data = {
        **booking.dict(exclude={'listingId', 'totalPaid'}),
        'nights': nights,
        'totalPaid': total_paid,
        'netIncome': net_income,
        'commissionPct': round(commission_pct, 2),
        'enteredBy': current_user['uid'],
        'createdAt': int(time.time() * 1000)
    }

    booking_id = add_document(f'collections/{collection_id}/income/{listing_id}', booking_data)

    return {
        "id": booking_id,
        "listingId": listing_id,
        **booking_data
    }


@router.get("/{booking_id}")
async def get_booking(
    booking_id: str,
    listingId: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific booking
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    booking = get_document(f'collections/{collection_id}/income/{listingId}', booking_id)

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {"id": booking_id, "listingId": listingId, **booking}


@router.put("/{booking_id}")
async def update_booking(
    booking_id: str,
    booking_update: BookingUpdate,
    listingId: str = Query(...),
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Update a booking
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    existing = get_document(f'collections/{collection_id}/income/{listingId}', booking_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Prepare update data
    update_data = {
        k: v for k, v in booking_update.dict(exclude_unset=True).items()
        if v is not None
    }

    # Recalculate if dates or rates changed
    check_in = update_data.get('checkIn', existing.get('checkIn'))
    check_out = update_data.get('checkOut', existing.get('checkOut'))
    nightly_rate = update_data.get('nightlyRate', existing.get('nightlyRate'))
    total_paid = update_data.get('totalPaid')
    commission_paid = update_data.get('commissionPaid', existing.get('commissionPaid', 0))

    if check_in and check_out:
        nights = calculate_nights(check_in, check_out)
        update_data['nights'] = nights

        if total_paid is None:
            total_paid = nights * nightly_rate
            update_data['totalPaid'] = total_paid

    if total_paid is None:
        total_paid = existing.get('totalPaid', 0)

    net_income = total_paid - commission_paid
    commission_pct = (commission_paid / total_paid * 100) if total_paid > 0 else 0

    update_data['netIncome'] = net_income
    update_data['commissionPct'] = round(commission_pct, 2)
    update_data['updatedAt'] = int(time.time() * 1000)

    # Log audit
    audit_data = {
        'table': 'bookings',
        'recordId': booking_id,
        'action': 'update',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': update_data,
        'timestamp': int(time.time() * 1000)
    }
    add_document('audit_log', audit_data)

    update_document(f'collections/{collection_id}/income/{listingId}', booking_id, update_data)

    return {"message": "Booking updated successfully"}


@router.delete("/{booking_id}")
async def delete_booking(
    booking_id: str,
    listingId: str = Query(...),
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Delete a booking
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    existing = get_document(f'collections/{collection_id}/income/{listingId}', booking_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Log audit
    audit_data = {
        'table': 'bookings',
        'recordId': booking_id,
        'action': 'delete',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': {},
        'timestamp': int(time.time() * 1000)
    }
    add_document('audit_log', audit_data)

    delete_document(f'collections/{collection_id}/income/{listingId}', booking_id)

    return {"message": "Booking deleted successfully"}
