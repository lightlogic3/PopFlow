import uuid
import logging
import random

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from sqlmodel import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from card_game.server.card_challenge_service import CardChallengeService
from card_game.server.rag_app_task_sup_chat_manage_v2 import RAGAppChatSupTask
from knowledge_api.framework.auth import TokenUtil
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.card import RARITY_CHOICES, UNLOCK_TYPE_CHOICES, Card
from card_game.server.card_service import CardService
from knowledge_api.model.llm_model import ChatSubTaskInput

challenge_router = APIRouter(prefix="/challenge", tags=["Card Challenge"])
chat_sup = RAGAppChatSupTask()  # Use the Redis cached version


@challenge_router.post("/chat/start")
async def start_challenge(
        card_id: int,
        authorization: Optional[str] = Header(None, description="Authentication Token, optional, will return the card unlock status after providing"),
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Start Card Challenge"""
    try:
        # Get user ID
        user_id = TokenUtil.get_user_id(authorization) if authorization else None
        if not user_id:
            raise ValueError("The user is not logged in or has not provided a valid authentication token")

        # Get the challenge card information first
        card_service = CardService(db)
        card: Card = await card_service.get_card_by_id(card_id)
        if not card:
            raise ValueError("The card does not exist or has been deleted")

        # Check if the user has enough points
        user_points = await card_service.get_user_points(user_id)
        if user_points < card.game_cost_points:
            raise ValueError("User points are insufficient to start the challenge")

        # Initialize chat task
        input_data = ChatSubTaskInput(
            message="",
            role_id="",
            user_level=1,
            top_k=3,
            temperature=0.8,
            user_id=str(user_id),
            level=1.0,
            user_name="players",
            relationship_level=1,
            task_sup_id="",
            session_id=None,  # Use the Challenge ID as part of the Session ID
        )

        # Initialize chat task
        task_session = await chat_sup.init_task(input_data)

        # Points are deducted only when it is a new task
        if task_session and task_session.is_new_task:
            # Deduct points
            await card_service.deduct_user_points(user_id, card.game_cost_points, card_id)

            # Create a challenge task
            series_id = await card_service.create_challenge_task(card_id, user_id, task_session.session_id)
            if not series_id:
                # If the creation fails and an exception is thrown, FastAPI will automatically roll back the transaction
                raise ValueError("Failed to create challenge task")
        else:
            # If it's not a new task, keep a log
            logging.info(
                f"继续已有挑战，不扣除积分。用户ID: {user_id}, 卡牌ID: {card_id}, 会话ID: {input_data.session_id}")

        # Store the card ID in the session data for subsequent reward processing
        if task_session:
            await chat_sup.session_manager.update_session(
                input_data.session_id,
                {"card_id": card_id}
            )

        return {
            "message": "The challenge began successfully",
            "data": {
                "user_id": user_id,
                "session_id": input_data.session_id,
                "task": task_session,
                "is_new_task": task_session.is_new_task if task_session else False
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"开始挑战失败: {str(e)}")


# Define the request body model
class ChatRequestBody(BaseModel):
    message: str
    session_id: str


@challenge_router.post("/chat")
async def chat_with_challenge(
        request: ChatRequestBody = Body(...),
        authorization: Optional[str] = Header(None, description="Authentication Token"),
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Chat with the card challenge"""
    await chat_sup.init_data()
    try:
        # Get user ID
        user_id = TokenUtil.get_user_id(authorization) if authorization else None
        if not user_id:
            raise ValueError("The user is not logged in or has not provided a valid authentication token")
        # Get the message and session ID from the request body
        message = request.message
        session_id = request.session_id
        # Ready to enter data
        input_data = ChatSubTaskInput(
            message=message,
            role_id="",
            user_level=1,
            top_k=3,
            temperature=0.8,
            user_id=str(user_id),
            level=1.0,
            user_name="Player",
            relationship_level=1,
            task_sup_id="",
            session_id=session_id,
        )
        # Handle chat logic
        response = await chat_sup.chat(input_data)
        # Get session data for returning chat history and updating session state
        session_data = await chat_sup.get_session_data(session_id)
        history = []
        if session_data:
            memory_manager = session_data.get("memory_manager")
            if memory_manager:
                history = memory_manager.get_formatted_history()
                # Keep only user and AI messages, filter out system messages
                history = [item for item in history if item.get("role") != "system"]

        # Check if the challenge was successful
        is_success = response.get("is_win", False)
        is_failed = response.get("is_failed", False)
        card_challenge_service = CardChallengeService(db)
        if is_success:
            data = await card_challenge_service.challenge_successful(
                user_id=user_id,
                record_id=session_id,  # Suppose 1 is the record ID, and it needs to be replaced with the correct ID when actually used.
            )
            # blind_box_id = data.get("blind_box_id", -1)
            # Add a success flag to the response
            response["challenge_success"] = True
            response["message"] = f"{response['message']}\n\n【挑战成功！】"
        elif is_failed:
            await card_challenge_service.fail_challenge(user_id=user_id, record_id=session_id)
            response["challenge_failed"] = True
            response["message"] = f"{response['message']}\n\n【挑战失败】"

        # Add chat history to response
        response["history"] = history

        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")
