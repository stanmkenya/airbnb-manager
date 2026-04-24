"""
Script to update income, expenses, and blocked_dates routers to be collection-aware.
Replaces paths like /listings, /income, /expenses, /blocked-dates with collection-scoped paths.
"""

import re
import sys

def get_collection_id_snippet():
    """Return the code snippet to get collectionId"""
    return """    # Get user's collection
    collection_id = current_user.get('collectionId')
    if not collection_id:
        raise HTTPException(status_code=400, detail="User not assigned to a collection")
"""

def update_income_router():
    """Update income router to be collection-aware"""
    print("Updating income router...")

    with open('app/routers/income.py', 'r') as f:
        content = f.read()

    # Replace role checks
    content = content.replace("current_user['role'] == 'admin'", "current_user['role'] in ['collection_admin', 'superadmin']")
    content = content.replace("current_user['role'] != 'admin'", "current_user['role'] not in ['collection_admin', 'superadmin']")

    # Replace /listings path references
    content = re.sub(
        r"firebase_client\.get_database_ref\('/listings'\)",
        "firebase_client.get_database_ref(f'/collections/{collection_id}/listings')",
        content
    )

    # Replace /income/{lid} path references
    content = re.sub(
        r"firebase_client\.get_database_ref\(f'/income/\{([^}]+)\}'\)",
        r"firebase_client.get_database_ref(f'/collections/{collection_id}/income/{\1}')",
        content
    )

    # Add collection_id retrieval to functions that need it
    # Find all async def functions and add collection retrieval after current_user
    def add_collection_retrieval(match):
        func_def = match.group(0)
        # Check if it already has collection_id code
        if 'collection_id = current_user.get' in func_def:
            return func_def

        # Add collection retrieval after the function definition
        lines = func_def.split('\n')
        # Find where to insert (after docstring if exists, otherwise after def line)
        insert_idx = 1
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                # Find end of docstring
                for j in range(i+1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        insert_idx = j + 1
                        break
                break

        lines.insert(insert_idx, get_collection_id_snippet())
        return '\n'.join(lines)

    # Apply to all async functions that use database
    content = re.sub(
        r'(@router\.(get|post|put|delete)\([^)]+\)\s*\nasync def [^:]+:\s*\n(?:    """[^"]*"""\s*\n)?)',
        add_collection_retrieval,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    with open('app/routers/income.py', 'w') as f:
        f.write(content)

    print("✓ Income router updated")


def update_expenses_router():
    """Update expenses router to be collection-aware"""
    print("Updating expenses router...")

    with open('app/routers/expenses.py', 'r') as f:
        content = f.read()

    # Replace role checks
    content = content.replace("current_user['role'] == 'admin'", "current_user['role'] in ['collection_admin', 'superadmin']")
    content = content.replace("current_user['role'] != 'admin'", "current_user['role'] not in ['collection_admin', 'superadmin']")

    # Replace /listings path references
    content = re.sub(
        r"firebase_client\.get_database_ref\('/listings'\)",
        "firebase_client.get_database_ref(f'/collections/{collection_id}/listings')",
        content
    )

    # Replace /expenses/{lid} path references
    content = re.sub(
        r"firebase_client\.get_database_ref\(f'/expenses/\{([^}]+)\}'\)",
        r"firebase_client.get_database_ref(f'/collections/{collection_id}/expenses/{\1}')",
        content
    )

    with open('app/routers/expenses.py', 'w') as f:
        f.write(content)

    print("✓ Expenses router updated")


def update_blocked_dates_router():
    """Update blocked_dates router to be collection-aware"""
    print("Updating blocked_dates router...")

    with open('app/routers/blocked_dates.py', 'r') as f:
        content = f.read()

    # Replace role checks
    content = content.replace("'admin'", "'collection_admin', 'superadmin'")
    content = content.replace("'manager'", "'manager', 'collection_admin', 'superadmin'")

    # Replace /blocked-dates path references
    content = re.sub(
        r"firebase_client\.get_database_ref\('/blocked-dates'\)",
        "firebase_client.get_database_ref(f'/collections/{collection_id}/blocked-dates')",
        content
    )

    content = re.sub(
        r"firebase_client\.get_database_ref\(f'/blocked-dates/\{([^}]+)\}'\)",
        r"firebase_client.get_database_ref(f'/collections/{collection_id}/blocked-dates/{\1}')",
        content
    )

    # Replace /listings references
    content = re.sub(
        r"firebase_client\.get_database_ref\(f'/listings/\{([^}]+)\}'\)",
        r"firebase_client.get_database_ref(f'/collections/{collection_id}/listings/{\1}')",
        content
    )

    with open('app/routers/blocked_dates.py', 'w') as f:
        f.write(content)

    print("✓ Blocked dates router updated")


def main():
    print("="*60)
    print("UPDATING ROUTERS FOR COLLECTION SUPPORT")
    print("="*60)
    print()

    try:
        update_income_router()
        update_expenses_router()
        update_blocked_dates_router()

        print()
        print("="*60)
        print("✅ ALL ROUTERS UPDATED SUCCESSFULLY")
        print("="*60)
        print()
        print("Note: You may need to manually add collection_id retrieval")
        print("to functions that don't have it yet.")
        print("Look for: collection_id = current_user.get('collectionId')")

    except Exception as e:
        print()
        print("="*60)
        print("❌ ERROR UPDATING ROUTERS")
        print("="*60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
