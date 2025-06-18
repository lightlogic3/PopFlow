from datetime import datetime
from typing import Optional

from knowledge_api.framework.ai_collect import BaseLLM
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.framework.task import get_task_manager
from knowledge_api.mapper.role_subtasks import RoleSubtaskCRUD, RoleSubtaskCreate, RoleSubtask
from knowledge_api.mapper.role_tasks.base import RoleTask
from knowledge_api.mapper.role_tasks.crud import RoleTaskCRUD
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger
from knowledge_api.scheduler_task.decorator import scheduled_task

logger = get_logger()


class RoleTaskSub:
    """
    RoleTaskSub is a class that represents a task for a specific role.
    It contains methods to handle the task and its associated data.
    """

    def __init__(self, db):
        self.task = RoleTaskCRUD(db)
        self.cache_manager = CacheManager()
        self.agent_create: BaseLLM = None
        self.agent_guide: BaseLLM = None
        self.create_model_id = None
        self.guide_model_id = None
        self.tools = ToolRegistry()
        self.role_sub = RoleSubtaskCRUD(db)
        self.task_id = None

    async def _init_data(self):
        """
        Initializes the data for this role.
        """
        # Initialize agent
        self._register_tool()
        await self._init_agent()

    async def _get_main_task(self, task_id: str) -> Optional[RoleTask]:
        """
        Sets the task data for this role.
        :param data: The data to be set for the task.
        """
        task = await self.task.get_by_id(id=task_id)
        return task

    async def _get_all_tasks(self) -> list:
        """
        Returns all tasks for this role.

        :return: A list of all tasks.
        """
        return await self.task.get_alls()

    async def _init_agent(self):
        """
        Initializes the agent for this role.
        """
        # cache fetch build configuration
        self.create_model_id = await self.cache_manager.get_system_config("AGENT_CONFIG_ROLE_TASK",
                                                                          "doubao-1-5-thinking-pro-250415")
        self.guide_model_id = await self.cache_manager.get_system_config("AGENT_GUIDE_ROLE_TASK",
                                                                         "doubao-pro-256k-241115")
        self.agent_create = await self.cache_manager.get_ai_by_model_id(self.create_model_id)
        self.agent_guide = await self.cache_manager.get_ai_by_model_id(self.guide_model_id)

    async def create_tasks(self, task_id: str, number: int, regular_time: bool = False,
                           task_time: Optional[datetime] = None):
        """
        Creates a task for this role.

        :param task_id: The ID of the task to be created.
        :param number: The number of tasks to be created.
        :param regular_time: Whether to set a regular time for the task.
        :param task_time: The time for the task.
        """
        self.task_id = task_id
        # Initialize data
        await self._init_data()
        # Get main task
        main_task = await self._get_main_task(task_id=task_id)
        main_task = main_task.model_dump()
        if not main_task:
            raise ValueError("Main task not found")

        if regular_time and task_time:
            # Execute scheduled tasks
            return
        task_manager = get_task_manager()

        # execute immediately
        # Create tasks
        for i in range(number):
            await task_manager.submit_time_consuming_tasks(
                self.create_task,
                main_task,
                timeout=60 * 5,
                description="auto-generate subtasks",
                wait=False  # Don't wait for the result.
            )
            # await self.create_task(main_task)
        return main_task

    async def create_random_task(self):
        """Get a main task at random, and then create a subtask for it

: return: created subtask"""
        # initialization data
        await self._init_data()

        # Get the main task randomly
        all_tasks = await self._get_all_tasks()
        if not all_tasks:
            logger.error("No main task available")
            return None

        import random
        # Select a main task at random
        main_task = random.choice(all_tasks)
        self.task_id = main_task.id

        logger.info(f"随机选择了主任务: {main_task.title} (ID: {main_task.id})")

        # Convert to dictionary format
        main_task_dict = main_task.model_dump()

        # Create subtask
        sub_task = await self.create_task(main_task_dict)
        logger.info(f"为主任务{sub_task}")
        # Return to subtask
        return RoleSubtask.model_validate(sub_task)

    async def create_task(self, role_task):
        """
        Creates a task for this role.

        :param role_task: The task to be created.
        """
        guide = await self.cache_manager.get_nearest_prompt("role_task_guide")
        # Build a director agent that guides the task without a function call
        guide = await self.agent_guide.chat_completion([
            {
                "role": "system",
                "content": guide.prompt_text.format(**role_task)
            }
        ], temperature=1, application_scenario=LLMApplication.BACKEND_CREATE_ROLE_TASK_GUIDE)

        create_prompt = await self.cache_manager.get_nearest_prompt("role_task_create")
        memory = EnhancedChatMemoryManager(
            k=4,
            system_message=create_prompt.prompt_text.format(**role_task)
                           + "[Important] Remember not to reply to me directly, please use the create_role_task tool to help me store the generation task in the database",
            memory_type='buffer_window',
        )
        memory.add_function_call_example(
            "create_role_task",
            arguments={
                "personality": "The village where Li Daniu is located has an ancient style and mysterious ruins, and there have been big figures here. I heard that the big figure left a jade pendant for future generations, which hid a mysterious treasure",
                "judging_criteria": "If Daniel successfully hands over the jade pendant, it can be judged successful.",
                "hide_settings": "As long as you say that I am Daniel's brother, you can get the jade pendant faster.",
                "difficulty": 1,
                "prologue": "Hello, what's the matter with me?"

            }
        )

        memory.add_user_message(f"请帮我根据引导生成下新的角色任务吧{guide.content}")

        tool_results, assistant_message,usage = await self.agent_create.function_call(
            messages=memory.get_formatted_history(),
            tools=self.tools,
            model=self.create_model_id,
            application_scenario=LLMApplication.BACKEND_CREATE_ROLE_TASK_CREATE,
        )
        if tool_results:
            return tool_results[0].get("content")
        else:
            return None

    def _register_tool(self):
        """
        Registers the tools for this role.
        """

        async def create_role_task(
                task_description: str,
                personality: str,
                task_goal: str,
                judging_criteria: str,
                hide_settings: str,
                difficulty: int,
                prologue: str):
            sub = await self.role_sub.create(
                obj_in=RoleSubtaskCreate(
                    task_id=self.task_id,
                    task_description=task_description,
                    task_personality=personality,
                    task_goal_judge=judging_criteria,
                    hide_designs=hide_settings,
                    task_level=difficulty,
                    task_goal=task_goal,
                    prologues=prologue
                )
            )
            logger.info("The topic has been successfully generated")
            return sub.model_dump()

        self.tools.register(create_role_task, name="create_role_task", description="Create a role task and store it in the database")
        self.tools.get_tool("create_role_task") \
            .set_parameter_description("task_description", "task description") \
            .set_parameter_description("personality", "Character Traits Personality") \
            .set_parameter_description("task_goal", "mission objective") \
            .set_parameter_description("judging_criteria", "Determine the criteria for completing the task") \
            .set_parameter_description("hide_settings", "Hide settings, what can be done better to complete the task") \
            .set_parameter_description("difficulty", "Difficulty 1-5, 1 easy 5 very difficult") \
            .set_parameter_description("prologue", "opening statement")


# Add module-level functions for timing tasks as entry points to APScheduler
@scheduled_task(
    name="subtask autogeneration",
    description="Automatically generate a specified number of subtasks based on the main task ID on a regular basis",
    tags=["subtask", "auto generation"]
)
async def create_subtasks_job(task_id: str, number: int):
    """Subtask creation function for timed tasks

@Param task_id: main task ID
@Param number: number of subtasks created"""
    # Get Database Session - Fix how to use get_session ()
    db = next(get_session())
    try:
        # Create a RoleTaskSub instance
        task_sub = RoleTaskSub(db)
        result = await task_sub.create_tasks(task_id=task_id, number=number)

        return f"成功为任务 {task_id} 创建了 {number} 个子任务"
    except Exception as e:
        logger.error(f"自动生成子任务失败: {str(e)}")
        raise
    finally:
        # Make sure to close the session
        db.close()
