"""
Comprehensive Batch Router Conversion: Realtime DB → Firestore
Automatically converts all remaining routers to use Firestore
"""

import re
import os
import shutil

ROUTERS = [
    'app/routers/listings.py',
    'app/routers/income.py',
    'app/routers/expenses.py',
    'app/routers/blocked_dates.py',
    'app/routers/reports.py',
    'app/routers/export.py',
    'app/routers/auth.py',
]


def backup_file(filepath):
    """Create backup of original file"""
    backup = filepath + '.pre_firestore'
    shutil.copy2(filepath, backup)
    return backup


def add_firestore_imports(content):
    """Add Firestore imports after firebase_client import"""
    if 'firestore_helpers' in content:
        return content

    pattern = r'(from (?:app\.)?firebase_client import firebase_client)'
    replacement = r'\1\nfrom app.core.firestore_helpers import (\n    get_documents, get_document, set_document, add_document,\n    update_document, delete_document, get_subcollection_documents\n)'

    return re.sub(pattern, replacement, content)


def convert_get_operations(content):
    """Convert get_database_ref().get() patterns"""

    # Pattern: Get subcollection documents and iterate
    # listings_ref = firebase_client.get_database_ref(f'/collections/{cid}/listings')
    # collection_listings = listings_ref.get() or {}
    # for listing_id, listing_data in collection_listings.items():

    pattern1 = r"(\w+)_ref\s*=\s*firebase_client\.get_database_ref\(f?['\"]\/collections\/\{(\w+)\}\/(\w+)['\"]?\)\s*\n\s*(\w+)\s*=\s*\1_ref\.get\(\)\s*(?:or\s*\{\})?"

    def replace_subcollection_get(match):
        var_name = match.group(1)
        coll_id_var = match.group(2)
        subcoll_name = match.group(3)
        result_var = match.group(4)

        return f'{result_var} = get_subcollection_documents("collections", {coll_id_var}, "{subcoll_name}")'

    content = re.sub(pattern1, replace_subcollection_get, content)

    # Pattern: Simple document get with variable storage
    # ref = firebase_client.get_database_ref(f'/users/{uid}')
    # data = ref.get()

    pattern2 = r'(\w+)_ref\s*=\s*firebase_client\.get_database_ref\(f?[\'"]\/(\w+)\/\{(\w+)\}[\'"]?\)\s*\n\s*(\w+)\s*=\s*\1_ref\.get\(\)'

    def replace_document_get(match):
        var_name = match.group(1)
        collection = match.group(2)
        doc_id_var = match.group(3)
        result_var = match.group(4)

        return f'{result_var} = get_document("{collection}", {doc_id_var})'

    content = re.sub(pattern2, replace_document_get, content)

    # Pattern: Inline get for collections with subcollection
    # firebase_client.get_database_ref(f'/collections/{cid}/listings/{lid}').get()

    pattern3 = r'firebase_client\.get_database_ref\(f?[\'"]\/collections\/\{(\w+)\}\/(\w+)\/\{(\w+)\}[\'"]?\)\.get\(\)'

    def replace_inline_subcoll_get(match):
        coll_id = match.group(1)
        subcoll_name = match.group(2)
        doc_id = match.group(3)

        return f'get_document(f"collections/{{{coll_id}}}/{subcoll_name}", {doc_id})'

    content = re.sub(pattern3, replace_inline_subcoll_get, content)

    return content


