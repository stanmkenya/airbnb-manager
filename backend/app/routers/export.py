from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from app.core.collection_helpers import get_user_collection_id
from app.core.auth import get_current_user
from app.core.firestore_helpers import get_subcollection_documents
from io import BytesIO
import csv

router = APIRouter()


@router.get("/csv")
async def export_csv(
    type: str = Query(...),  # 'expenses' or 'bookings'
    listingId: str = Query(...),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export expenses or bookings to CSV
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    # Fetch data
    if type == 'expenses':
        data_list = get_subcollection_documents('collections', collection_id, f'expenses/{listingId}')

        # Filter by date
        filtered_data = []
        for item in data_list:
            date = item.get('date', '')
            if from_date and date < from_date:
                continue
            if to_date and date > to_date:
                continue
            filtered_data.append({
                'id': item.get('id'),
                'date': item.get('date'),
                'category': item.get('category'),
                'subCategory': item.get('subCategory'),
                'amount': item.get('amount'),
                'notes': item.get('notes'),
                'receiptRef': item.get('receiptRef'),
            })

        # Create CSV
        output = BytesIO()
        output.write('\ufeff'.encode('utf-8'))  # BOM for Excel
        writer = csv.DictWriter(
            output,
            fieldnames=['id', 'date', 'category', 'subCategory', 'amount', 'notes', 'receiptRef'],
            extrasaction='ignore'
        )
        writer.writeheader()
        writer.writerows(filtered_data)

        output.seek(0)
        filename = f"expenses_{listingId}_{from_date or 'all'}_{to_date or 'all'}.csv"

    elif type == 'bookings':
        data_list = get_subcollection_documents('collections', collection_id, f'income/{listingId}')

        # Filter by date
        filtered_data = []
        for item in data_list:
            check_in = item.get('checkIn', '')
            if from_date and check_in < from_date:
                continue
            if to_date and check_in > to_date:
                continue
            filtered_data.append({
                'id': item.get('id'),
                'guestName': item.get('guestName'),
                'guestEmail': item.get('guestEmail'),
                'guestPhone': item.get('guestPhone'),
                'checkIn': item.get('checkIn'),
                'checkOut': item.get('checkOut'),
                'nights': item.get('nights'),
                'nightlyRate': item.get('nightlyRate'),
                'totalPaid': item.get('totalPaid'),
                'platform': item.get('platform'),
                'commissionPaid': item.get('commissionPaid'),
                'netIncome': item.get('netIncome'),
            })

        # Create CSV
        output = BytesIO()
        output.write('\ufeff'.encode('utf-8'))
        writer = csv.DictWriter(
            output,
            fieldnames=['id', 'guestName', 'guestEmail', 'guestPhone', 'checkIn', 'checkOut',
                       'nights', 'nightlyRate', 'totalPaid', 'platform', 'commissionPaid', 'netIncome'],
            extrasaction='ignore'
        )
        writer.writeheader()
        writer.writerows(filtered_data)

        output.seek(0)
        filename = f"bookings_{listingId}_{from_date or 'all'}_{to_date or 'all'}.csv"
    else:
        raise HTTPException(status_code=400, detail="Invalid export type")

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/excel")
async def export_excel(
    type: str = Query(...),
    listingId: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export to Excel (requires openpyxl implementation)
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if listingId and current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    # Placeholder - full implementation would use openpyxl
    return {
        "message": "Excel export will be implemented with openpyxl",
        "type": type,
        "listingId": listingId,
        "from": from_date,
        "to": to_date
    }


@router.get("/pdf")
async def export_pdf(
    type: str = Query(...),
    listingId: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export to PDF (requires WeasyPrint implementation)
    """
    # Get collection (supports superadmin)
    collection_id = get_user_collection_id(current_user)

    # Check access
    if listingId and current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listingId not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    # Placeholder - full implementation would use WeasyPrint
    return {
        "message": "PDF export will be implemented with WeasyPrint",
        "type": type,
        "listingId": listingId,
        "from": from_date,
        "to": to_date
    }
