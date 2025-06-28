from sqlalchemy import Column, Integer, String, Text, LargeBinary, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "mentor" or "mentee"
    bio = Column(Text)
    profile_image = Column(LargeBinary)  # 이미지 데이터를 바이너리로 저장
    skills = Column(JSON)  # 멘토의 기술 스택 (JSON 배열)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    sent_requests = relationship("MatchRequest", foreign_keys="MatchRequest.mentee_id", back_populates="mentee")
    received_requests = relationship("MatchRequest", foreign_keys="MatchRequest.mentor_id", back_populates="mentor")

class MatchRequest(Base):
    __tablename__ = "match_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mentee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="pending")  # "pending", "accepted", "rejected", "cancelled"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="received_requests")
    mentee = relationship("User", foreign_keys=[mentee_id], back_populates="sent_requests")