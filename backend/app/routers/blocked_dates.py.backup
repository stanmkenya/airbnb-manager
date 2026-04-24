from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..firebase_client import firebase_client
from .auth import get_current_user

router = APIRouter(tags=["blocked-dates"])


class BlockedDateCreate(BaseModel):
    listingId: str
    date: str  # YYYY-MM-DD format
    reason: Optional[str] = "Blocked by manager"


class BlockedDateResponse(BaseModel):
    id: str
    listingId: str
    date: str
    reason: str
    blockedBy: str
    blockedAt: str


@router.get("")
async def get_blocked_dates(
    listing_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all blocked dates, optionally filtered by listing"""
    try:
        if listing_id:
            # Get blocked dates for specific listing
            blocked_ref = firebase_client.get_database_ref(f'/blocked-dates/{listing_id}')
            blocked_data = blocked_ref.get() or {}

            return [
                {
                    'id': blocked_id,
                    'listingId': listing_id,
                    **data
                }
                for blocked_id, data in blocked_data.items()
            ]
        else:
            # Get all blocked dates
            blocked_ref = firebase_client.get_database_ref('/blocked-dates')
            all_blocked = blocked_ref.get() or {}

            result = []
            for listing_id, dates in all_blocked.items():
                for blocked_id, data in dates.items():
                    result.append({
                        'id': blocked_id,
                        'listingId': listing_id,
                        **data
                    })

            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=BlockedDateResponse)
async def block_date(
    blocked_date: BlockedDateCreate,
    current_user: dict = Depends(get_current_user)
):
    """Block a date for a listing"""
    # Only admin or property managers can block dates
    if current_user['role'] not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized to block dates")

    try:
        # Verify listing exists
        listing_ref = firebase_client.get_database_ref(f'/listings/{blocked_date.listingId}')
        if not listing_ref.get():
            raise HTTPException(status_code=404, detail="Listing not found")

        # Check if date is already blocked
        blocked_ref = firebase_client.get_database_ref(f'/blocked-dates/{blocked_date.listingId}')
        existing_blocked = blocked_ref.get() or {}

        # Check if this exact date is already blocked
        for block_id, block_data in existing_blocked.items():
            if block_data.get('date') == blocked_date.date:
                # Already blocked, return existing
                return {
                    'id': block_id,
                    'listingId': blocked_date.listingId,
                    **block_data
                }

        # Create new blocked date
        new_blocked_ref = blocked_ref.push()
        blocked_id = new_blocked_ref.key

        blocked_data = {
            'date': blocked_date.date,
            'reason': blocked_date.reason,
            'blockedBy': current_user['email'],
            'blockedAt': datetime.utcnow().isoformat()
        }

        new_blocked_ref.set(blocked_data)

        return {
            'id': blocked_id,
            'listingId': blocked_date.listingId,
            **blocked_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{listing_id}/{date}")
async def unblock_date(
    listing_id: str,
    date: str,  # YYYY-MM-DD format
    current_user: dict = Depends(get_current_user)
):
    """Unblock a date for a listing"""
    # Only admin or property managers can unblock dates
    if current_user['role'] not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized to unblock dates")

    try:
        # Find and delete the blocked date
        blocked_ref = firebase_client.get_database_ref(f'/blocked-dates/{listing_id}')
        all_blocked = blocked_ref.get() or {}

        blocked_id = None
        for block_id, block_data in all_blocked.items():
            if block_data.get('date') == date:
                blocked_id = block_id
                break

        if not blocked_id:
            raise HTTPException(status_code=404, detail="Blocked date not found")

        # Delete the blocked date
        date_ref = firebase_client.get_database_ref(f'/blocked-dates/{listing_id}/{blocked_id}')
        date_ref.delete()

        return {"message": "Date unblocked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
