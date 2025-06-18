from fastapi import APIRouter

from app_rag_chat.api.session_router import session_router
from app_rag_chat.api import chat_router
from knowledge_api.config import APP_PREFIX
from knowledge_api.framework.redis.cache_manager import CacheManager

app_router = APIRouter(prefix=APP_PREFIX)

app_router.include_router(chat_router.router)
app_router.include_router(session_router)

@app_router.get("/test")
async def test(role_id:str,level):
    redis=await CacheManager().get_nearest_prompt(role_id,level)
    return redis