from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from app.core.collection_helpers import get_user_collection_id
from app.core.auth import get_current_user
from app.core.firestore_helpers import get_subcollection_documents, get_document
from collections import defaultdict
from datetime import datetime

router = APIRouter()


@router.get("/monthly-summary")
async def monthly_summary(
    listingId: Optional[str] = Query(None),
    year: int = Query(datetime.now().year),
    current_user: dict = Depends(get_current_user)
):
    """Get monthly expense summary by category"""
    collection_id = get_user_collection_id(current_user)

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
                return {"error": "Access denied"}
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Aggregate expenses by month and category
    monthly_data = defaultdict(lambda: defaultdict(float))

    for lid in listing_ids:
        expenses = get_subcollection_documents('collections', collection_id, f'expenses/{lid}')

        for expense in expenses:
            date_str = expense.get('date', '')
            if date_str.startswith(str(year)):
                month = date_str[:7]  # YYYY-MM
                category = expense.get('category', 'Other')
                amount = expense.get('amount', 0)
                monthly_data[month][category] += amount

    # Format response
    result = []
    for month in sorted(monthly_data.keys()):
        result.append({
            'month': month,
            'categories': dict(monthly_data[month]),
            'total': sum(monthly_data[month].values())
        })

    return result


@router.get("/cumulative")
async def cumulative_report(
    listingId: str = Query(...),
    year: int = Query(datetime.now().year),
    month: int = Query(datetime.now().month),
    current_user: dict = Depends(get_current_user)
):
    """Get daily cumulative expense report for a specific month"""
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            return {"error": "Access denied"}

    # Fetch expenses
    expenses = get_subcollection_documents('collections', collection_id, f'expenses/{listingId}')

    # Filter by month and aggregate by day
    month_str = f"{year}-{month:02d}"
    daily_totals = defaultdict(float)

    for expense in expenses:
        date_str = expense.get('date', '')
        if date_str.startswith(month_str):
            daily_totals[date_str] += expense.get('amount', 0)

    # Calculate cumulative
    cumulative = []
    running_total = 0
    for date in sorted(daily_totals.keys()):
        running_total += daily_totals[date]
        cumulative.append({
            'date': date,
            'dailyTotal': daily_totals[date],
            'cumulative': running_total
        })

    return {
        'month': month_str,
        'data': cumulative,
        'total': running_total
    }


@router.get("/pnl")
async def profit_loss_report(
    from_date: str = Query(...),
    to_date: str = Query(...),
    listingId: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get P&L report by listing for a date range"""
    collection_id = get_user_collection_id(current_user)

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
                return {"error": "Access denied"}
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    results = []

    for lid in listing_ids:
        # Get listing info
        listing = get_document(f'collections/{collection_id}/listings', lid) or {}

        # Calculate expenses
        expenses = get_subcollection_documents('collections', collection_id, f'expenses/{lid}')
        total_expenses = sum(
            e.get('amount', 0) for e in expenses
            if from_date <= e.get('date', '') <= to_date
        )

        # Calculate income
        bookings = get_subcollection_documents('collections', collection_id, f'income/{lid}')
        total_income = sum(
            b.get('netIncome', 0) for b in bookings
            if from_date <= b.get('checkIn', '') <= to_date
        )

        results.append({
            'listingId': lid,
            'listingName': listing.get('name', 'Unknown'),
            'revenue': total_income,
            'expenses': total_expenses,
            'netIncome': total_income - total_expenses,
            'margin': ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
        })

    return results


@router.get("/portfolio")
async def portfolio_report(
    from_date: str = Query(...),
    to_date: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Get consolidated portfolio P&L (Collection admin only)"""
    collection_id = get_user_collection_id(current_user)

    # Only collection admin or superadmin can view portfolio
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Access denied")

    all_listings = get_subcollection_documents('collections', collection_id, 'listings')

    total_revenue = 0
    total_expenses = 0
    listings_data = []

    for listing in all_listings:
        lid = listing['id']

        # Calculate expenses
        expenses = get_subcollection_documents('collections', collection_id, f'expenses/{lid}')
        listing_expenses = sum(
            e.get('amount', 0) for e in expenses
            if from_date <= e.get('date', '') <= to_date
        )

        # Calculate income
        bookings = get_subcollection_documents('collections', collection_id, f'income/{lid}')
        listing_income = sum(
            b.get('netIncome', 0) for b in bookings
            if from_date <= b.get('checkIn', '') <= to_date
        )

        total_revenue += listing_income
        total_expenses += listing_expenses

        listings_data.append({
            'listingId': lid,
            'listingName': listing.get('name', 'Unknown'),
            'revenue': listing_income,
            'expenses': listing_expenses,
            'netIncome': listing_income - listing_expenses
        })

    return {
        'period': {'from': from_date, 'to': to_date},
        'summary': {
            'totalRevenue': total_revenue,
            'totalExpenses': total_expenses,
            'netIncome': total_revenue - total_expenses,
            'margin': ((total_revenue - total_expenses) / total_revenue * 100) if total_revenue > 0 else 0
        },
        'listings': listings_data
    }


@router.get("/occupancy")
async def occupancy_report(
    listingId: str = Query(...),
    year: int = Query(datetime.now().year),
    month: int = Query(datetime.now().month),
    current_user: dict = Depends(get_current_user)
):
    """Get occupancy rate for a listing in a specific month"""
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            return {"error": "Access denied"}

    # Fetch bookings
    bookings = get_subcollection_documents('collections', collection_id, f'income/{listingId}')

    # Calculate occupied nights
    month_str = f"{year}-{month:02d}"
    total_nights = 0

    for booking in bookings:
        check_in = booking.get('checkIn', '')
        check_out = booking.get('checkOut', '')

        # Simple check if booking overlaps with the month
        if check_in.startswith(month_str) or check_out.startswith(month_str):
            total_nights += booking.get('nights', 0)

    # Calculate available nights (simplified - days in month)
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]

    occupancy_rate = (total_nights / days_in_month * 100) if days_in_month > 0 else 0

    return {
        'listingId': listingId,
        'year': year,
        'month': month,
        'occupiedNights': total_nights,
        'availableNights': days_in_month,
        'occupancyRate': round(occupancy_rate, 2)
    }


@router.get("/yoy")
async def year_over_year_report(
    listingId: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Year-over-year comparison"""
    collection_id = get_user_collection_id(current_user)

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
                return {"error": "Access denied"}
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Aggregate by year
    yearly_data = defaultdict(lambda: {'revenue': 0, 'expenses': 0})

    for lid in listing_ids:
        # Expenses
        expenses = get_subcollection_documents('collections', collection_id, f'expenses/{lid}')
        for expense in expenses:
            date_str = expense.get('date', '')
            if date_str:
                year = date_str[:4]
                yearly_data[year]['expenses'] += expense.get('amount', 0)

        # Income
        bookings = get_subcollection_documents('collections', collection_id, f'income/{lid}')
        for booking in bookings:
            check_in = booking.get('checkIn', '')
            if check_in:
                year = check_in[:4]
                yearly_data[year]['revenue'] += booking.get('netIncome', 0)

    # Format response
    result = []
    for year in sorted(yearly_data.keys()):
        data = yearly_data[year]
        result.append({
            'year': year,
            'revenue': data['revenue'],
            'expenses': data['expenses'],
            'netIncome': data['revenue'] - data['expenses']
        })

    return result
