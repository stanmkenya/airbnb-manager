#!/bin/bash
# Quick fix to allow superadmin to access routers
# Replaces the collection_id pattern with one that supports superadmin

echo "Applying quick fix for superadmin support..."

# Files to update
files=(
    "app/routers/income.py"
    "app/routers/expenses.py"
    "app/routers/blocked_dates.py"
    "app/routers/reports.py"
    "app/routers/export.py"
)

for file in "${files[@]}"; do
    echo "Processing $file..."

    # Add import if not present
    if ! grep -q "from app.core.collection_helpers import" "$file"; then
        # Add after the auth import
        sed -i.bak '/from app.core.auth import/a\
from app.core.collection_helpers import get_user_collection_id' "$file"
        echo "  ✓ Added import to $file"
    fi

    # Replace the collection_id pattern
    # This is a multi-line replacement so we'll use perl
    perl -i -pe 'BEGIN{undef $/;} s/# Get user'\''s collection\n    collection_id = current_user\.get\('\''collectionId'\''\)\n    if not collection_id:\n        raise HTTPException\(status_code=400, detail="User not assigned to a collection"\)/# Get collection (supports superadmin)\n    collection_id = get_user_collection_id(current_user)/smg' "$file"

    echo "  ✓ Updated collection_id patterns in $file"
done

echo ""
echo "✅ Quick fix applied to all routers!"
echo ""
echo "Next steps:"
echo "1. Test that superadmin can now access the dashboard"
echo "2. Deploy to Railway"
echo "3. Later: Add full multi-collection aggregation support"
