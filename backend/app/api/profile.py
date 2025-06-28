from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import User as UserProfile, MentorProfile, MenteeProfile, UpdateMentorProfileRequest, UpdateMenteeProfileRequest, ErrorResponse
from app.auth import get_current_user
from app.models.user import User
from app.crud import update_user_profile, get_user_by_id
from typing import Union

router = APIRouter()

def create_profile_response(user: User):
    """사용자 정보를 프로필 응답 형태로 변환"""
    if user.role == "mentor":
        profile = {
            "name": user.name,
            "bio": user.bio or "",
            "imageUrl": f"/images/mentor/{user.id}",
            "skills": user.skills or []
        }
        return MentorProfile(
            id=user.id,
            email=user.email,
            role="mentor",
            profile=profile
        )
    else:
        profile = {
            "name": user.name,
            "bio": user.bio or "",
            "imageUrl": f"/images/mentee/{user.id}"
        }
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

@router.get("/images/{role}/{user_id}",
           summary="Get profile image",
           description="Retrieve the profile image for a specific user",
           responses={
               200: {"description": "Profile image retrieved successfully"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               404: {"model": ErrorResponse, "description": "User or image not found"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def get_profile_image(
    role: str,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 역할 검증
        if role not in ["mentor", "mentee"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Must be 'mentor' or 'mentee'"
            )
        
        # 사용자 찾기
        user = get_user_by_id(db, user_id)
        if not user or user.role != role:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # 프로필 이미지가 있는 경우 반환
        if user.profile_image:
            # 이미지 형식 감지
            if user.profile_image.startswith(b'\xff\xd8'):
                media_type = "image/jpeg"
            elif user.profile_image.startswith(b'\x89PNG'):
                media_type = "image/png"
            else:
                media_type = "image/jpeg"  # 기본값
            
            return Response(content=user.profile_image, media_type=media_type)
        else:
            # 기본 이미지로 리다이렉트
            from fastapi.responses import RedirectResponse
            if role == "mentor":
                return RedirectResponse(url="https://placehold.co/500x500.jpg?text=MENTOR")
            else:
                return RedirectResponse(url="https://placehold.co/500x500.jpg?text=MENTEE")
    
    except HTTPException:
        raise
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
        # 프로필 데이터의 사용자 ID가 현재 사용자와 일치하는지 확인
        if profile_data.id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own profile"
            )
        
        # 역할이 일치하는지 확인
        if profile_data.role != current_user.role:
            raise HTTPException(
                status_code=400,
                detail="Role cannot be changed"
            )
        
        # 프로필 업데이트
        updated_user = update_user_profile(db, current_user, profile_data)
        return create_profile_response(updated_user)
    
    except ValueError as e:
        # 이미지 검증 오류
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="서버 내부 오류가 발생했습니다"
        )