from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from knowledge_api.framework.ai_collect import SystemMessage
from knowledge_api.framework.ai_collect.message import UserMessage
from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.manage.model.llm_models import LlmQueryInputEnhance
from knowledge_api.manage.services.rag_chat_stream_manage import RAGChatStreamManage
from knowledge_api.manage.services.rag_task_chat_manage import RAGChatTaskManage
from knowledge_api.manage.services.rag_task_sup_chat_manage import RAGChatSupTaskManage
from knowledge_api.mapper.role_subtasks import UserSubtaskRelationCRUD
from knowledge_api.model.llm_model import ChatTestInput, ChatTaskInput, ChatSubTaskInput, TaskSessions, SkipTask
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger

logger = get_logger()
llm_router = APIRouter(prefix="/llm", tags=["llm"])

# Create a service instance (to be initialized on first invocation, singleton pattern)
chat_stream_service = RAGChatStreamManage()
chat_task_service = RAGChatTaskManage()
chat_sub_task_service = RAGChatSupTaskManage()


@llm_router.post('/enhance')
async def enhance(query: LlmQueryInputEnhance):
    chat_service = await CacheManager().get_ai_by_model_id(query.model_id)
    msg_list = [SystemMessage(
        query.prompt + "\n" + "Output requirements: Each enhancement block is separated by two newlines, and the enhanced content is not less than 3, that is, there are at least 3 blocks and 3 pairs of newlines"),
        UserMessage(query.enhance_context)]
    """Chat interface (streaming)"""
    try:
        async def stream_generator():
            async for token in chat_enhance(msg_list, chat_service):
                yield f"{token}"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def chat_enhance(msg_list, chat_service) -> AsyncGenerator[str, None]:
    collected_response = ""
    async for chunk in chat_service.chat_completion_stream(msg_list, application=LLMApplication.KNOWLEDGE_ENHANCE):
        if chunk.content:
            collected_response += chunk.content
            yield chunk.content


@llm_router.post("/chat/stream")
async def chat_stream(
        input_data: ChatTestInput
):
    """Chat interface (streaming)"""
    try:
        # Service initialization ensures completion inside chat_stream method
        async def stream_generator():
            async for token in chat_stream_service.chat_stream(input_data):
                yield f"{token}"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"聊天流处理出错: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@llm_router.post("/chat/task")
async def chat(
        input_data: ChatTaskInput
):
    """Chat interface (non-streaming)"""
    # Make sure the service is initialized (automatically done internally).
    return {
        "data": await chat_task_service.chat(input_data)
    }


@llm_router.post("/chat/sub/task")
async def chat_sub_task(
        input_data: ChatSubTaskInput
):
    """Chat interface (non-streaming)"""
    # Make sure the service is initialized (automatically done internally).
    return {
        "data": await chat_sub_task_service.chat(input_data)
    }


@llm_router.post("/chat/sub/task/session")
async def chat_sub_init_session(
        input_data: ChatSubTaskInput
) -> Optional[TaskSessions]:
    """Chat interface (non-streaming)"""
    # Make sure the service is initialized (automatically done internally).
    return await chat_sub_task_service.init_task(input_data)


@llm_router.put("/chat/task/skip")
async def chat_sub_task_skip(input_data: SkipTask, db: Session = Depends(get_session)):
    """Skip the topic"""
    user_subtask_db = UserSubtaskRelationCRUD(db)
    data = await user_subtask_db.update_by_user_id_skip(input_data.user_id, input_data.subtask_id)
    return data
