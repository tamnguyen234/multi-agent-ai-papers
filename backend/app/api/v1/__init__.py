from fastapi import APIRouter
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.paper_routes import router as paper_router
from app.api.v1.digest_routes import router as digest_router
from app.api.v1.trend_routes import router as trend_router
from app.api.v1.chat_routes import router as chat_router
from app.api.v1.user_routes import router as user_router

from app.api.v1.system_routes import router as system_router
from app.api.v1.dev_routes import router as dev_router

v1_router = APIRouter()

v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(user_router, prefix="/users", tags=["User Settings"])
v1_router.include_router(paper_router, prefix="/papers", tags=["AI Papers"])
v1_router.include_router(digest_router, prefix="/digests", tags=["Daily Digest"])
v1_router.include_router(trend_router, prefix="/trend", tags=["Trend Analysis"])
v1_router.include_router(trend_router, prefix="/trends", tags=["Trend Analysis"])
v1_router.include_router(chat_router, prefix="/chat", tags=["Paper Chat (RAG)"])
v1_router.include_router(system_router, prefix="/system", tags=["System Diagnostics"])
v1_router.include_router(dev_router, prefix="/dev", tags=["Development"])
