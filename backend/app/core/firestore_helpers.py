"""
Firestore Helper Functions
Provides utility functions for common Firestore operations
"""

from typing import Optional, List, Dict, Any
from google.cloud.firestore_v1 import FieldFilter
from ..firebase_client import firebase_client


def get_firestore_db():
    """Get Firestore database client"""
    return firebase_client.get_firestore()


def get_document(collection_path: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single document from Firestore

    Args:
        collection_path: Path to collection (e.g., 'users' or 'collections/abc/listings')
        doc_id: Document ID

    Returns:
        Document data as dict or None if not found
    """
    db = get_firestore_db()
    doc_ref = db.document(f"{collection_path}/{doc_id}")
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None


def get_documents(collection_path: str, filters: Optional[List[tuple]] = None,
                  order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get multiple documents from a collection with optional filtering

    Args:
        collection_path: Path to collection
        filters: List of tuples (field, operator, value) e.g., [('status', '==', 'active')]
        order_by: Field to order by
        limit: Maximum number of documents to return

    Returns:
        List of documents with their IDs included
    """
    db = get_firestore_db()
    query = db.collection(collection_path)

    # Apply filters
    if filters:
        for field, operator, value in filters:
            query = query.where(filter=FieldFilter(field, operator, value))

    # Apply ordering
    if order_by:
        query = query.order_by(order_by)

    # Apply limit
    if limit:
        query = query.limit(limit)

    # Execute query
    docs = query.stream()

    return [{'id': doc.id, **doc.to_dict()} for doc in docs]


def set_document(collection_path: str, doc_id: str, data: Dict[str, Any], merge: bool = False) -> None:
    """
    Create or overwrite a document

    Args:
        collection_path: Path to collection
        doc_id: Document ID
        data: Document data
        merge: If True, merge with existing data instead of overwriting
    """
    db = get_firestore_db()
    doc_ref = db.document(f"{collection_path}/{doc_id}")
    doc_ref.set(data, merge=merge)


def add_document(collection_path: str, data: Dict[str, Any]) -> str:
    """
    Add a new document with auto-generated ID

    Args:
        collection_path: Path to collection
        data: Document data

    Returns:
        Generated document ID
    """
    db = get_firestore_db()
    col_ref = db.collection(collection_path)
    _, doc_ref = col_ref.add(data)
    return doc_ref.id


def update_document(collection_path: str, doc_id: str, updates: Dict[str, Any]) -> None:
    """
    Update specific fields in a document

    Args:
        collection_path: Path to collection
        doc_id: Document ID
        updates: Dictionary of fields to update
    """
    db = get_firestore_db()
    doc_ref = db.document(f"{collection_path}/{doc_id}")
    doc_ref.update(updates)


def delete_document(collection_path: str, doc_id: str) -> None:
    """
    Delete a document

    Args:
        collection_path: Path to collection
        doc_id: Document ID
    """
    db = get_firestore_db()
    doc_ref = db.document(f"{collection_path}/{doc_id}")
    doc_ref.delete()


def batch_write(operations: List[Dict[str, Any]]) -> None:
    """
    Perform batch write operations (up to 500 operations)

    Args:
        operations: List of operation dicts with keys:
            - 'type': 'set', 'update', or 'delete'
            - 'collection': Collection path
            - 'doc_id': Document ID
            - 'data': Data to write (for set/update)
            - 'merge': Boolean (optional, for set operations)
    """
    db = get_firestore_db()
    batch = db.batch()

    for op in operations:
        doc_ref = db.document(f"{op['collection']}/{op['doc_id']}")

        if op['type'] == 'set':
            merge = op.get('merge', False)
            batch.set(doc_ref, op['data'], merge=merge)
        elif op['type'] == 'update':
            batch.update(doc_ref, op['data'])
        elif op['type'] == 'delete':
            batch.delete(doc_ref)

    batch.commit()


def run_transaction(transaction_func, *args, **kwargs):
    """
    Run a Firestore transaction

    Args:
        transaction_func: Function to execute in transaction
        *args, **kwargs: Arguments to pass to transaction function

    Returns:
        Result from transaction function
    """
    db = get_firestore_db()
    transaction = db.transaction()
    return transaction_func(transaction, *args, **kwargs)


def collection_exists(collection_path: str) -> bool:
    """
    Check if a collection has any documents

    Args:
        collection_path: Path to collection

    Returns:
        True if collection has at least one document
    """
    db = get_firestore_db()
    docs = db.collection(collection_path).limit(1).stream()
    return len(list(docs)) > 0


def count_documents(collection_path: str, filters: Optional[List[tuple]] = None) -> int:
    """
    Count documents in a collection

    Args:
        collection_path: Path to collection
        filters: Optional filters to apply

    Returns:
        Number of documents matching criteria
    """
    db = get_firestore_db()
    query = db.collection(collection_path)

    if filters:
        for field, operator, value in filters:
            query = query.where(filter=FieldFilter(field, operator, value))

    # Note: Firestore doesn't have a native count, so we need to fetch docs
    # For large collections, consider using aggregation queries (newer feature)
    docs = query.stream()
    return sum(1 for _ in docs)


def get_subcollection_documents(parent_collection: str, parent_doc_id: str,
                                subcollection: str) -> List[Dict[str, Any]]:
    """
    Get all documents from a subcollection

    Args:
        parent_collection: Parent collection name (e.g., 'collections')
        parent_doc_id: Parent document ID
        subcollection: Subcollection name (e.g., 'listings')

    Returns:
        List of documents with their IDs
    """
    collection_path = f"{parent_collection}/{parent_doc_id}/{subcollection}"
    return get_documents(collection_path)
