from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..firebase_client import firebase_client
from ..core.firestore_helpers import (
    get_documents, get_document, add_document,
    update_document, delete_document, set_document
)
from .auth import get_current_user

router = APIRouter(tags=["collections"])


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None


def require_superadmin(current_user: dict = Depends(get_current_user)):
    """Require user to be a super admin"""
    if current_user.get('role') != 'superadmin':
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def require_collection_admin(current_user: dict = Depends(get_current_user)):
    """Require user to be a collection admin or super admin"""
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Collection admin access required")
    return current_user


@router.get("")
async def get_collections(current_user: dict = Depends(get_current_user)):
    """Get all collections (superadmin) or user's collection (others)"""
    try:
        if current_user['role'] == 'superadmin':
            # Super admin sees all collections
            all_collections = get_documents('collections')
            return all_collections
        else:
            # Regular users see only their collection
            collection_id = current_user.get('collectionId')
            if not collection_id:
                raise HTTPException(status_code=404, detail="No collection assigned to user")

            collection_data = get_document('collections', collection_id)
            if not collection_data:
                raise HTTPException(status_code=404, detail="Collection not found")

            return [{'id': collection_id, **collection_data}]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{collection_id}")
async def get_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific collection"""
    try:
        # Check access
        if current_user['role'] != 'superadmin' and current_user.get('collectionId') != collection_id:
            raise HTTPException(status_code=403, detail="Access denied to this collection")

        collection_data = get_document('collections', collection_id)

        if not collection_data:
            raise HTTPException(status_code=404, detail="Collection not found")

        return {'id': collection_id, **collection_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_collection(
    collection: CollectionCreate,
    current_user: dict = Depends(require_superadmin)
):
    """Create a new collection (super admin only)"""
    try:
        collection_data = {
            'name': collection.name,
            'description': collection.description or '',
            'isActive': True,
            'createdAt': datetime.utcnow().isoformat(),
            'createdBy': current_user['email'],
            'userCount': 0
        }

        # Add document with auto-generated ID
        collection_id = add_document('collections', collection_data)

        return {
            'id': collection_id,
            **collection_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{collection_id}")
async def update_collection(
    collection_id: str,
    collection: CollectionUpdate,
    current_user: dict = Depends(require_collection_admin)
):
    """Update a collection"""
    try:
        # Check access
        if current_user['role'] != 'superadmin' and current_user.get('collectionId') != collection_id:
            raise HTTPException(status_code=403, detail="Access denied to this collection")

        existing_collection = get_document('collections', collection_id)

        if not existing_collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Update only provided fields
        update_data = {}
        if collection.name is not None:
            update_data['name'] = collection.name
        if collection.description is not None:
            update_data['description'] = collection.description
        if collection.isActive is not None:
            update_data['isActive'] = collection.isActive

        if update_data:
            update_data['updatedAt'] = datetime.utcnow().isoformat()
            update_document('collections', collection_id, update_data)

        # Return updated collection
        updated_collection = get_document('collections', collection_id)
        return {'id': collection_id, **updated_collection}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(require_superadmin)
):
    """Delete a collection (super admin only)"""
    try:
        collection_data = get_document('collections', collection_id)

        if not collection_data:
            raise HTTPException(status_code=404, detail="Collection not found")

        # TODO: Add check to prevent deletion if collection has data
        # For now, just delete the collection metadata
        delete_document('collections', collection_id)

        return {"message": f"Collection {collection_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
