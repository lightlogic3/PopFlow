import json
import random
import uuid
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from starlette.websockets import WebSocket, WebSocketDisconnect

from knowledge_api.model.agent.game_agent import TurtleSoupGameAgent, GameRole
from knowledge_api.game_play.base_game import BaseGame
from knowledge_api.game_play.game_session_manager import GameSessionManager
from knowledge_api.mapper.chat_session.base import Session
from knowledge_api.model.llm_token_model import LLMTokenResponse
from knowledge_api.model.task_game_model import TaskGameInput
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class TurtleSoup(BaseGame):
    """The Turtle Soup game implementation class supports serialization and recovery of distributed sessions and Agent objects"""

    game_type = "turtle_soup"

    def __init__(self, db: Session, taskGameInput: TaskGameInput):
        super().__init__(db, taskGameInput)
        self.current_round = 0
        self.soup_surface = ""
        self.soup_truth = ""

    async def _load_agents_from_cache(self) -> List[TurtleSoupGameAgent]:
        """Load Agent object from cache

Returns:
List of Agent objects, empty if the cache does not exist"""
        if not self.session_id:
            return []

        # Attempt to load an Agent object
        try:
            agents = await GameSessionManager.load_agent_objects(self.session_id, self.game_type)
            if agents:
                # Make sure the client side of each agent is initialized
                for agent in agents:
                    if not agent.client:
                        agent.init_client()
                return agents
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"从缓存加载Agent对象失败: {str(e)}")

        return []

    async def _save_agents_to_cache(self, agents: List[TurtleSoupGameAgent]) -> bool:
        """Save Agent object to cache

Args:
Agents: Agent object list

Returns:
Did you save successfully?"""
        if not self.session_id or not agents:
            return False

        try:
            # Save Agent object
            return await GameSessionManager.save_agent_objects(
                self.session_id, agents, self.game_type
            )
        except Exception as e:
            logger.error(f"保存Agent对象到缓存失败: {str(e)}")
            return False

    async def create_agents(self, setter=None) -> List[TurtleSoupGameAgent]:
        """Create or load game proxy objects from the cache

Args:
Setter: Optionally specify the questioner

Returns:
game proxy object list"""
        # Attempt to load the Agent object from the session
        cached_agents = await self._load_agents_from_cache()
        if cached_agents:
            logger.info(f"从缓存加载了 {len(cached_agents)} 个Agent对象")
            return cached_agents

        if not self.character_list:
            return []

        # No cache, create a new Agent object
        agents = []

        # Pick a random soup owner out.
        if setter is None:
            selected_character = random.choice(self.character_list)
            self.character_list.remove(selected_character)
            result = next((item for item in self.character_infos if item.role_id == selected_character.role_id), None)
            if result:
                result = result.model_dump(exclude={"updated_at", "created_at"})
            # questioner prompt word template
            agents.append(TurtleSoupGameAgent(GameRole(
                role_id=selected_character.role_id,
                model_id=self.game_config.get("setter_model_id"),
                setting=selected_character.character_setting,
                voice=selected_character.voice,
                role_info=result
            ), system="", identity="setter"))  # set the questioner
        else:
            # Use the designated questioner
            agents.append(setter)

        # Create player character
        for character in self.character_list:
            role = None
            for character_info in self.character_infos:
                if character_info.role_id == character.role_id:
                    role = character_info.model_dump(exclude={"updated_at", "created_at"})
                    break
            role = GameRole(
                role_id=character.role_id,
                model_id=character.llm_model if character.llm_model else self.game_config.get("player_model_id"),
                setting=character.character_setting,
                voice=character.voice,
                role_info=role
            )
            # Player Cue Template
            agents.append(TurtleSoupGameAgent(role, system=""))

        # Agent objects created by cache
        await self._save_agents_to_cache(agents)
        return agents

    async def create_puzzle(self, setter: TurtleSoupGameAgent, custom_puzzle: Optional[Dict[str, str]] = None) -> (
            Tuple)[str, str, Dict, LLMTokenResponse]:
        """Create turtle soup puzzles, support random creation or custom puzzles

Args:
Setter: Submitter Agent
custom_puzzle: Custom puzzles in the format {"surface": "noodle soup content", "truth": "noodle soup content"}

Returns:
Noodles of soup, soup base, and records containing complete information about the puzzle"""
        usage = None
        if custom_puzzle:
            # Use custom puzzles
            soup_surface = custom_puzzle.get("surface", "")
            soup_truth = custom_puzzle.get("truth", "")
            puzzle_record = {
                "role": "task_setter",
                "content": f"我已准备好谜题，汤面是：{soup_surface}"
            }
        else:
            tool_results = []
            for retries in range(3):
                tool_results, assistant, usage = await self.function_call(setter, [
                    {"role": "system", "content":
                        "Help me create a turtle soup puzzle according to the rules of turtle soup. You must call the create_soup function of tools to help me store the turtle soup puzzle. Don't reply directly to me." +
                        await self.create_prompt("game_turtle_soup_set_question", {
                            "description": self.game_info.description,
                            "setting": self.game_info.setting,
                            "question_type": self.taskInput.user_info.get("question_type", "simple")
                        })
                     }
                ], model=self.game_config.get("create_question"))

                if assistant and len(tool_results) > 0:
                    break
                logger.info(f"Function call 返回空结果，正在进行第 {retries + 1} 次重试...")
            usage = usage
            content_json = tool_results[0].get('content')
            soup_surface = content_json.get("soup")
            soup_truth = content_json.get("answer")

            # Create a puzzle record for the player
            puzzle_record = {
                "role": "task_setter",
                "content": f"我已经准备好了一个谜题，汤面是：{soup_surface}"
            }

        return soup_surface, soup_truth, puzzle_record, usage

    async def initialize_game(self, custom_puzzle: Optional[Dict[str, str]] = None) -> str:
        """Initialize the game, create a session, and set up puzzles

Args:
custom_puzzle: Optional custom puzzles

Returns:
Session ID"""
        if not self.agents or len(self.agents) < 2:
            raise ValueError("The game requires at least two agents: a questioner and at least one player")

        # Find the questioner agent and player agent
        setter: TurtleSoupGameAgent = next((agent for agent in self.agents if agent.identity == "setter"), None)
        if not setter:
            raise ValueError("The questioner's agent could not be found")

        players: list[TurtleSoupGameAgent] = [agent for agent in self.agents if agent.identity != "setter"]
        if not players:
            raise ValueError("Player agent not found")

        # Create session ID
        session_id = self.session_id
        await self.send_message_answer(answer="The game of turtle soup begins! Players will create a puzzle and solve it by asking questions.")

        # Create a turtle soup puzzle
        self.soup_surface, self.soup_truth, puzzle_info, usage = await self.create_puzzle(setter, custom_puzzle)
        setter.memory.update_system_message(
            await self.create_prompt("game_turtle_soup_judge", {
                "soup": self.soup_surface,
                "answer": self.soup_truth,
            })
        )
        # Give AI learning examples to let AI know that Function Calls must be called
        setter.memory.add_function_call_example("function_judge_answer", {"answer": "no.", "is_solved": 0})

        # Show noodle soup to all players
        await self.send_message_answer(setter, puzzle_info["content"], "task_setter", usage)
        for player in players:
            player.memory.update_system_message(await self.create_prompt("game_turtle_soup", {
                "soup": self.soup_surface,
            }))

        # Create game session data
        game_session = {
            "game_type": self.game_type,
            "current_round": 0,
            "solved_players": [],
            "human_has_answered": False,
            "is_game_over": False,
            "user_info": self.taskInput.user_info,
            "soup_surface": self.soup_surface,
            "soup_truth": self.soup_truth,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }

        # Save session to Redis
        await GameSessionManager.create_session(session_id, self.game_type, game_session)

        # Save agent object to cache
        await GameSessionManager.save_agent_objects(session_id, self.agents, self.game_type)

        # Start the first round, in this game (AI replies first)
        await self.play_round()

        # Return session ID
        return session_id

    def add_message_agents(self, message: str, exclude_player: TurtleSoupGameAgent = None) -> None:
        """Adds messages to the memory of all agents, optionally excluding specific agents"""
        for player in self.agents:
            if player.identity != "setter" and (exclude_player is None or exclude_player.agent_id != player.agent_id):
                player.memory.add_user_message(message)

    async def get_current_session(self) -> Dict[str, Any]:
        """Get current session data

Returns:
Session data dictionary, returns an empty dictionary if it does not exist"""
        if not self.session_id:
            return {}

        session_data = await GameSessionManager.get_session(self.session_id, self.game_type)
        return session_data or {}

    async def update_session(self, updates: Dict[str, Any]) -> bool:
        """Update session data

Args:
Updates: updated fields

Returns:
Is the update successful?"""
        if not self.session_id:
            return False

        # Update session
        result = await GameSessionManager.update_session(self.session_id, updates, self.game_type)
        return result is not None

    async def play_round(self, message: Optional[str] = None) -> Dict:
        """Execute a round of the game

Args:
Message: User message (optional)

Returns:
Game status information, including hints for next steps"""
        # Get session data
        session_data = await self.get_current_session()
        if not session_data:
            raise ValueError(f"找不到会话: {self.session_id}")

        if session_data.get("is_game_over", False):
            return await self.end_game()

        current_round = session_data.get("current_round", 0)

        # Make sure there are agents
        if not self.agents or len(self.agents) < 2:
            try:
                self.agents = await GameSessionManager.load_agent_objects(self.session_id, self.game_type)
                if not self.agents or len(self.agents) < 2:
                    raise ValueError("Unable to load or create agents")
            except Exception as e:
                logger.error(f"加载agents失败: {str(e)}")
                raise ValueError(f"加载agents失败: {str(e)}")

        # Get the questioner
        setter: TurtleSoupGameAgent = next((agent for agent in self.agents if agent.identity == "setter"), None)

        # Acquire players
        players = [agent for agent in self.agents if agent.identity != "setter"]

        # If a message is provided, process it (human player turn).
        if message:
            # If it is a game end command
            if message.strip().lower() in ["End Game", "end game", "/end"]:
                return await self.end_game()

            # Add the message to the questioner's memory
            setter.memory.add_user_message(f"人类玩家: {message}")

            # Check if the puzzle was successfully solved
            end_request = await self.is_judge_answer(message, current_round)
            if end_request.get("status") == "game_over":
                return end_request

            if end_request.get("ask"):
                self.add_message_agents(f"其他玩家的提问：{message},出题者对提问的回答：{end_request.get('ask')}")

            # Increment the number of rounds
            current_round += 1

            # Update session data
            await self.update_session({
                "current_round": current_round
            })

            # Save updated agent status
            await GameSessionManager.save_agent_objects(self.session_id, self.agents, self.game_type)

            # Return status - Human round ends, wait for AI round
            return {
                "status": "ai_turn",
                "message": "AI player round begins",
                "current_round": current_round
            }

        # AI player round (executed when no message is provided)
        if current_round == 0:
            # Entering the game for the first time, the initial round
            current_round = 1
        else:
            # Increment the number of rounds
            current_round += 1

        # Update session data
        await self.update_session({
            "current_round": current_round
        })

        # Traverse the AI Player Q & A
        for player in players:
            question_response = await player.client.chat_completion(
                messages=player.memory.get_formatted_history(),
                temperature=0.7,
                application_scenario=f"{self.function_call_scenario}-{self.game_type}"
            )
            question = question_response.content
            player.memory.add_ai_message(question)

            # Send questions to AI players
            await self.send_message_answer(player, question, "player", usage=question_response)

            user_name = player.role.role_info.get('name')
            # Add the AI player's question to the questioner's memory
            setter.memory.add_user_message(f"{user_name}: {question}")

            # The questioner answers the question
            end_request = await self.is_judge_answer(question, current_round)
            if end_request.get("status") == "game_over":
                return end_request

            if end_request.get("ask", ""):
                # Setter.memory.add_user_message ("author pair")
                self.add_message_agents(f"{user_name}：{question},汤主回答了{user_name}：{end_request.get('ask')}",
                                        player)
                player.memory.add_user_message("The soup owner replied:" + end_request.get('ask'))

        # Save updated agent status
        await GameSessionManager.save_agent_objects(self.session_id, self.agents, self.game_type)

        # Return status - AI round ends, waiting for human round
        return {
            "status": "waiting_for_human",
            "message": "AI player round ends, waiting for human player input",
            "current_round": current_round
        }

    async def end_game(self) -> Dict:
        """End Game

Returns:
Game end state"""
        # Get session data
        session_data = await self.get_current_session()
        if not session_data:
            raise ValueError(f"找不到会话: {self.session_id}")

        # Mark game over
        await self.update_session({
            "is_game_over": True
        })

        # Get the questioner
        setter = next((agent for agent in self.agents if agent.identity == "setter"), None)
        if not setter:
            logger.error("Can't find the questioner")
            return {
                "status": "error",
                "message": "Can't find the questioner"
            }

        # Ask the questioner to solve the puzzle
        setter.memory.update_system_message(
            await self.create_prompt("game_turtle_soup_end", {
                "soup": self.soup_surface,
                "answer": self.soup_truth,
                "description": self.game_info.description,
                "content": "\n".join([item.get("content") for item in setter.memory.get_formatted_history() if
                                      item.get("role") == "user"])
            }))

        # Get the analysis of the questioner
        reveal_response = await setter.client.chat_completion(
            messages=[setter.memory.get_formatted_history()[0]],  # Reorganize the message and give the answer analysis directly
            temperature=0.8,
            application_scenario=f"{self.function_call_scenario}-{self.game_type}"
        )

        answer = reveal_response.content
        setter.memory.add_ai_message(answer)

        # Send the final answer
        await self.send_message_answer(answer=f"【谜底揭晓】\n{answer}",usage=reveal_response)

        # Send game over notification
        await self.send_message_answer(answer="Game over! Thanks for participating!")

        # Clear cache
        GameSessionManager.clear_local_cache(self.session_id, self.game_type)

        return {
            "status": "game_over",
            "message": "Game Over",
            "soup_surface": self.soup_surface,
            "soup_truth": self.soup_truth,
            "final_answer": answer
        }

    async def play_game(self, websocket: WebSocket,
                        customize_parameters: Optional[Dict[str, Any]] = None,
                        ) -> None:
        """Handle the game flow, including interacting with the user's WebSocket

Args:
WebSocket: WebSocket connection
customize_parameters: Custom parameters, can contain custom puzzles"""
        await super().play_game(websocket, customize_parameters)

        # #Register a WebSocket connection
        # await self.register_websocket(self.session_id, websocket)

        await websocket.send_json({
            "status": "waiting_for_human",
            "message": "It's your turn to ask questions"
        })

        try:
            # Processing messages from the client
            while True:
                data = await websocket.receive_json()

                # Get the latest session data
                session_data = await self.get_current_session()
                if not session_data:
                    logger.error(f"找不到会话数据: {self.session_id}")
                    break

                # Check if the game is over
                if session_data.get("is_game_over", False):
                    logger.info(f"游戏已结束: {self.session_id}")
                    break

                # Only handle messages from human players, other types are ignored
                if data.get("type") == "human_message":
                    message = data.get("message")
                    if message:
                        logger.info(f"收到人类玩家消息: {message[:30]}...")
                        # Handle human player messages - directly pass in message strings instead of message objects
                        result = await self.play_round(message)
                        if result.get("status") == "game_over":
                            logger.info(f"游戏攻略成功！: 会话ID={self.session_id}")
                            break

                        # Retrieve session data and check game status
                        session_data = await self.get_current_session()
                        if not session_data or session_data.get("is_game_over", False):
                            logger.info(f"游戏已结束: {self.session_id}")
                            break

                        # If the game is not over, the AI round starts automatically
                        # Give a little delay to allow the front end time to display human messages and respond to the questioner
                        result = await self.play_round()
                        if result.get("status") != "game_over":
                            # After the AI round is completed, the front-end user is notified that it is ready to enter.
                            await websocket.send_json({
                                "status": "waiting_for_human",
                                "message": "It's your turn to ask questions"
                            })
                        else:
                            logger.info(f"游戏攻略成功！: 会话ID={self.session_id}")
                            break

                # If you receive an end game request, end the game manually
                elif data.get("type") == "end_game":
                    logger.info(f"收到手动结束游戏请求: 会话ID={self.session_id}")
                    await self.end_game()
                    break
        except WebSocketDisconnect:
            logger.info(f"WebSocket连接已断开: 会话ID={self.session_id}")
        finally:
            # Unregister WebSocket Connection
            await self.unregister_websocket(self.session_id, websocket)

    async def send_message_setter(self, answer, usage=None):
        """Send questioner message

Args:
Answer: Answer by the author
Usage: Message usage (optional)"""
        # Get the questioner
        setter = next((agent for agent in self.agents if agent.identity == "setter"), None)
        if setter:
            await self.send_message_answer(setter, answer, "setter", usage)
        else:
            logger.error("Can't find the questioner")

    async def is_judge_answer(self, answer: str, current_round: int, max_retries: int = 3, retry_delay: float = 1.0):
        """Determine whether the user's answer is successful

Args:
Answer: User's answer
current_round: Number of rounds
max_retries: Maximum number of retries
retry_delay: retry interval (seconds)

Returns:
Game state information"""
        return await self._is_judge_answer_with_retry(answer, current_round, 0, max_retries, retry_delay)

    async def _is_judge_answer_with_retry(self, answer: str, current_round: int,
                                          current_retry: int, max_retries: int, retry_delay: float):
        """Puzzle-solving Judgment with Retry Logic

Args:
Answer: User answer
current_round: Current Round
current_retry: Current number of retries
max_retries: Maximum number of retries
retry_delay: Retry delay time (seconds)

Returns:
judgment result"""
        # Get the questioner
        setter = next((agent for agent in self.agents if agent.identity == "setter"), None)
        if not setter:
            logger.error("Can't find the questioner")
            return {
                "status": "error",
                "message": "Can't find the questioner"
            }

        # Add more explicit instructions to ensure AI calls function_call
        if current_retry > 0:
            # If it is a retry, add a stronger prompt
            setter.memory.add_user_message(
                f"请务必使用function_judge_answer函数分析这个问题: \"{answer}\"。你必须调用函数，直接回复是不被允许的。")

        history = setter.memory.get_formatted_history()
        if history[-1].get("role") == "user":
            end_history = history[-1]
            # Enhanced intent
            end_history[
                "content"] = f'根据用户提问分析提问内容是否符合海龟汤 汤底。然后调用function_judge_answer处理存储分析后的结果，不要直接回复我。用户提问：{end_history["content"]}'
            history[-1] = end_history
        tool_results, assistant, usage = await self.function_call(setter, history,
                                                                  model=self.game_config.get("decision_making"))

        # Check if the result is empty
        empty_result = (tool_results is None or len(tool_results) == 0 or
                        (isinstance(tool_results, str) and not tool_results.strip()))
        # If the result is empty and does not exceed the maximum number of retries, retry
        if empty_result and current_retry < max_retries:
            import asyncio
            # Add log
            logger.info(f"Function call 返回空结果，正在进行第 {current_retry + 1} 次重试...")

            # Wait for a while and try again.
            await asyncio.sleep(retry_delay)

            # Recursive call to itself to retry
            return await self._is_judge_answer_with_retry(
                answer, current_round, current_retry + 1, max_retries, retry_delay
            )
        if assistant is None:
            tool_msg = tool_results if not empty_result else "I need more information to make a judgment."
            setter.memory.add_ai_message(tool_msg)
            await self.send_message_setter(tool_msg)

            # Save Agent State
            await GameSessionManager.save_agent_objects(self.session_id, self.agents, self.game_type)

            return {
                "status": "waiting_for_human",
                "message": "AI player round ends, waiting for human player input",
                "current_round": current_round,
                "ask": tool_msg,
            }
        else:
            content_json = tool_results[0].get('content')
            setter.memory.add_function_call_exchange(assistant,
                                                     f"is_solved={content_json.get('is_solved')}"
                                                     f"answer={content_json.get('answer')}")

            # Save Agent State
            await GameSessionManager.save_agent_objects(self.session_id, self.agents, self.game_type)

            if content_json.get('is_solved') == 1:
                await self.send_message_setter(f"恭喜玩家解谜成功！",usage)
                return await self.end_game()
            else:
                await self.send_message_setter(content_json.get('answer'),usage)
                return {
                    "status": "waiting_for_human",
                    "message": "AI player round ends, waiting for human player input",
                    "current_round": current_round,
                    "ask": content_json.get('answer'),
                }

    def _register_tool(self):
        async def function_judge_answer(is_solved: int, answer: str):
            return {
                "is_solved": is_solved,
                "answer": answer
            }

        async def create_soup(soup: str, answer: str):
            return {
                "soup": soup,
                "answer": answer
            }

        self.tools.register(create_soup, name="create_soup", description="Store Turtle Soup Puzzles")
        self.tools.get_tool("create_soup") \
            .set_parameter_description("soup", "Noodle soup (initial puzzle description for the player)") \
            .set_parameter_description("answer", "Soup bottom, complete puzzle answer")

        # Register class methods
        self.tools.register(function_judge_answer,
                            name="function_judge_answer",
                            description="Analyze whether the user's question meets the turtle soup base, as well as the set content, store and process, and reply to the user")

        self.tools.get_tool("function_judge_answer") \
            .set_parameter_description("is_solved",
                                       "Nothing to do with noodle soup or is_solved answer is set to 0, only the real answer can be set to 1") \
            .set_parameter_description("answer", self.game_config.get("reply_setting",
                                                                      "Reply yes, no, or don't know according to the settings. And the content allowed by the owner of Turtle Soup, do not write other irrelevant text."))
