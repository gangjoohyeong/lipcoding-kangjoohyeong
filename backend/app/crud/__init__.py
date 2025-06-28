from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import User, MatchRequest
from app.schemas.user import SignupRequest, UpdateMentorProfileRequest, UpdateMenteeProfileRequest, MatchRequestCreate
from app.core.security import get_password_hash
import base64
from typing import Optional, List
from PIL import Image
import io

# 사용자 관련 CRUD
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: SignupRequest):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        name=user.name,
        role=user.role,
        bio="",
        skills=[] if user.role == "mentor" else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, user: User, profile_data):
    user.name = profile_data.name
    user.bio = profile_data.bio
    
    # Base64 이미지 디코딩 및 검증
    if profile_data.image:
        try:
            # Base64 디코딩
            image_data = base64.b64decode(profile_data.image)
            
            # 파일 크기 검증 (1MB = 1024 * 1024 bytes)
            if len(image_data) > 1024 * 1024:
                raise ValueError("이미지 파일 크기는 1MB를 초과할 수 없습니다")
            
            # 이미지 형식 및 크기 검증
            image = Image.open(io.BytesIO(image_data))
            
            # 형식 검증 (.jpg, .png만 허용)
            if image.format not in ['JPEG', 'PNG']:
                raise ValueError("이미지 형식은 JPG 또는 PNG만 허용됩니다")
            
            # 이미지 크기 검증 (500x500 ~ 1000x1000)
            width, height = image.size
            if width < 500 or height < 500 or width > 1000 or height > 1000:
                raise ValueError("이미지 크기는 500x500 ~ 1000x1000 픽셀이어야 합니다")
            
            # 정사각형 검증
            if width != height:
                raise ValueError("이미지는 정사각형이어야 합니다")
            
            user.profile_image = image_data
        except ValueError as e:
            # 검증 오류는 다시 발생시켜서 API에서 처리하도록
            raise e
        except Exception:
            raise ValueError("이미지 처리 중 오류가 발생했습니다")
    
    if hasattr(profile_data, 'skills'):
        user.skills = profile_data.skills
    
    db.commit()
    db.refresh(user)
    return user

# 멘토 관련 CRUD
def get_mentors(db: Session, skill: Optional[str] = None, order_by: Optional[str] = None):
    query = db.query(User).filter(User.role == "mentor")
    
    if skill:
        # JSON 배열에서 특정 스킬 검색
        query = query.filter(User.skills.contains(f'"{skill}"'))
    
    if order_by == "name":
        query = query.order_by(User.name)
    elif order_by == "skill":
        query = query.order_by(User.skills)
    else:
        query = query.order_by(User.id)
    
    return query.all()

# 매칭 요청 관련 CRUD
def create_match_request(db: Session, request_data: MatchRequestCreate):
    # 멘티가 이미 pending 상태의 요청을 가지고 있는지 확인
    existing_pending_request = db.query(MatchRequest).filter(
        and_(
            MatchRequest.mentee_id == request_data.menteeId,
            MatchRequest.status == "pending"
        )
    ).first()
    
    if existing_pending_request:
        return None  # 이미 pending 요청이 있음
    
    # 같은 멘토에게 pending 상태의 요청이 있는지만 확인 (거절/취소된 경우는 재요청 가능)
    existing_pending_to_mentor = db.query(MatchRequest).filter(
        and_(
            MatchRequest.mentor_id == request_data.mentorId,
            MatchRequest.mentee_id == request_data.menteeId,
            MatchRequest.status == "pending"
        )
    ).first()
    
    if existing_pending_to_mentor:
        return None  # 이미 해당 멘토에게 pending 요청이 있음
    
    # 새 요청 생성
    new_request = MatchRequest(
        mentor_id=request_data.mentorId,
        mentee_id=request_data.menteeId,
        message=request_data.message,
        status="pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

def get_incoming_match_requests(db: Session, mentor_id: int):
    # 모든 상태의 요청 반환 (API 명세에 따라)
    return db.query(MatchRequest).filter(MatchRequest.mentor_id == mentor_id).all()

def get_outgoing_match_requests(db: Session, mentee_id: int):
    return db.query(MatchRequest).filter(MatchRequest.mentee_id == mentee_id).all()

def get_match_request_by_id(db: Session, request_id: int):
    return db.query(MatchRequest).filter(MatchRequest.id == request_id).first()

def accept_match_request(db: Session, request_id: int, mentor_id: int):
    # 해당 요청 찾기
    request = db.query(MatchRequest).filter(
        and_(
            MatchRequest.id == request_id,
            MatchRequest.mentor_id == mentor_id
        )
    ).first()
    
    if not request:
        return None
    
    # 멘토의 다른 모든 요청을 거절 처리
    db.query(MatchRequest).filter(
        and_(
            MatchRequest.mentor_id == mentor_id,
            MatchRequest.id != request_id,
            MatchRequest.status == "pending"
        )
    ).update({"status": "rejected"})
    
    # 해당 요청을 수락
    request.status = "accepted"
    db.commit()
    db.refresh(request)
    return request

def reject_match_request(db: Session, request_id: int, mentor_id: int):
    request = db.query(MatchRequest).filter(
        and_(
            MatchRequest.id == request_id,
            MatchRequest.mentor_id == mentor_id
        )
    ).first()
    
    if not request:
        return None
    
    request.status = "rejected"
    db.commit()
    db.refresh(request)
    return request

def cancel_match_request(db: Session, request_id: int, mentee_id: int):
    request = db.query(MatchRequest).filter(
        and_(
            MatchRequest.id == request_id,
            MatchRequest.mentee_id == mentee_id
        )
    ).first()
    
    if not request:
        return None
    
    request.status = "cancelled"
    db.commit()
    db.refresh(request)
    return request