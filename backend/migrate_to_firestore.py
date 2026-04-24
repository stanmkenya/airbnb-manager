"""
Data Migration Script: Realtime Database → Firestore
Migrates all data from Firebase Realtime Database to Firestore
"""

import sys
import json
from datetime import datetime
from app.firebase_client import firebase_client
from app.core.firestore_helpers import (
    set_document, batch_write, get_firestore_db
)


def backup_realtime_data(output_file='realtime_db_backup.json'):
    """Export all data from Realtime Database to JSON file"""
    print("📦 Backing up Realtime Database data...")

    try:
        # Get root reference
        root_ref = firebase_client.get_database_ref('/')
        all_data = root_ref.get()

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)

        print(f"✅ Backup saved to {output_file}")
        print(f"   Total size: {len(json.dumps(all_data))} characters")
        return all_data
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)


def migrate_users(realtime_data):
    """Migrate users collection"""
    print("\n👥 Migrating users...")

    users = realtime_data.get('users', {})
    if not users:
        print("⚠️  No users found to migrate")
        return 0

    migrated = 0
    batch_ops = []

    for uid, user_data in users.items():
        # Prepare user document
        # Firestore doesn't allow undefined, so convert None to null
        clean_data = {k: (v if v is not None else '') for k, v in user_data.items()}

        batch_ops.append({
            'type': 'set',
            'collection': 'users',
            'doc_id': uid,
            'data': clean_data,
            'merge': False
        })

        migrated += 1

        # Batch write every 500 operations (Firestore limit)
        if len(batch_ops) >= 500:
            batch_write(batch_ops)
            print(f"   Migrated {migrated} users...")
            batch_ops = []

    # Write remaining
    if batch_ops:
        batch_write(batch_ops)

    print(f"✅ Migrated {migrated} users")
    return migrated


def migrate_collections(realtime_data):
    """Migrate collections and their subcollections"""
    print("\n📁 Migrating collections...")

    collections = realtime_data.get('collections', {})
    if not collections:
        print("⚠️  No collections found to migrate")
        return 0

    migrated_collections = 0
    migrated_subcollections = {}

    for collection_id, collection_data in collections.items():
        # Separate collection metadata from subcollections
        metadata = {}
        subcollections = {}

        for key, value in collection_data.items():
            # These are subcollections
            if key in ['listings', 'income', 'expenses', 'blocked_dates']:
                if isinstance(value, dict):
                    subcollections[key] = value
            else:
                # This is metadata
                metadata[key] = value if value is not None else ''

        # Migrate collection document
        set_document('collections', collection_id, metadata)
        migrated_collections += 1
        print(f"   ✓ Collection: {metadata.get('name', collection_id)}")

        # Migrate subcollections
        for subcoll_name, subcoll_data in subcollections.items():
            count = migrate_subcollection(collection_id, subcoll_name, subcoll_data)
            migrated_subcollections[subcoll_name] = migrated_subcollections.get(subcoll_name, 0) + count

    print(f"✅ Migrated {migrated_collections} collections")
    for subcoll_name, count in migrated_subcollections.items():
        print(f"   - {subcoll_name}: {count} documents")

    return migrated_collections


def migrate_subcollection(collection_id, subcollection_name, subcollection_data):
    """Migrate a subcollection under a collection"""
    if not subcollection_data:
        return 0

    batch_ops = []
    migrated = 0

    for doc_id, doc_data in subcollection_data.items():
        # Clean data (remove None values)
        clean_data = {k: (v if v is not None else '') for k, v in doc_data.items()}

        batch_ops.append({
            'type': 'set',
            'collection': f'collections/{collection_id}/{subcollection_name}',
            'doc_id': doc_id,
            'data': clean_data,
            'merge': False
        })

        migrated += 1

        # Batch write every 500 operations
        if len(batch_ops) >= 500:
            batch_write(batch_ops)
            batch_ops = []

    # Write remaining
    if batch_ops:
        batch_write(batch_ops)

    return migrated


def verify_migration():
    """Verify that migration was successful"""
    print("\n🔍 Verifying migration...")

    db = get_firestore_db()

    # Check users
    users_ref = db.collection('users')
    users_count = len(list(users_ref.limit(1000).stream()))
    print(f"   Users in Firestore: {users_count}")

    # Check collections
    collections_ref = db.collection('collections')
    collections_docs = list(collections_ref.stream())
    collections_count = len(collections_docs)
    print(f"   Collections in Firestore: {collections_count}")

    # Check subcollections for each collection
    for coll_doc in collections_docs:
        coll_name = coll_doc.to_dict().get('name', 'Unknown')
        print(f"\n   Collection: {coll_name}")

        for subcoll in ['listings', 'income', 'expenses', 'blocked_dates']:
            subcoll_ref = db.collection(f'collections/{coll_doc.id}/{subcoll}')
            subcoll_count = len(list(subcoll_ref.limit(100).stream()))
            if subcoll_count > 0:
                print(f"      - {subcoll}: {subcoll_count} documents")

    print("\n✅ Verification complete")


def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 Firebase Realtime Database → Firestore Migration")
    print("=" * 60)

    # Confirm before proceeding
    response = input("\n⚠️  This will migrate all data to Firestore. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        sys.exit(0)

    start_time = datetime.now()

    # Step 1: Backup
    realtime_data = backup_realtime_data()

    # Step 2: Migrate users
    users_migrated = migrate_users(realtime_data)

    # Step 3: Migrate collections and subcollections
    collections_migrated = migrate_collections(realtime_data)

    # Step 4: Verify
    verify_migration()

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("✨ Migration Complete!")
    print("=" * 60)
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Users migrated: {users_migrated}")
    print(f"Collections migrated: {collections_migrated}")
    print("\n📋 Next Steps:")
    print("   1. Test the collections API endpoints")
    print("   2. Update remaining routers to use Firestore")
    print("   3. Deploy updated backend")
    print("   4. Keep Realtime DB active for rollback (1 week)")
    print("=" * 60)


if __name__ == '__main__':
    main()
