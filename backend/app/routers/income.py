from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.core.auth import get_current_user, require_manager_or_admin
from app.firebase_client import firebase_client
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
    all_bookings = []

    # Determine which listings to query
    if current_user['role'] == 'admin':
        if listingId:
            listing_ids = [listingId]
        else:
            listings_ref = firebase_client.get_database_ref('/listings')
            all_listings = listings_ref.get() or {}
            listing_ids = list(all_listings.keys())
    else:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId:
            if listingId not in assigned_listings:
                raise HTTPException(status_code=403, detail="Access denied to this listing")
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Fetch bookings for each listing
    for lid in listing_ids:
        bookings_ref = firebase_client.get_database_ref(f'/bookings/{lid}')
        bookings = bookings_ref.get() or {}

        for booking_id, booking in bookings.items():
            # Apply filters
            if from_date and booking.get('checkIn', '') < from_date:
                continue
            if to_date and booking.get('checkOut', '') > to_date:
                continue
            if platform and booking.get('platform') != platform:
                continue

            all_bookings.append({
                'id': booking_id,
                'listingId': lid,
                **booking
            })

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
    listing_id = booking.listingId

    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listing_id not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied to this listing")

    # Calculate nights and totals
    nights = calculate_nights(booking.checkIn, booking.checkOut)
    total_paid = booking.totalPaid if booking.totalPaid is not None else (nights * booking.nightlyRate)
    net_income = total_paid - booking.commissionPaid
    commission_pct = (booking.commissionPaid / total_paid * 100) if total_paid > 0 else 0

    # Create booking
    bookings_ref = firebase_client.get_database_ref(f'/bookings/{listing_id}')
    new_booking_ref = bookings_ref.push()

    booking_data = {
        **booking.dict(exclude={'listingId', 'totalPaid'}),
        'nights': nights,
        'totalPaid': total_paid,
        'netIncome': net_income,
        'commissionPct': round(commission_pct, 2),
        'enteredBy': current_user['uid'],
        'createdAt': int(time.time() * 1000)
    }

    new_booking_ref.set(booking_data)

    return {
        "id": new_booking_ref.key,
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
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    booking_ref = firebase_client.get_database_ref(f'/bookings/{listingId}/{booking_id}')
    booking = booking_ref.get()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {"id": booking_id, "listingId": listingId, **booking}


@router.put("/{booking_id}")
async def update_booking(
    booking_id: str,
    listingId: str = Query(...),
    booking_update: BookingUpdate,
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Update a booking
    """
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    booking_ref = firebase_client.get_database_ref(f'/bookings/{listingId}/{booking_id}')
    existing = booking_ref.get()

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
    audit_ref = firebase_client.get_database_ref('/audit_log').push()
    audit_ref.set({
        'table': 'bookings',
        'recordId': booking_id,
        'action': 'update',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': update_data,
        'timestamp': int(time.time() * 1000)
    })

    booking_ref.update(update_data)

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
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    booking_ref = firebase_client.get_database_ref(f'/bookings/{listingId}/{booking_id}')
    existing = booking_ref.get()

    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Log audit
    audit_ref = firebase_client.get_database_ref('/audit_log').push()
    audit_ref.set({
        'table': 'bookings',
        'recordId': booking_id,
        'action': 'delete',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': {},
        'timestamp': int(time.time() * 1000)
    })

    booking_ref.delete()

    return {"message": "Booking deleted successfully"}
