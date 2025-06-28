from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import SignupRequest, LoginRequest, LoginResponse, ErrorResponse
from app.crud import get_user_by_email, create_user
from app.core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/signup", status_code=201)
async def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    try:
        # 이메일 중복 확인
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="이미 등록된 이메일입니다"
            )
        
        # 사용자 생성
        user = create_user(db, user_data)
        return {"message": "사용자가 성공적으로 생성되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="서버 내부 오류가 발생했습니다"
        )

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        # 사용자 찾기
        user = get_user_by_email(db, login_data.email)
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )
        
        # JWT 토큰 생성
        token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        })
        
        return LoginResponse(token=token)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="서버 내부 오류가 발생했습니다"
        )