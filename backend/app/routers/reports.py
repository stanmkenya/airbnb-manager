from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.auth import get_current_user, require_admin
from app.firebase_client import firebase_client
from collections import defaultdict
from datetime import datetime

router = APIRouter()


@router.get("/monthly-summary")
async def monthly_summary(
    listingId: Optional[str] = Query(None),
    year: int = Query(datetime.now().year),
    current_user: dict = Depends(get_current_user)
):
    """
    Get monthly expense summary by category
    """
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
                return {"error": "Access denied"}
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Aggregate expenses by month and category
    monthly_data = defaultdict(lambda: defaultdict(float))

    for lid in listing_ids:
        expenses_ref = firebase_client.get_database_ref(f'/expenses/{lid}')
        expenses = expenses_ref.get() or {}

        for expense_id, expense in expenses.items():
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
    """
    Get daily cumulative expense report for a specific month
    """
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            return {"error": "Access denied"}

    # Fetch expenses
    expenses_ref = firebase_client.get_database_ref(f'/expenses/{listingId}')
    expenses = expenses_ref.get() or {}

    # Filter by month and aggregate by day
    month_str = f"{year}-{month:02d}"
    daily_totals = defaultdict(float)

    for expense_id, expense in expenses.items():
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
    """
    Get P&L report by listing for a date range
    """
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
                return {"error": "Access denied"}
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    results = []

    for lid in listing_ids:
        # Get listing info
        listing_ref = firebase_client.get_database_ref(f'/listings/{lid}')
        listing = listing_ref.get() or {}

        # Calculate expenses
        expenses_ref = firebase_client.get_database_ref(f'/expenses/{lid}')
        expenses = expenses_ref.get() or {}
        total_expenses = sum(
            e.get('amount', 0) for e in expenses.values()
            if from_date <= e.get('date', '') <= to_date
        )

        # Calculate income
        bookings_ref = firebase_client.get_database_ref(f'/bookings/{lid}')
        bookings = bookings_ref.get() or {}
        total_income = sum(
            b.get('netIncome', 0) for b in bookings.values()
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
    current_user: dict = Depends(require_admin)
):
    """
    Get consolidated portfolio P&L (Admin only)
    """
    listings_ref = firebase_client.get_database_ref('/listings')
    all_listings = listings_ref.get() or {}

    total_revenue = 0
    total_expenses = 0
    listings_data = []

    for lid in all_listings.keys():
        # Calculate expenses
        expenses_ref = firebase_client.get_database_ref(f'/expenses/{lid}')
        expenses = expenses_ref.get() or {}
        listing_expenses = sum(
            e.get('amount', 0) for e in expenses.values()
            if from_date <= e.get('date', '') <= to_date
        )

        # Calculate income
        bookings_ref = firebase_client.get_database_ref(f'/bookings/{lid}')
        bookings = bookings_ref.get() or {}
        listing_income = sum(
            b.get('netIncome', 0) for b in bookings.values()
            if from_date <= b.get('checkIn', '') <= to_date
        )

        total_revenue += listing_income
        total_expenses += listing_expenses

        listings_data.append({
            'listingId': lid,
            'listingName': all_listings[lid].get('name', 'Unknown'),
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
    """
    Get occupancy rate for a listing in a specific month
    """
    # Check access
    if current_user['role'] != 'admin':
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            return {"error": "Access denied"}

    # Fetch bookings
    bookings_ref = firebase_client.get_database_ref(f'/bookings/{listingId}')
    bookings = bookings_ref.get() or {}

    # Calculate occupied nights
    month_str = f"{year}-{month:02d}"
    total_nights = 0

    for booking_id, booking in bookings.items():
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
    """
    Year-over-year comparison
    """
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
                return {"error": "Access denied"}
            listing_ids = [listingId]
        else:
            listing_ids = list(assigned_listings.keys())

    # Aggregate by year
    yearly_data = defaultdict(lambda: {'revenue': 0, 'expenses': 0})

    for lid in listing_ids:
        # Expenses
        expenses_ref = firebase_client.get_database_ref(f'/expenses/{lid}')
        expenses = expenses_ref.get() or {}
        for expense in expenses.values():
            date_str = expense.get('date', '')
            if date_str:
                year = date_str[:4]
                yearly_data[year]['expenses'] += expense.get('amount', 0)

        # Income
        bookings_ref = firebase_client.get_database_ref(f'/bookings/{lid}')
        bookings = bookings_ref.get() or {}
        for booking in bookings.values():
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
