from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.auth import get_current_user, require_admin
from app.firebase_client import firebase_client
import time

router = APIRouter()


class ListingCreate(BaseModel):
    name: str
    address: str
    airbnbUrl: Optional[str] = None
    defaultRate: float
    bedrooms: int
    bathrooms: int


class ListingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    airbnbUrl: Optional[str] = None
    defaultRate: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    status: Optional[str] = None


@router.get("")
async def get_listings(current_user: dict = Depends(get_current_user)):
    """
    Get all listings accessible by current user
    """
    listings_ref = firebase_client.get_database_ref('/listings')
    all_listings = listings_ref.get() or {}

    # Filter based on role
    if current_user['role'] == 'admin':
        return list(all_listings.values())
    else:
        # Filter by assigned listings
        assigned_listings = current_user.get('assignedListings', {})
        filtered = [
            listing for listing_id, listing in all_listings.items()
            if listing_id in assigned_listings
        ]
        return filtered


@router.post("")
async def create_listing(
    listing: ListingCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new listing (Admin only)
    """
    listings_ref = firebase_client.get_database_ref('/listings')
    new_listing_ref = listings_ref.push()

    listing_data = {
        **listing.dict(),
        'status': 'active',
        'assignedManagers': {},
        'createdBy': current_user['uid'],
        'createdAt': int(time.time() * 1000)
    }

    new_listing_ref.set(listing_data)

    return {
        "id": new_listing_ref.key,
        **listing_data
    }


@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific listing
    """
    listing_ref = firebase_client.get_database_ref(f'/listings/{listing_id}')
    listing = listing_ref.get()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listing_id not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    return {"id": listing_id, **listing}


@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    listing_update: ListingUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update a listing (Admin only)
    """
    listing_ref = firebase_client.get_database_ref(f'/listings/{listing_id}')
    existing = listing_ref.get()

    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")

    update_data = {
        k: v for k, v in listing_update.dict(exclude_unset=True).items()
        if v is not None
    }
    update_data['updatedAt'] = int(time.time() * 1000)

    listing_ref.update(update_data)

    return {
        "message": "Listing updated successfully",
        "id": listing_id
    }


@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Soft delete a listing (Admin only)
    """
    listing_ref = firebase_client.get_database_ref(f'/listings/{listing_id}')
    existing = listing_ref.get()

    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing_ref.update({
        'status': 'inactive',
        'deletedAt': int(time.time() * 1000),
        'deletedBy': current_user['uid']
    })

    return {"message": "Listing deleted successfully"}
