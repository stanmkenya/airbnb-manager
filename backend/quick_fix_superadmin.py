#!/usr/bin/env python3
"""
Quick fix to allow superadmin to access all routers.

This script replaces the collection_id retrieval pattern in all routers
to support superadmin accessing data (defaults to first collection).
"""

import re


def fix_router_file(filepath: str) -> bool:
    """Fix a single router file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Step 1: Add import if not present
    if "from app.core.collection_helpers import" not in content:
        # Find auth import and add collection helpers import after it
        auth_import = "from app.core.auth import"
        if auth_import in content:
            content = content.replace(
                auth_import,
                f"from app.core.collection_helpers import get_user_collection_id\n{auth_import}"
            )

    # Step 2: Replace the collection_id pattern
    old_pattern = r"# Get user's collection\s+collection_id = current_user\.get\('collectionId'\)\s+if not collection_id:\s+raise HTTPException\(status_code=400, detail=\"User not assigned to a collection\"\)"

    new_pattern = "# Get collection (supports superadmin)\n    collection_id = get_user_collection_id(current_user)"

    content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

    # Write back if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True

    return False


def main():
    """Main function"""
    print("\n" + "="*70)
    print("QUICK FIX: ENABLING SUPERADMIN ACCESS TO ALL ROUTERS")
    print("="*70 + "\n")

    routers = [
        'app/routers/income.py',
        'app/routers/expenses.py',
        'app/routers/blocked_dates.py',
        'app/routers/reports.py',
        'app/routers/export.py',
    ]

    for router in routers:
        print(f"Processing: {router}...")
        try:
            if fix_router_file(router):
                print(f"  ✓ Updated {router}")
            else:
                print(f"  - No changes needed for {router}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "="*70)
    print("✅ QUICK FIX COMPLETE")
    print("="*70)
    print("\nSuperadmin will now default to the first available collection.")
    print("This allows dashboard access without errors.")
    print("\nNext steps:")
    print("1. Test superadmin dashboard access")
    print("2. Deploy to Railway")
    print("3. Later: Add full multi-collection aggregation support")


if __name__ == '__main__':
    main()
