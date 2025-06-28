from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import MentorListItem, MentorProfileDetails, MatchRequestCreate, MatchRequest, MatchRequestOutgoing
from app.auth import get_current_user
from app.models.user import User, MatchRequest as MatchRequestModel
from app.crud import (
    get_mentors, create_match_request, get_incoming_match_requests, 
    get_outgoing_match_requests, accept_match_request, reject_match_request, 
    cancel_match_request, get_match_request_by_id, get_user_by_id
)
from typing import Optional, List
from sqlalchemy import and_

router = APIRouter()

@router.get("/mentors", response_model=List[MentorListItem])
async def get_mentors_list(
    skill: Optional[str] = Query(None),
    orderBy: Optional[str] = Query(None, regex="^(skill|name)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘티만 접근 가능
        if current_user.role != "mentee":
            raise HTTPException(
                status_code=403,
                detail="Only mentees can access mentor list"
            )
        
        # orderBy를 order_by로 변환
        order_by = orderBy if orderBy else None
        mentors = get_mentors(db, skill=skill, order_by=order_by)
        
        mentor_list = []
        for mentor in mentors:
            profile = MentorProfileDetails(
                name=mentor.name,
                bio=mentor.bio or "",
                imageUrl=f"/images/mentor/{mentor.id}",
                skills=mentor.skills or []
            )
            mentor_item = MentorListItem(
                id=mentor.id,
                email=mentor.email,
                role="mentor",
                profile=profile
            )
            mentor_list.append(mentor_item)
        
        return mentor_list
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/match-requests", response_model=MatchRequest)
async def create_match_request_endpoint(
    request_data: MatchRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘티만 접근 가능
        if current_user.role != "mentee":
            raise HTTPException(
                status_code=403,
                detail="Only mentees can send match requests"
            )
        
        # 요청하는 멘티가 현재 사용자인지 확인
        if request_data.menteeId != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Can only send requests for yourself"
            )
        
        # 멘토가 존재하는지 확인
        mentor = get_user_by_id(db, request_data.mentorId)
        if not mentor or mentor.role != "mentor":
            raise HTTPException(
                status_code=400,
                detail="Mentor not found"
            )
        
        # 매칭 요청 생성
        match_request = create_match_request(db, request_data)
        if not match_request:
            # 더 구체적인 에러 메시지 제공
            existing_pending = db.query(MatchRequestModel).filter(
                and_(
                    MatchRequestModel.mentee_id == request_data.menteeId,
                    MatchRequestModel.status == "pending"
                )
            ).first()
            
            if existing_pending:
                raise HTTPException(
                    status_code=400,
                    detail="You already have a pending request. Please wait for a response or cancel it before sending a new request."
                )
            
            existing_to_same_mentor = db.query(MatchRequestModel).filter(
                and_(
                    MatchRequestModel.mentor_id == request_data.mentorId,
                    MatchRequestModel.mentee_id == request_data.menteeId
                )
            ).first()
            
            if existing_to_same_mentor:
                raise HTTPException(
                    status_code=400,
                    detail="You have already sent a request to this mentor."
                )
            
            raise HTTPException(
                status_code=400,
                detail="Unable to create match request"
            )
        
        return MatchRequest(
            id=match_request.id,
            mentorId=match_request.mentor_id,
            menteeId=match_request.mentee_id,
            message=match_request.message,
            status=match_request.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/match-requests/incoming", response_model=List[MatchRequest])
async def get_incoming_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘토만 접근 가능
        if current_user.role != "mentor":
            raise HTTPException(
                status_code=403,
                detail="Only mentors can view incoming requests"
            )
        
        requests = get_incoming_match_requests(db, current_user.id)
        
        return [
            MatchRequest(
                id=req.id,
                mentorId=req.mentor_id,
                menteeId=req.mentee_id,
                message=req.message,
                status=req.status
            )
            for req in requests
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/match-requests/outgoing", response_model=List[MatchRequestOutgoing])
async def get_outgoing_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘티만 접근 가능
        if current_user.role != "mentee":
            raise HTTPException(
                status_code=403,
                detail="Only mentees can view outgoing requests"
            )
        
        requests = get_outgoing_match_requests(db, current_user.id)
        
        return [
            MatchRequestOutgoing(
                id=req.id,
                mentorId=req.mentor_id,
                menteeId=req.mentee_id,
                status=req.status
            )
            for req in requests
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.put("/match-requests/{request_id}/accept", response_model=MatchRequest)
async def accept_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘토만 접근 가능
        if current_user.role != "mentor":
            raise HTTPException(
                status_code=403,
                detail="Only mentors can accept requests"
            )
        
        match_request = accept_match_request(db, request_id, current_user.id)
        if not match_request:
            raise HTTPException(
                status_code=404,
                detail="Match request not found"
            )
        
        return MatchRequest(
            id=match_request.id,
            mentorId=match_request.mentor_id,
            menteeId=match_request.mentee_id,
            message=match_request.message,
            status=match_request.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.put("/match-requests/{request_id}/reject", response_model=MatchRequest)
async def reject_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘토만 접근 가능
        if current_user.role != "mentor":
            raise HTTPException(
                status_code=403,
                detail="Only mentors can reject requests"
            )
        
        match_request = reject_match_request(db, request_id, current_user.id)
        if not match_request:
            raise HTTPException(
                status_code=404,
                detail="Match request not found"
            )
        
        return MatchRequest(
            id=match_request.id,
            mentorId=match_request.mentor_id,
            menteeId=match_request.mentee_id,
            message=match_request.message,
            status=match_request.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.delete("/match-requests/{request_id}", response_model=MatchRequest)
async def cancel_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘티만 접근 가능
        if current_user.role != "mentee":
            raise HTTPException(
                status_code=403,
                detail="Only mentees can cancel requests"
            )
        
        match_request = cancel_match_request(db, request_id, current_user.id)
        if not match_request:
            raise HTTPException(
                status_code=404,
                detail="Match request not found"
            )
        
        return MatchRequest(
            id=match_request.id,
            mentorId=match_request.mentor_id,
            menteeId=match_request.mentee_id,
            message=match_request.message,
            status=match_request.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )