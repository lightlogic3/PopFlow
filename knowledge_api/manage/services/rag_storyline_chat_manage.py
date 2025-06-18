from typing import Dict, Any

from app_rag_chat.service.rag_chat_base import RAGChatService
from knowledge_api.model.llm_model import ChatTaskInput
from knowledge_api.framework import ToolRegistry

tools = ToolRegistry()


@tools.register_decorator(description="When the conversation enters a key plot node, the user is provided with a plot selection")
def StoryChoice(scene: str, options: list[str]) -> Dict[str, Any]:
    return {
        "name": "StoryChoice",
        "scene": scene,
        "options": options,
    }


class RAGChatStorylineManage(RAGChatService):
    """RAG chat service"""

    async def chat(self, input_data: ChatTaskInput) -> Dict[str, Any]:
        """Chat function (streaming)

Args:

Yields:
generated text fragment"""
        await self.init_chat(input_data)
        # Create prompt word
        sources, contexts, prompt, timbre = await self.create_template(
            input_data.message,
            input_data.top_k,
            prompt_type=input_data.taskType,
            extended=input_data.model_dump(exclude_none=True)
        )
        ai, messages =await self.get_ai(msg=input_data.message, prompt=prompt)
        response = await ai.chat_completion(messages=messages, temperature=input_data.temperature)
        await self.update_chat(response=response, msg=input_data.message)
        """== Push the current plot according to key nodes and provide users with choices =="""
        tools.get_tool("StoryChoice") \
            .set_parameter_description("scene", "Current scene: If the protagonist wants to explore the secret realm, then scene = Do you want to explore the secret realm with me?") \
            .set_parameter_description("options",
                                       'Provide options according to the scene ["It's too dangerous not to go to the secret realm","Let's go together","It is recommended to go in a group.","... More options"]')

        tool_results, assistant_message,usage = await ai.function_call(
            [{"role": "system", "content": getSystemContent(input_data, messages)}], tools=tools)
        if tool_results:
            return {
                "message": "`",
                "assistant_message": assistant_message,
                "tool_results": tool_results,
            }


        messages.append({
            "role": "assistant",
            "content": response.get("content"),
        })

        return {
            "message": response.get("content"),
            "assistant_message": assistant_message,
            "tool_results": tool_results,
        }


def getSystemContent(request: ChatTaskInput, messages: list):
    history = "\n".join([item.get("role") + "：" + item.get("content") for item in messages])

    return f"""You are the story system of the world of "The Strongest Metahuman in History". When the dialogue triggers a key story node, you need to provide a story selection option.
Story settings: {request.taskDescription}
NPC settings: {request.taskPersonality}
Task Goal: {request.taskGoal}
The content of the historical dialogue:
{history}

Please judge whether the user is close to the goal based on the latest conversation content. Points should be added if the user's conversation strategy meets the goal or takes advantage of NPC characteristics (such as fear); points should be deducted if it deviates from the goal or backfires.

Note: The target score is {request.benchetScore} for completion, and the value range is {request.scoreRange}"""
