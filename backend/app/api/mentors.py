from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import MentorListItem, MentorProfileDetails, MatchRequestCreate, MatchRequest, MatchRequestOutgoing, ErrorResponse
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

@router.get("/mentors", 
           response_model=List[MentorListItem],
           summary="Get list of mentors (mentee only)",
           description="Retrieve a list of all mentors, with optional filtering and sorting",
           responses={
               200: {"description": "Mentor list retrieved successfully"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def get_mentors_list(
    skill: Optional[str] = Query(None, description="Filter mentors by skill set (only one skill at a time)"),
    orderBy: Optional[str] = Query(None, regex="^(skill|name)$", description="Sort mentors by skill or name (ascending order)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘티만 접근 가능
        if current_user.role != "mentee":
            raise HTTPException(
                status_code=403,
                detail="멘티만 멘토 목록에 접근할 수 있습니다"
            )
        
        mentors = get_mentors(db, skill=skill, order_by=orderBy)
        
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

@router.post("/match-requests", 
            response_model=MatchRequest,
            summary="Send match request (mentee only)",
            description="Send a matching request to a mentor",
            responses={
                200: {"description": "Match request sent successfully"},
                400: {"model": ErrorResponse, "description": "Bad request - invalid payload or mentor not found"},
                401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
                500: {"model": ErrorResponse, "description": "Internal server error"}
            })
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
                detail="멘티만 매칭 요청을 보낼 수 있습니다"
            )
        
        # 요청하는 멘티가 현재 사용자인지 확인
        if request_data.menteeId != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="본인만 요청을 보낼 수 있습니다"
            )
        
        # 멘토가 존재하는지 확인
        mentor = get_user_by_id(db, request_data.mentorId)
        if not mentor or mentor.role != "mentor":
            raise HTTPException(
                status_code=400,
                detail="멘토를 찾을 수 없습니다"
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
                    detail="이미 대기 중인 요청이 있습니다. 응답을 받거나 취소한 후 새로운 요청을 보내주세요."
                )
            
            existing_to_same_mentor = db.query(MatchRequestModel).filter(
                and_(
                    MatchRequestModel.mentor_id == request_data.mentorId,
                    MatchRequestModel.mentee_id == request_data.menteeId,
                    MatchRequestModel.status == "pending"
                )
            ).first()
            
            if existing_to_same_mentor:
                raise HTTPException(
                    status_code=400,
                    detail="이미 해당 멘토에게 대기 중인 요청이 있습니다."
                )
            
            raise HTTPException(
                status_code=400,
                detail="매칭 요청을 생성할 수 없습니다"
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

@router.get("/match-requests/incoming", 
           response_model=List[MatchRequest],
           summary="Get incoming match requests (mentor only)",
           description="Retrieve all match requests received by the mentor",
           responses={
               200: {"description": "Incoming match requests retrieved successfully"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def get_incoming_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘토만 접근 가능
        if current_user.role != "mentor":
            raise HTTPException(
                status_code=403,
                detail="멘토만 받은 요청을 볼 수 있습니다"
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
            detail="서버 내부 오류가 발생했습니다"
        )

@router.get("/match-requests/outgoing", 
           response_model=List[MatchRequestOutgoing],
           summary="Get outgoing match requests (mentee only)",
           description="Retrieve all match requests sent by the mentee",
           responses={
               200: {"description": "Outgoing match requests retrieved successfully"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
async def get_outgoing_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 멘티만 접근 가능
        if current_user.role != "mentee":
            raise HTTPException(
                status_code=403,
                detail="멘티만 보낸 요청을 볼 수 있습니다"
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

@router.put("/match-requests/{request_id}/accept", 
           response_model=MatchRequest,
           summary="Accept match request (mentor only)",
           description="Accept a specific match request",
           responses={
               200: {"description": "Match request accepted successfully"},
               404: {"model": ErrorResponse, "description": "Match request not found"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
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
                detail="멘토만 요청을 수락할 수 있습니다"
            )
        
        match_request = accept_match_request(db, request_id, current_user.id)
        if not match_request:
            raise HTTPException(
                status_code=404,
                detail="매칭 요청을 찾을 수 없습니다"
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
            detail="서버 내부 오류가 발생했습니다"
        )

@router.put("/match-requests/{request_id}/reject", 
           response_model=MatchRequest,
           summary="Reject match request (mentor only)",
           description="Reject a specific match request",
           responses={
               200: {"description": "Match request rejected successfully"},
               404: {"model": ErrorResponse, "description": "Match request not found"},
               401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
               500: {"model": ErrorResponse, "description": "Internal server error"}
           })
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
                detail="멘토만 요청을 거절할 수 있습니다"
            )
        
        match_request = reject_match_request(db, request_id, current_user.id)
        if not match_request:
            raise HTTPException(
                status_code=404,
                detail="매칭 요청을 찾을 수 없습니다"
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
            detail="서버 내부 오류가 발생했습니다"
        )

@router.delete("/match-requests/{request_id}", 
              response_model=MatchRequest,
              summary="Cancel match request (mentee only)",
              description="Cancel/delete a specific match request",
              responses={
                  200: {"description": "Match request cancelled successfully"},
                  404: {"model": ErrorResponse, "description": "Match request not found"},
                  401: {"model": ErrorResponse, "description": "Unauthorized - authentication failed"},
                  500: {"model": ErrorResponse, "description": "Internal server error"}
              })
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
                detail="멘티만 요청을 취소할 수 있습니다"
            )
        
        match_request = cancel_match_request(db, request_id, current_user.id)
        if not match_request:
            raise HTTPException(
                status_code=404,
                detail="매칭 요청을 찾을 수 없습니다"
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
            detail="서버 내부 오류가 발생했습니다"
        )