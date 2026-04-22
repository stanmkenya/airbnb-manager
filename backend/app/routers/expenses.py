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

router = APIRouter()


class ExpenseCreate(BaseModel):
    listingId: str
    date: str  # YYYY-MM-DD format
    category: str
    subCategory: Optional[str] = None
    amount: float
    notes: Optional[str] = None
    receiptRef: Optional[str] = None


class ExpenseUpdate(BaseModel):
    date: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None
    receiptRef: Optional[str] = None


@router.get("")
async def get_expenses(
    listingId: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get expenses with optional filters
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    all_expenses = []

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

    # Fetch all expenses from the collection
    all_collection_expenses = get_subcollection_documents('collections', collection_id, 'expenses')

    # Filter expenses by listing IDs and other criteria
    for expense in all_collection_expenses:
        expense_listing_id = expense.get('listingId')

        # Check if expense belongs to one of the allowed listings
        if expense_listing_id not in listing_ids:
            continue

        # Apply date filters
        if from_date and expense.get('date', '') < from_date:
            continue
        if to_date and expense.get('date', '') > to_date:
            continue

        # Apply category filter
        if category and expense.get('category') != category:
            continue

        all_expenses.append(expense)

    # Sort by date descending
    all_expenses.sort(key=lambda x: x.get('date', ''), reverse=True)

    return all_expenses


@router.post("")
async def create_expense(
    expense: ExpenseCreate,
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Create a new expense entry
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    listing_id = expense.listingId

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listing_id not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied to this listing")

    # Create expense
    expense_data = {
        **expense.dict(exclude={'listingId'}),
        'enteredBy': current_user['uid'],
        'createdAt': int(time.time() * 1000),
        'updatedAt': int(time.time() * 1000)
    }

    expense_id = add_document(f'collections/{collection_id}/expenses/{listing_id}', expense_data)

    return {
        "id": expense_id,
        "listingId": listing_id,
        **expense_data
    }


@router.get("/{expense_id}")
async def get_expense(
    expense_id: str,
    listingId: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific expense
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    expense = get_document(f'collections/{collection_id}/expenses/{listingId}', expense_id)

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"id": expense_id, "listingId": listingId, **expense}


@router.put("/{expense_id}")
async def update_expense(
    expense_id: str,
    expense_update: ExpenseUpdate,
    listingId: str = Query(...),
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Update an expense
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    existing = get_document(f'collections/{collection_id}/expenses/{listingId}', expense_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Check if user can edit (managers can only edit their own within 30 days)
    if current_user['role'] == 'manager':
        if existing.get('enteredBy') != current_user['uid']:
            raise HTTPException(status_code=403, detail="Can only edit your own expenses")

        created_at = existing.get('createdAt', 0)
        age_days = (time.time() * 1000 - created_at) / (1000 * 60 * 60 * 24)
        if age_days > 30:
            raise HTTPException(status_code=403, detail="Cannot edit expenses older than 30 days")

    # Log audit
    audit_data = {
        'table': 'expenses',
        'recordId': expense_id,
        'action': 'update',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': expense_update.dict(exclude_unset=True),
        'timestamp': int(time.time() * 1000)
    }
    add_document('audit_log', audit_data)

    # Update expense
    update_data = {
        k: v for k, v in expense_update.dict(exclude_unset=True).items()
        if v is not None
    }
    update_data['updatedAt'] = int(time.time() * 1000)

    update_document(f'collections/{collection_id}/expenses/{listingId}', expense_id, update_data)

    return {"message": "Expense updated successfully"}


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    listingId: str = Query(...),
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Delete an expense
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    existing = get_document(f'collections/{collection_id}/expenses/{listingId}', expense_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Check if user can delete (managers can only delete their own within 30 days)
    if current_user['role'] == 'manager':
        if existing.get('enteredBy') != current_user['uid']:
            raise HTTPException(status_code=403, detail="Can only delete your own expenses")

        created_at = existing.get('createdAt', 0)
        age_days = (time.time() * 1000 - created_at) / (1000 * 60 * 60 * 24)
        if age_days > 30:
            raise HTTPException(status_code=403, detail="Cannot delete expenses older than 30 days")

    # Log audit
    audit_data = {
        'table': 'expenses',
        'recordId': expense_id,
        'action': 'delete',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': {},
        'timestamp': int(time.time() * 1000)
    }
    add_document('audit_log', audit_data)

    # Delete expense
    delete_document(f'collections/{collection_id}/expenses/{listingId}', expense_id)

    return {"message": "Expense deleted successfully"}
