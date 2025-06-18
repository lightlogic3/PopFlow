# api/chat_router.py
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app_rag_chat.model.chat_models import ChatInput
from app_rag_chat.service.rag_chat_base import RAGChatService
from knowledge_api.framework.database.database import get_session

from knowledge_api.mapper.role_subtasks import UserSubtaskRelationCRUD
from knowledge_api.model.llm_model import ChatSubTaskInput, TaskSessions, SkipTask

router = APIRouter(prefix="/rag",tags=["rag_chat"])


# @router.post("/chat")
# async def chat(
#         input_data: ChatInput,
#         chat_service: RAGChatService = Depends(rag_chat_service_dependency),
# ):
#     "" Chat interface (non-streaming) ""
#     try:
#
#         result = await chat_service.chat(input_data)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/chat/stream")
# async def chat_stream(
#         input_data: ChatInput,
#         chat_service: RAGChatService = Depends(rag_chat_service_dependency)
# ):
#     "" Chat interface (streaming) ""
#     try:
#         async def stream_generator():
#             async for token in chat_service.chat_stream(input_data):
#                 yield f"{token}"
#
#         return StreamingResponse(
#             stream_generator(),
#             media_type="text/event-stream"
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/chat/sub/task")
# async def chat_sub_task(
#         input_data: ChatSubTaskInput,
#         chat_service: RAGAppChatSupTask = Depends(rag_app_manage_sub_task_dependency),
# ):
#     "" Chat interface (non-streaming) ""
#     return {
#         "data": await chat_service.chat(input_data)
#     }
#
#
# @router.post("/chat/sub/task/session")
# async def chat_sub_init_session(
#         input_data: ChatSubTaskInput,
#         chat_service: RAGAppChatSupTask = Depends(rag_app_manage_sub_task_dependency),
# ) -> Optional[TaskSessions]:
#     "" Chat interface (non-streaming) ""
#     return await chat_service.init_task(input_data)
#
#
# @router.put("/chat/task/skip")
# async def chat_sub_task_skip(input_data: SkipTask, db:Session=Depends(get_session)):
#     "" Skip the topic ""
#     user_subtask_db = UserSubtaskRelationCRUD(db)
#     data = await user_subtask_db.update_by_user_id_skip(input_data.user_id, input_data.subtask_id)
#     return data
#
