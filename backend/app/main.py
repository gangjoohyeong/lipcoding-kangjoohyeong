from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.models.user import Base
from app.api import auth, profile, mentors

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mentor-Mentee Matching API",
    description="API for matching mentors and mentees in a mentoring platform",
    version="1.0.0",
    docs_url="/swagger-ui", 
    openapi_url="/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 경로에서 Swagger UI로 리다이렉트
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/swagger-ui")

@app.get("/api")
async def read_root():
    return {"message": "Mentor-Mentee Matching App Backend"}

# API 라우터 등록
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(profile.router, prefix="/api", tags=["User Profile"])
app.include_router(mentors.router, prefix="/api", tags=["Mentors", "Match Requests"])
