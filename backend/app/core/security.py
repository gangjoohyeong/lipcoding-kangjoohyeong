from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid
import os

# 시크릿 키 (환경변수에서 가져오거나 기본값 사용)
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secure-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1  # 요구사항에 따라 1시간으로 변경

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # RFC 7519 표준 클레임 추가
    to_encode.update({
        "iss": "mentor-mentee-app",  # issuer
        "sub": str(data.get("user_id")),  # subject (user ID)
        "aud": "mentor-mentee-api",  # audience
        "exp": expire,  # expiration time
        "nbf": datetime.utcnow(),  # not before
        "iat": datetime.utcnow(),  # issued at
        "jti": str(uuid.uuid4())  # JWT ID
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            audience="mentor-mentee-api",
            issuer="mentor-mentee-app"
        )
        return payload
    except JWTError:
        return None