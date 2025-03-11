from fastapi import APIRouter
from app.api.v1 import documents, chat, user_preferences, config, templates

api_router = APIRouter()

# Include specific route modules
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(user_preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(config.router, prefix="/config", tags=["configuration"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])