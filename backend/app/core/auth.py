from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.firebase_client import firebase_client

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
    Get current user info from database using the verified token.
    """
    try:
        uid = token['uid']
        user_ref = firebase_client.get_database_ref(f'/users/{uid}')
        user_data = user_ref.get()

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
    Require admin role for protected endpoints.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_manager_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require manager or admin role for protected endpoints.
    """
    role = current_user.get('role')
    if role not in ['manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required"
        )
    return current_user