def convert_set_operations(content):
    """Convert ref.set() patterns"""

    # Pattern: ref.push().set() for auto-generated IDs
    # new_ref = listings_ref.push()
    # listing_id = new_ref.key
    # new_ref.set(data)

    pattern = r'(\w+)_ref\s*=\s*firebase_client\.get_database_ref\(f?[\'"]\/collections\/\{(\w+)\}\/(\w+)[\'"]?\)\s*\n\s*new_(\w+)_ref\s*=\s*\1_ref\.push\(\)\s*\n(?:\s*(\w+)\s*=\s*new_\4_ref\.key\s*\n)?'

    def replace_push_pattern(match):
        ref_var = match.group(1)
        coll_id = match.group(2)
        subcoll_name = match.group(3)
        entity_type = match.group(4)
        id_var = match.group(5) if match.group(5) else f'{entity_type}_id'

        return f'{id_var} = "PLACEHOLDER_FOR_ADD_DOCUMENT"  # TODO: Replace with: add_document(f"collections/{{{coll_id}}}/{subcoll_name}", data)'

    content = re.sub(pattern, replace_push_pattern, content)

    # Pattern: Direct set with explicit ID
    # ref = firebase_client.get_database_ref(f'/users/{uid}')
    # ref.set(data)

    pattern2 = r'(\w+)_ref\s*=\s*firebase_client\.get_database_ref\(f?[\'"]\/(\w+)\/\{(\w+)\}[\'"]?\)\s*\n.*?\n\s*\1_ref\.set\((\w+)\)'

    def replace_set(match):
        collection = match.group(2)
        doc_id = match.group(3)
        data_var = match.group(4)

        return f'set_document("{collection}", {doc_id}, {data_var})'

    # This pattern is complex, skip for manual review
    return content


def convert_update_operations(content):
    """Convert ref.update() patterns"""

    # Pattern: ref.update(data)
    # listing_ref.update(update_data)

    # This is complex because we need the collection path and doc ID
    # Let's convert the simpler inline patterns

    pattern = r'firebase_client\.get_database_ref\(f?[\'"]\/collections\/\{(\w+)\}\/(\w+)\/\{(\w+)\}[\'"]?\)\.update\(([^)]+)\)'

    def replace_update(match):
        coll_id = match.group(1)
        subcoll = match.group(2)
        doc_id = match.group(3)
        data = match.group(4)

        return f'update_document(f"collections/{{{coll_id}}}/{subcoll}", {doc_id}, {data})'

    content = re.sub(pattern, replace_update, content)

    return content


def convert_delete_operations(content):
    """Convert ref.delete() patterns"""

    pattern = r'firebase_client\.get_database_ref\(f?[\'"]\/collections\/\{(\w+)\}\/(\w+)\/\{(\w+)\}[\'"]?\)\.delete\(\)'

    def replace_delete(match):
        coll_id = match.group(1)
        subcoll = match.group(2)
        doc_id = match.group(3)

        return f'delete_document(f"collections/{{{coll_id}}}/{subcoll}", {doc_id})'

    content = re.sub(pattern, replace_delete, content)

    return content


def convert_router_file(filepath):
    """Convert a single router file"""
    print(f"\n📄 Converting {filepath}...")

    if not os.path.exists(filepath):
        print(f"  ❌ Not found")
        return False

    # Backup
    backup = backup_file(filepath)
    print(f"  💾 Backed up to {backup}")

    # Read
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Apply conversions
    content = add_firestore_imports(content)
    content = convert_get_operations(content)
    content = convert_set_operations(content)
    content = convert_update_operations(content)
    content = convert_delete_operations(content)

    # Save
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Converted")
        return True
    else:
        print(f"  ⚠️  No changes")
        return False


def main():
    print("="*70)
    print("🔄 BATCH ROUTER CONVERSION: Realtime DB → Firestore")
    print("="*70)

    converted = []
    for router in ROUTERS:
        try:
            if convert_router_file(router):
                converted.append(router)
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "="*70)
    print("📊 CONVERSION SUMMARY")
    print("="*70)
    print(f"✅ Converted: {len(converted)}/{len(ROUTERS)} files")
    for r in converted:
        print(f"   - {r}")

    print("\n⚠️  IMPORTANT: Manual review required!")
    print("   Some patterns are too complex for automatic conversion.")
    print("   Please review each file and look for:")
    print("   - TODO comments")
    print("   - PLACEHOLDER markers")
    print("   - Complex ref.push() patterns")
    print("   - Nested get() operations")
    print("\n   Use collections.py and users.py as reference examples.")
    print("="*70)


if __name__ == '__main__':
    main()
