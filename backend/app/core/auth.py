from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.firebase_client import firebase_client
from app.core.firestore_helpers import get_document

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify Firebase ID token from Authorization header.
    Returns decoded token with user info.
    """
    try:
        token = credentials.credentials
        decoded_token = firebase_client.verify_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: dict = Depends(verify_token)) -> dict:
    """
    Get current user info from Firestore using the verified token.
    """
    try:
        uid = token['uid']
        # Use Firestore instead of Realtime Database
        user_data = get_document('users', uid)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        # Check if user is active
        if not user_data.get('isActive', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        return {
            'uid': uid,
            'email': token.get('email'),
            **user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user data: {str(e)}"
        )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require admin role (superadmin or collection_admin) for protected endpoints.
    """
    role = current_user.get('role')
    if role not in ['superadmin', 'collection_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_manager_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require manager or admin role for protected endpoints.
    Allows: manager, collection_admin, superadmin
    """
    role = current_user.get('role')
    if role not in ['manager', 'collection_admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required"
        )
    return current_user
