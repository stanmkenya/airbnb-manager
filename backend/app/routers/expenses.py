from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.core.auth import get_current_user, require_manager_or_admin
from app.firebase_client import firebase_client
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
    all_expenses = []

    # Determine which listings to query
    if current_user['role'] == 'admin':
        if listingId:
            listing_ids = [listingId]
        else:
            # Get all listings
            listings_ref = firebase_client.get_database_ref('/listings')
            all_listings = listings_ref.get() or {}
            listing_ids = list(all_listings.keys())
    else:
        # Get assigned listings
        assigned_listings = current_user.get('assignedListings', {})
        if listingId:
            if listingId not in assigned_listings:
                raise HTTPException(status_code=403, detail="Access denied to this listing")
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Fetch expenses for each listing
    for lid in listing_ids:
        expenses_ref = firebase_client.get_database_ref(f'/expenses/{lid}')
        expenses = expenses_ref.get() or {}

        for expense_id, expense in expenses.items():
            # Apply filters
            if from_date and expense.get('date', '') < from_date:
                continue
            if to_date and expense.get('date', '') > to_date:
                continue
            if category and expense.get('category') != category:
                continue

            all_expenses.append({
                'id': expense_id,
                'listingId': lid,
                **expense
            })

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
    listing_id = expense.listingId

    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listing_id not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied to this listing")

    # Create expense
    expenses_ref = firebase_client.get_database_ref(f'/expenses/{listing_id}')
    new_expense_ref = expenses_ref.push()

    expense_data = {
        **expense.dict(exclude={'listingId'}),
        'enteredBy': current_user['uid'],
        'createdAt': int(time.time() * 1000),
        'updatedAt': int(time.time() * 1000)
    }

    new_expense_ref.set(expense_data)

    return {
        "id": new_expense_ref.key,
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
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    expense_ref = firebase_client.get_database_ref(f'/expenses/{listingId}/{expense_id}')
    expense = expense_ref.get()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"id": expense_id, "listingId": listingId, **expense}


@router.put("/{expense_id}")
async def update_expense(
    expense_id: str,
    listingId: str = Query(...),
    expense_update: ExpenseUpdate,
    current_user: dict = Depends(require_manager_or_admin)
):
    """
    Update an expense
    """
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    expense_ref = firebase_client.get_database_ref(f'/expenses/{listingId}/{expense_id}')
    existing = expense_ref.get()

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
    audit_ref = firebase_client.get_database_ref('/audit_log').push()
    audit_ref.set({
        'table': 'expenses',
        'recordId': expense_id,
        'action': 'update',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': expense_update.dict(exclude_unset=True),
        'timestamp': int(time.time() * 1000)
    })

    # Update expense
    update_data = {
        k: v for k, v in expense_update.dict(exclude_unset=True).items()
        if v is not None
    }
    update_data['updatedAt'] = int(time.time() * 1000)

    expense_ref.update(update_data)

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
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    expense_ref = firebase_client.get_database_ref(f'/expenses/{listingId}/{expense_id}')
    existing = expense_ref.get()

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
    audit_ref = firebase_client.get_database_ref('/audit_log').push()
    audit_ref.set({
        'table': 'expenses',
        'recordId': expense_id,
        'action': 'delete',
        'changedBy': current_user['uid'],
        'oldValues': existing,
        'newValues': {},
        'timestamp': int(time.time() * 1000)
    })

    # Delete expense
    expense_ref.delete()

    return {"message": "Expense deleted successfully"}
