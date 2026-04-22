from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.firestore_helpers import (
    get_subcollection_documents, get_document, add_document, delete_document
)
from ..core.collection_helpers import get_user_collection_id
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
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    try:
        # Fetch all blocked dates from the collection
        all_blocked_dates = get_subcollection_documents('collections', collection_id, 'blocked-dates')

        # Filter by listing_id if specified
        if listing_id:
            result = []
            for date in all_blocked_dates:
                if date.get('listingId') == listing_id:
                    result.append(date)
            return result
        else:
            # Return all blocked dates
            return all_blocked_dates

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=BlockedDateResponse)
async def block_date(
    blocked_date: BlockedDateCreate,
    current_user: dict = Depends(get_current_user)
):
    """Block a date for a listing"""
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Only admin or property managers can block dates
    if current_user['role'] not in ['collection_admin', 'superadmin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized to block dates")

    try:
        # Verify listing exists
        listing = get_document(f'collections/{collection_id}/listings', blocked_date.listingId)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Check if date is already blocked
        all_blocked_dates = get_subcollection_documents('collections', collection_id, 'blocked-dates')

        # Check if this exact date and listing combination is already blocked
        for block_data in all_blocked_dates:
            if block_data.get('date') == blocked_date.date and block_data.get('listingId') == blocked_date.listingId:
                # Already blocked, return existing
                return {
                    'id': block_data['id'],
                    'listingId': blocked_date.listingId,
                    **{k: v for k, v in block_data.items() if k != 'id'}
                }

        # Create new blocked date
        blocked_data = {
            'listingId': blocked_date.listingId,
            'date': blocked_date.date,
            'reason': blocked_date.reason,
            'blockedBy': current_user['email'],
            'blockedAt': datetime.utcnow().isoformat()
        }

        blocked_id = add_document(f'collections/{collection_id}/blocked-dates', blocked_data)

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
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Only admin or property managers can unblock dates
    if current_user['role'] not in ['collection_admin', 'superadmin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized to unblock dates")

    try:
        # Find and delete the blocked date
        all_blocked = get_subcollection_documents('collections', collection_id, 'blocked-dates')

        blocked_id = None
        for block_data in all_blocked:
            if block_data.get('date') == date and block_data.get('listingId') == listing_id:
                blocked_id = block_data['id']
                break

        if not blocked_id:
            raise HTTPException(status_code=404, detail="Blocked date not found")

        # Delete the blocked date
        delete_document(f'collections/{collection_id}/blocked-dates', blocked_id)

        return {"message": "Date unblocked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
