import asyncio
import logging
import traceback
from typing import  Any, List, Optional
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import HumanMessage as CoreHumanMessage

from knowledge_api.framework.ai_collect.all_ai import AllAI
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager

# configuration log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ConversationSummarizer")

class ConversationSummarizer:
    """dialogue summary service
Monitor conversation rounds in the background, regularly summarize conversation content and update to memory manager
Support for summarizing with project-defined AllAI"""

    def __init__(
        self,
        llm: Optional[Any] = None,  # Can be a LangChain model or an AllAI instance
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        summary_interval: int = 5,
        summary_prompt_template: str = None,
        sleep_interval: float = 1.0,
        max_retry_attempts: int = 3
    ):
        """Initialize the conversation summary service

@Param llm: A language model for generating summaries, either a LangChain model or an AllAI instance of the project
@Param api_key: If llm is not provided, AllAI can be initialized via api_key
@Param model_name: model name, default is gpt-3.5-turbo
@Param summary_interval: Interval of conversation rounds that trigger summary
@Param summary_prompt_template: summary prompt template (optional)
@Param sleep_interval: Check summary sleep intervals (seconds)
@Param max_retry_attempts: Maximum number of retries when summarizing failures"""
        # Initialize LLM
        if llm is None and api_key is None:
            raise ValueError("You must provide LLM or api_key one of them")

        self.summary_interval = summary_interval
        self.summary_prompt_template = summary_prompt_template or self._default_summary_prompt_template()
        self.running_tasks = {}  # Track background tasks for each conversation
        self.sleep_interval = sleep_interval
        self.max_retry_attempts = max_retry_attempts

        # Setting up LLM
        if llm is not None:
            # If llm is provided, use it directly
            self.llm = llm
            self.using_project_ai = isinstance(llm, AllAI)
        else:
            # If api_key is provided, use the project's AllAI
            self.llm = AllAI(
                api_key=api_key,
                model=model_name,
                temperature=0.3  # It is more stable to summarize with low temperature
            )
            self.using_project_ai = True

        logger.info(f"对话总结服务初始化完成，使用{'项目AI' if self.using_project_ai else 'LangChain模型'}")

    def _default_summary_prompt_template(self) -> str:
        """Default summary prompt template"""
        return """Please summarize the important content of the following conversation, extracting key information, user requests, and important points.
Keep the summary concise and clear (no more than 200 words), highlighting the main intentions and key messages expressed by the user.
Write the summary in third-person narrative form.

Dialogue history:
{conversation}

Summarize:"""

    def _format_messages_for_summary(self, messages: List[BaseMessage]) -> str:
        """Format the message as text to generate a summary

@param messages: list of messages
@Return: formatted dialogue text"""
        formatted_conversation = ""
        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Skip system messages, do not count in summary
                continue
            elif isinstance(msg, HumanMessage):
                formatted_conversation += f"用户: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                if msg.content:  # AI messages that skip empty content (such as pure tool calls)
                    formatted_conversation += f"AI: {msg.content}\n"
        return formatted_conversation

    async def _retry_generate_summary(self, messages: List[BaseMessage], max_attempts: int = 3) -> str:
        """Summary generation with retry mechanism

@Param messages: List of messages to summarize
@Param max_attempts: Maximum number of retries
@Return: Generated summary text"""
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                summary = await self.generate_summary(messages)
                return summary
            except Exception as e:
                attempt += 1
                last_error = e
                logger.warning(f"总结生成失败 (尝试 {attempt}/{max_attempts}): {e}")
                if attempt < max_attempts:
                    # Wait a while and try again, using exponential backoff
                    await asyncio.sleep(2 ** attempt)

        # All retries failed, errors were logged
        logger.error(f"总结生成在 {max_attempts} 次尝试后失败: {last_error}")
        return f"对话总结：生成总结时发生错误，请稍后再试。错误: {str(last_error)}"

    async def generate_summary(self, messages: List[BaseMessage]) -> str:
        """Generate conversation summaries

@Param messages: List of messages to summarize
@Return: Generated summary text"""
        try:
            # Format dialogue
            conversation_text = self._format_messages_for_summary(messages)
            if not conversation_text:
                return "Dialogue summary: There is no effective dialogue content yet"

            # Create summary prompt
            summary_prompt = self.summary_prompt_template.format(conversation=conversation_text)

            # Invoke different methods depending on the type of AI used
            if self.using_project_ai:
                # Using the project's AllAI
                response = await self.llm.chat_completion(
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.3
                )
                summary = response.get("content", "Conversation summary generation failed")
            else:
                # Using the LangChain model
                if hasattr(self.llm, 'agenerate'):
                    # Asynchronous invocation - using the correct message format
                    prompt_message = CoreHumanMessage(content=summary_prompt)
                    responses = await self.llm.agenerate([[prompt_message]])
                    summary = responses.generations[0][0].text.strip()
                else:
                    # synchronous call
                    summary = self.llm(summary_prompt).strip()

            # Make sure the summary has a standard prefix
            if not summary.startswith("Dialogue summary:"):
                summary = f"对话总结：{summary}"

            return summary
        except Exception as e:
            logger.error(f"生成总结时出错: {e}")
            traceback.print_exc()  # Print detailed error information
            return "Dialogue summary: An error occurred while generating the summary"

    async def summarize_if_needed(self, memory_manager: EnhancedChatMemoryManager) -> bool:
        """Check if a summary is required and generate a summary

@Param memory_manager: Conversation Memory Manager
@Return: whether the summary was executed"""
        # Check if the summary should be triggered
        if memory_manager.should_summarize(self.summary_interval):
            logger.info(f"触发总结，当前对话轮次: {memory_manager.get_exchange_count()}")

            # Get the full conversation history
            messages = memory_manager.get_all_messages()

            # Generate summary (with retry mechanism)
            summary = await self._retry_generate_summary(messages, self.max_retry_attempts)

            # Update summary to memory manager
            memory_manager.update_summary_message(summary)

            logger.info(f"总结已更新: {summary}")
            return True

        return False

    def start_background_summary_service(self, memory_manager: EnhancedChatMemoryManager,
                                         conversation_id: str = "default") -> None:
        """Start the background summary service

@Param memory_manager: Conversation Memory Manager
@Param conversation_id: Conversation ID to identify different conversations"""
        # If a task with the same ID is already running, stop it first
        if conversation_id in self.running_tasks and not self.running_tasks[conversation_id].done():
            self.running_tasks[conversation_id].cancel()

        # Create and start a new background task
        task = asyncio.create_task(
            self._background_summary_loop(memory_manager, conversation_id)
        )
        self.running_tasks[conversation_id] = task
        logger.info(f"已启动总结服务，对话ID: {conversation_id}")

    async def _background_summary_loop(self, memory_manager: EnhancedChatMemoryManager,
                                      conversation_id: str) -> None:
        """background summary loop

@Param memory_manager: Conversation Memory Manager
@Param conversation_id: Conversation ID"""
        logger.info(f"总结服务循环开始，对话ID: {conversation_id}")
        try:
            while True:
                # Check if a summary is required
                try:
                    await self.summarize_if_needed(memory_manager)
                except Exception as e:
                    logger.error(f"总结过程出错: {e}")
                    traceback.print_exc()

                # Wait a while before checking.
                await asyncio.sleep(self.sleep_interval)
        except asyncio.CancelledError:
            logger.info(f"总结服务被取消，对话ID: {conversation_id}")
        except Exception as e:
            logger.error(f"总结服务异常: {e}")
            traceback.print_exc()

    def stop_summary_service(self, conversation_id: str = "default") -> None:
        """Stop the background summary service

@Param conversation_id: Conversation ID"""
        if conversation_id in self.running_tasks:
            task = self.running_tasks[conversation_id]
            if not task.done():
                task.cancel()
            del self.running_tasks[conversation_id]
            logger.info(f"已停止总结服务，对话ID: {conversation_id}")

    def stop_all_services(self) -> None:
        """Stop all background summary services"""
        for conversation_id, task in list(self.running_tasks.items()):
            if not task.done():
                task.cancel()
        self.running_tasks.clear()
        logger.info("All summary services have been stopped")

    async def manually_summarize(self, memory_manager: EnhancedChatMemoryManager) -> str:
        """manual trigger summary
Used to generate summaries immediately when needed, without waiting for automatic triggering

@Param memory_manager: Conversation Memory Manager
@Return: Generated summary"""
        logger.info("manual trigger summary")

        # Get the full conversation history
        messages = memory_manager.get_all_messages()

        # Generative summary
        summary = await self._retry_generate_summary(messages, self.max_retry_attempts)

        # Update summary to memory manager
        memory_manager.update_summary_message(summary)

        logger.info(f"手动总结已更新: {summary}")
        return summary

    async def close(self):
        """Close summary services and related resources"""
        # Stop all background tasks
        self.stop_all_services()

        # If using AllAI, close its session
        if self.using_project_ai and hasattr(self.llm, 'close'):
            await self.llm.close()

        logger.info("The summary service has been completely shut down")

# Usage example
"""#Using the project's AllAI
From knowledge_api ai_collect import AllAI all_ai

#initialization summary service
Summarizer = ConversationSummarizer (
api_key = "your-api-key", #Initialize internal AllAI with API key
model_name = "gpt-3.5-turbo",
summary_interval = 5
)

#Or create an AllAI instance first and then pass in
AI = AllAI (api_key = "your-api-key", model = "gpt-3.5-turbo")
Summarizer = ConversationSummarizer (llm = ai, summary_interval = 5)

#Initialize Memory Manager
memory_manager = EnhancedChatMemoryManager (
system_message = "You are an assistant",
memory_type = "buffer_window",
K = 20
)

#Start the background summary service
Summarizer start_background_summary_service (memory_manager)

Stop the service at the end of the application
Summarizer stop_all_services ()""" 