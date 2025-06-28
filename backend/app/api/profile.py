from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import MentorProfile, MenteeProfile, UpdateMentorProfileRequest, UpdateMenteeProfileRequest, MentorProfileDetails, MenteeProfileDetails, ErrorResponse
from app.auth import get_current_user
from app.models.user import User
from app.crud import update_user_profile
from typing import Union
import io

router = APIRouter()

def create_profile_response(user: User):
    """사용자 객체를 프로필 응답으로 변환"""
    image_url = f"/images/{user.role}/{user.id}"
    
    if user.role == "mentor":
        profile = MentorProfileDetails(
            name=user.name,
            bio=user.bio or "",
            imageUrl=image_url,
            skills=user.skills or []
        )
        return MentorProfile(
            id=user.id,
            email=user.email,
            role="mentor",
            profile=profile
        )
    else:
        profile = MenteeProfileDetails(
            name=user.name,
            bio=user.bio or "",
            imageUrl=image_url
        )
        return MenteeProfile(
            id=user.id,
            email=user.email,
            role="mentee",
            profile=profile
        )

@router.get("/me",
           summary="Get current user information",
           description="Retrieve the profile information of the currently authenticated user",
           responses={
               200: {"description": "User information retrieved successfully"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    try:
        return create_profile_response(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.put("/profile",
           summary="Update user profile",
           description="Update the profile information of the currently authenticated user",
           responses={
               200: {"description": "Profile updated successfully"},
               400: {"model": ErrorResponse, "description": "Bad request - invalid payload format"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def update_profile(
    profile_data: Union[UpdateMentorProfileRequest, UpdateMenteeProfileRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 권한 확인
        if profile_data.id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update this profile"
            )
        
        # 역할 확인
        if profile_data.role != current_user.role:
            raise HTTPException(
                status_code=400,
                detail="Role mismatch"
            )
        
        # 프로필 업데이트
        updated_user = update_user_profile(db, current_user, profile_data)
        return create_profile_response(updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/images/{role}/{user_id}",
           summary="Get profile image",
           description="Retrieve the profile image for a specific user",
           responses={
               200: {"description": "Profile image retrieved successfully"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def get_profile_image(
    role: str,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 사용자 찾기
        from app.crud import get_user_by_id
        user = get_user_by_id(db, user_id)
        
        if not user or user.role != role:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 프로필 이미지가 있으면 반환, 없으면 기본 이미지 URL로 리다이렉트
        if user.profile_image:
            return Response(
                content=user.profile_image,
                media_type="image/jpeg"
            )
        else:
            # 기본 이미지 URL로 리다이렉트
            default_text = "MENTOR" if role == "mentor" else "MENTEE"
            default_url = f"https://placehold.co/500x500.jpg?text={default_text}"
            return Response(
                status_code=302,
                headers={"Location": default_url}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )