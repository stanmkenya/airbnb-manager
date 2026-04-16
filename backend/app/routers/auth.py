from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.auth import verify_token, get_current_user
from app.firebase_client import firebase_client

router = APIRouter()


class ProfileUpdate(BaseModel):
    displayName: Optional[str] = None
    photoURL: Optional[str] = None


@router.post("/verify")
async def verify_user_token(token_data: dict = Depends(verify_token)):
    """
    Verify Firebase ID token and return user profile
    """
    uid = token_data['uid']
    user_ref = firebase_client.get_database_ref(f'/users/{uid}')
    user_profile = user_ref.get()

    if not user_profile:
        return {
            "uid": uid,
            "email": token_data.get('email'),
            "message": "User profile not found in database"
        }

    return {
        "uid": uid,
        "email": token_data.get('email'),
        "profile": user_profile
    }


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile
    """
    return current_user


@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user profile (display name, photo URL)
    """
    uid = current_user['uid']
    user_ref = firebase_client.get_database_ref(f'/users/{uid}')

    update_data = {}
    if profile_data.displayName is not None:
        update_data['displayName'] = profile_data.displayName
    if profile_data.photoURL is not None:
        update_data['photoURL'] = profile_data.photoURL

    if update_data:
        update_data['updatedAt'] = firebase_client.get_database_ref().push().key
        user_ref.update(update_data)

    return {
        "message": "Profile updated successfully",
        "updated": update_data
    }
