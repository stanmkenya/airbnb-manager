#!/usr/bin/env python3
"""
Automated script to update routers for superadmin multi-collection access.

This script updates income, expenses, blocked_dates, reports, and export routers
to support superadmin accessing all collections while maintaining existing
functionality for regular users.
"""

import re


def add_imports_to_file(content: str) -> str:
    """Add necessary imports for collection helpers"""
    # Check if Query is already imported
    if ", Query" not in content and "Query" not in content:
        content = content.replace(
            "from fastapi import ",
            "from fastapi import Query, "
        )

    # Add collection helpers import after auth import
    if "from app.core.collection_helpers import" not in content:
        auth_import_line = "from app.core.auth import"
        if auth_import_line in content:
            content = content.replace(
                auth_import_line,
                f"from app.core.collection_helpers import get_collection_ids, require_collection_id_for_mutation\n{auth_import_line}"
            )

    return content


def update_get_endpoint(func_content: str, resource_name: str) -> str:
    """
    Update a GET endpoint to support multi-collection access.

    Changes:
    1. Add collectionId parameter
    2. Replace collection_id retrieval with get_collection_ids()
    3. Loop through collections
    4. Add collectionId to response objects
    """
    # Add collectionId parameter if not already present
    if "collectionId: Optional[str] = Query(None)" not in func_content:
        # Find the function signature and add parameter
        func_content = re.sub(
            r"(async def \w+\([^)]*)(current_user: dict = Depends\(get_current_user\))",
            r"\1collectionId: Optional[str] = Query(None),\n    \2",
            func_content
        )

    # Replace the old collection_id pattern
    old_pattern = r"# Get user's collection\s+collection_id = current_user\.get\('collectionId'\)\s+if not collection_id:\s+raise HTTPException\(status_code=400, detail=\"User not assigned to a collection\"\)"

    new_pattern = """# Get collection IDs to query
    collection_ids = get_collection_ids(current_user, collectionId)"""

    func_content = re.sub(old_pattern, new_pattern, func_content, flags=re.MULTILINE)

    return func_content


def update_mutation_endpoint(func_content: str) -> str:
    """
    Update a POST/PUT/DELETE endpoint to support multi-collection mutations.

    Changes:
    1. Add collectionId parameter
    2. Replace collection_id retrieval with require_collection_id_for_mutation()
    """
    # Add collectionId parameter if not already present
    if "collectionId: Optional[str] = Query(None)" not in func_content:
        # Find where to add the parameter (before current_user dependency)
        patterns_to_try = [
            (r"(async def \w+\([^)]*)(current_user: dict = Depends\(require_manager_or_admin\))",
             r"\1collectionId: Optional[str] = Query(None),\n    \2"),
            (r"(async def \w+\([^)]*)(current_user: dict = Depends\(get_current_user\))",
             r"\1collectionId: Optional[str] = Query(None),\n    \2"),
        ]

        for pattern, replacement in patterns_to_try:
            if re.search(pattern, func_content):
                func_content = re.sub(pattern, replacement, func_content)
                break

    # Replace the old collection_id pattern
    old_pattern = r"# Get user's collection\s+collection_id = current_user\.get\('collectionId'\)\s+if not collection_id:\s+raise HTTPException\(status_code=400, detail=\"User not assigned to a collection\"\)"

    new_pattern = """# Get collection ID for mutation
    collection_id = require_collection_id_for_mutation(current_user, collectionId)"""

    func_content = re.sub(old_pattern, new_pattern, func_content, flags=re.MULTILINE)

    return func_content


def process_router_file(filepath: str):
    """Process a single router file"""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath}")
    print(f"{'='*60}")

    with open(filepath, 'r') as f:
        content = f.read()

    # Add imports
    print("✓ Adding imports...")
    content = add_imports_to_file(content)

    # The actual endpoint updates need to be done manually or with more
    # sophisticated parsing since they vary by endpoint
    # This script provides the foundation

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✓ Updated {filepath}")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("UPDATING ROUTERS FOR SUPERADMIN MULTI-COLLECTION ACCESS")
    print("="*60)

    routers = [
        'app/routers/income.py',
        'app/routers/expenses.py',
        'app/routers/blocked_dates.py',
        'app/routers/reports.py',
        'app/routers/export.py',
    ]

    for router in routers:
        try:
            process_router_file(router)
        except Exception as e:
            print(f"❌ Error processing {router}: {e}")

    print("\n" + "="*60)
    print("✅ SCRIPT COMPLETE")
    print("="*60)
    print("\nNote: Imports have been added. Manual review and endpoint")
    print("updates still required for full functionality.")


if __name__ == '__main__':
    main()
