"""
app/api/v1/router.py

Aggregates all v1 endpoint routers under the /api/v1 prefix.
Adding a new feature only requires importing its router here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.chats import router as chats_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.summary import router as summary_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(health_router, tags=["ops"])
api_router.include_router(analyze_router, tags=["analysis"])
api_router.include_router(summary_router, tags=["summary"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(chats_router, tags=["sessions"])
