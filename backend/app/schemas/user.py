from pydantic import BaseModel, EmailStr
from typing import Literal, Optional, List

# 기본 스키마
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: Literal["mentor", "mentee"]

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# 회원가입/로그인 스키마
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Literal["mentor", "mentee"]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str

# 프로필 스키마
class MentorProfileDetails(BaseModel):
    name: str
    bio: str
    imageUrl: str
    skills: List[str]

class MenteeProfileDetails(BaseModel):
    name: str
    bio: str
    imageUrl: str

class MentorProfile(BaseModel):
    id: int
    email: EmailStr
    role: Literal["mentor"]
    profile: MentorProfileDetails

class MenteeProfile(BaseModel):
    id: int
    email: EmailStr
    role: Literal["mentee"]
    profile: MenteeProfileDetails

class UpdateMentorProfileRequest(BaseModel):
    id: int
    name: str
    role: Literal["mentor"]
    bio: str
    image: str  # Base64 encoded string
    skills: List[str]

class UpdateMenteeProfileRequest(BaseModel):
    id: int
    name: str
    role: Literal["mentee"]
    bio: str
    image: str  # Base64 encoded string

# 멘토 리스트 스키마
class MentorListItem(BaseModel):
    id: int
    email: EmailStr
    role: Literal["mentor"]
    profile: MentorProfileDetails

# 매칭 요청 스키마
class MatchRequestCreate(BaseModel):
    mentorId: int
    menteeId: int
    message: str

class MatchRequest(BaseModel):
    id: int
    mentorId: int
    menteeId: int
    message: str
    status: Literal["pending", "accepted", "rejected", "cancelled"]

class MatchRequestOutgoing(BaseModel):
    id: int
    mentorId: int
    menteeId: int
    status: Literal["pending", "accepted", "rejected", "cancelled"]

# 에러 응답 스키마
class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
