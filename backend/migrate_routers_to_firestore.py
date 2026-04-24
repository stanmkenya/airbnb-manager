"""
Automated Router Migration Script: Realtime Database → Firestore
Converts all router files to use Firestore helpers
"""

import re
import os

# Router files to migrate
ROUTERS_TO_MIGRATE = [
    'app/routers/listings.py',
    'app/routers/income.py',
    'app/routers/expenses.py',
    'app/routers/blocked_dates.py',
    'app/routers/reports.py',
    'app/routers/export.py',
    'app/routers/auth.py',
]


def add_firestore_imports(content):
    """Add Firestore helper imports to the file"""
    # Check if firestore imports already exist
    if 'firestore_helpers' in content:
        print("  ✓ Firestore imports already present")
        return content

    # Find the import section and add firestore imports
    import_pattern = r'(from app\.firebase_client import firebase_client)'
    replacement = r'\1\nfrom app.core.firestore_helpers import (\n    get_documents, get_document, set_document, add_document,\n    update_document, delete_document, get_subcollection_documents\n)'

    content = re.sub(import_pattern, replacement, content)
    print("  ✓ Added Firestore imports")
    return content


def convert_get_database_ref_to_firestore(content):
    """Convert get_database_ref() calls to Firestore operations"""

    conversions = 0

    # Pattern 1: ref().get() patterns for collections
    # Before: firebase_client.get_database_ref(f'/collections/{cid}/listings')
    #         listings_ref.get() or {}
    # After:  get_subcollection_documents('collections', cid, 'listings')

    # Pattern 2: Simple document get
    # Before: ref = firebase_client.get_database_ref(f'/path/{id}')
    #         data = ref.get()
    # After:  data = get_document('path', id)

    # Pattern 3: ref.set() calls
    # Before: ref.set(data)
    # After:  set_document('collection', doc_id, data)

    # Pattern 4: ref.update() calls
    # Before: ref.update(data)
    # After:  update_document('collection', doc_id, data)

    # Pattern 5: ref.delete() calls
    # Before: ref.delete()
    # After:  delete_document('collection', doc_id)

    # Pattern 6: ref.push() for auto-generated IDs
    # Before: new_ref = ref.push()
    #         new_ref.set(data)
    # After:  doc_id = add_document('collection', data)

    print("  ℹ Manual conversion required - patterns are complex")
    print("    This script adds imports. Manual updates needed for:")
    print("    - get_database_ref() → get_document/get_documents()")
    print("    - ref.set() → set_document()")
    print("    - ref.update() → update_document()")
    print("    - ref.delete() → delete_document()")
    print("    - ref.push() → add_document()")

    return content, conversions


def migrate_router_file(filepath):
    """Migrate a single router file to Firestore"""
    print(f"\n📄 Migrating {filepath}...")

    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filepath}")
        return False

    # Read file
    with open(filepath, 'r') as f:
        content = f.read()

    # Backup original
    backup_path = filepath + '.rtdb_backup'
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"  💾 Backup created: {backup_path}")

    # Apply migrations
    original_content = content
    content = add_firestore_imports(content)
    content, conversions = convert_get_database_ref_to_firestore(content)

    # Save if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ File updated with Firestore imports")
        return True
    else:
        print(f"  ⚠️  No changes made")
        return False


def print_manual_conversion_guide():
    """Print guide for manual conversions"""
    print("\n" + "="*60)
    print("📖 MANUAL CONVERSION GUIDE")
    print("="*60)
    print("""
The imports have been added. Now manually convert these patterns:

1. GET COLLECTION (iterate over all docs)
   ❌ Before:
      ref = firebase_client.get_database_ref(f'/collections/{cid}/listings')
      data = ref.get() or {}
      for listing_id, listing_data in data.items():
          all_listings.append({'id': listing_id, **listing_data})

   ✅ After:
      listings = get_subcollection_documents('collections', cid, 'listings')
      all_listings.extend(listings)

2. GET DOCUMENT
   ❌ Before:
      ref = firebase_client.get_database_ref(f'/users/{uid}')
      data = ref.get()

   ✅ After:
      data = get_document('users', uid)

3. CREATE WITH AUTO-ID
   ❌ Before:
      ref = firebase_client.get_database_ref(f'/collections/{cid}/listings')
      new_ref = ref.push()
      listing_id = new_ref.key
      new_ref.set(data)

   ✅ After:
      listing_id = add_document(f'collections/{cid}/listings', data)

4. CREATE/SET WITH SPECIFIC ID
   ❌ Before:
      ref = firebase_client.get_database_ref(f'/users/{uid}')
      ref.set(data)

   ✅ After:
      set_document('users', uid, data)

5. UPDATE
   ❌ Before:
      ref = firebase_client.get_database_ref(f'/users/{uid}')
      ref.update(updates)

   ✅ After:
      update_document('users', uid, updates)

6. DELETE
   ❌ Before:
      ref = firebase_client.get_database_ref(f'/path/{id}')
      ref.delete()

   ✅ After:
      delete_document('path', id)

7. DELETE FIELD (like in users.py)
   ❌ Before:
      user_ref.child('collectionId').delete()

   ✅ After:
      from google.cloud.firestore import DELETE_FIELD
      update_data['collectionId'] = DELETE_FIELD
      update_document('users', uid, update_data)
""")


def main():
    """Main migration function"""
    print("="*60)
    print("🔄 Router Migration: Realtime DB → Firestore")
    print("="*60)

    migrated = []
    failed = []

    for router_path in ROUTERS_TO_MIGRATE:
        try:
            if migrate_router_file(router_path):
                migrated.append(router_path)
            else:
                failed.append(router_path)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed.append(router_path)

    # Summary
    print("\n" + "="*60)
    print("📊 MIGRATION SUMMARY")
    print("="*60)
    print(f"✅ Successfully added imports: {len(migrated)}")
    for path in migrated:
        print(f"   - {path}")

    if failed:
        print(f"\n⚠️  Needs attention: {len(failed)}")
        for path in failed:
            print(f"   - {path}")

    print_manual_conversion_guide()

    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("="*60)
    print("1. Review each router file listed above")
    print("2. Follow the manual conversion guide")
    print("3. Look at users.py and collections.py as examples")
    print("4. Test each endpoint after conversion")
    print("5. Run migration script again if needed")
    print("="*60)


if __name__ == '__main__':
    main()
