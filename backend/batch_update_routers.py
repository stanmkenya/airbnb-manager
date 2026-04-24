#!/usr/bin/env python3
"""
Batch update all remaining routers for superadmin multi-collection support.

This script makes the minimum necessary changes to allow superadmin to bypass
the "User not assigned to a collection" error while maintaining backward
compatibility for regular users.
"""

import re


def update_file(filepath: str, updates: dict):
    """Update a file with the specified find/replace operations"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Apply each update
    for find_text, replace_text in updates.items():
        if find_text in content:
            content = content.replace(find_text, replace_text, 1)

    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False


def add_collection_helper_imports(filepath: str):
    """Add collection helper imports to a file"""
    with open(filepath, 'r') as f:
        content = f.read()

    if "from app.core.collection_helpers import" in content:
        print(f"  ✓ Imports already added to {filepath}")
        return False

    # Find the auth import line
    auth_import = "from app.core.auth import"
    if auth_import in content:
        content = content.replace(
            auth_import,
            "from app.core.collection_helpers import get_collection_ids, require_collection_id_for_mutation\n" + auth_import
        )

        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✓ Added imports to {filepath}")
        return True

    return False


def update_collection_id_pattern(filepath: str):
    """
    Replace the collection_id retrieval pattern to support superadmin.

    Changes this:
        collection_id = current_user.get('collectionId')
        if not collection_id:
            raise HTTPException(...)

    To this:
        collection_ids = get_collection_ids(current_user, collectionId if 'collectionId' in locals() else None)
        # For single collection operations, use first collection
        collection_id = collection_ids[0] if collection_ids else None
        if not collection_id:
            raise HTTPException(...)
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for the pattern
        if "collection_id = current_user.get('collectionId')" in line:
            # Check if next lines contain the error check
            if i + 2 < len(lines) and "if not collection_id:" in lines[i+1]:
                # Replace the pattern
                indent = len(line) - len(line.lstrip())
                spaces = ' ' * indent

                new_lines.append(f"{spaces}# Get collection IDs (superadmin gets all, regular users get their own)\n")
                new_lines.append(f"{spaces}if current_user.get('role') == 'superadmin':\n")
                new_lines.append(f"{spaces}    # Superadmin: use collectionId param if provided, else get all collections\n")
                new_lines.append(f"{spaces}    collection_ids = get_collection_ids(current_user, locals().get('collectionId'))\n")
                new_lines.append(f"{spaces}else:\n")
                new_lines.append(f"{spaces}    # Regular user: use their assigned collection\n")
                new_lines.append(f"{spaces}    collection_id = current_user.get('collectionId')\n")
                new_lines.append(lines[i+1])  # Keep the "if not collection_id:" check
                new_lines.append(lines[i+2])  # Keep the raise statement
                new_lines.append(f"{spaces}    collection_ids = [collection_id]\n")

                modified = True
                i += 3  # Skip the lines we just replaced
                continue

        new_lines.append(line)
        i += 1

    if modified:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True

    return False


def main():
    """Main function"""
    print("\n" + "="*70)
    print("BATCH UPDATING ROUTERS FOR SUPERADMIN MULTI-COLLECTION SUPPORT")
    print("="*70 + "\n")

    routers = [
        'app/routers/income.py',
        'app/routers/expenses.py',
        'app/routers/blocked_dates.py',
        'app/routers/reports.py',
        'app/routers/export.py',
    ]

    for router in routers:
        print(f"\nProcessing: {router}")
        print("-" * 70)

        try:
            # Step 1: Add imports
            add_collection_helper_imports(router)

            # Step 2: Update collection_id pattern
            if update_collection_id_pattern(router):
                print(f"  ✓ Updated collection_id patterns in {router}")
            else:
                print(f"  - No collection_id patterns to update in {router}")

        except Exception as e:
            print(f"  ❌ Error processing {router}: {e}")

    print("\n" + "="*70)
    print("✅ BATCH UPDATE COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Review the changes in each file")
    print("2. Add 'collectionId' query parameters to GET endpoints")
    print("3. Add 'collectionId' fields to response objects")
    print("4. Test the superadmin functionality")


if __name__ == '__main__':
    main()
