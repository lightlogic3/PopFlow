import asyncio
from typing import Dict, Any, List, Optional, Tuple

from knowledge_api.utils.log_config import get_logger
from knowledge_api.chat.prompt_utils import merge_contexts, extract_sources_from_results
from plugIns.memory_system import MemoryManager, MemoryLevel
from runtime import ExecutionTimer
from knowledge_api.manage.game_knowledge import RAGService
from knowledge_api.framework.redis.cache_manager import CacheManager

logger = get_logger()


class ContextManager:
    """context manager

Responsible for retrieving relevant context from the knowledge base and formatting it"""

    def __init__(self, role_service: RAGService, world_service: RAGService):
        """Initialize the context manager

Args:
role_service: Role RAG Service
world_service: World RAG Services"""
        self.role_service = role_service
        self.world_service = world_service

    async def retrieve_context(self, query: str, ai_message: str, top_k: int = 3,
                               user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """retrieve relevant context

Args:
Query: user query
ai_message: User Intentions for AI Analytics
top_k: Number of most similar documents returned
user_info: User Information

Returns:
Dictionary with context and source"""
        try:
            # Use a timer to record the query time
            timer = ExecutionTimer("Total time required to check the database:")
            timer.start()

            # If no user information is provided, an empty dictionary is used
            if user_info is None:
                user_info = {}

            # Acquiring long-term memory
            async def get_long_term_memory() -> List[Dict[str, Any]]:
                if user_info.get("long_term_memory", False):
                    memory_manager = MemoryManager()
                    await memory_manager.set_memory_level(MemoryLevel(user_info.get("memory_level", 6)))
                    # Retrieve long-term memory
                    retrieved_memories = await memory_manager.retrieve(
                        query=query,
                        user_id=user_info.get("user_id"),
                        role_id=user_info.get("role_id"),
                        session_id=None,
                        top_k=5  # Retrieve the top 5 most relevant memories
                    )
                    if retrieved_memories:
                        # Process the retrieved memory and convert it into a format appropriate to the context
                        return [
                            {
                                "text": memory.get("content", ""),
                                "score": memory.get("score", 0.0),
                                "role": memory.get("role", "user"),
                            } for memory in retrieved_memories if memory.get("content")
                        ]
                    # memory_manager = EnhancedChatMemoryManager()
                    # return await memory_manager.get_long_term_memory(user_info.get("user_id", ""))
                return []

            # Concurrent execution of role knowledge and world knowledge queries
            results1, results2, results3 = await asyncio.gather(
                self.role_service.query(query, top_k, user_info),
                self.world_service.query(query, top_k, user_info),
                get_long_term_memory()
            )

            # Merge results and filter duplicates
            combined_results = results1.get("results", []) + results2.get("results", [])
            timer.stop()

            # sort by similarity
            sorted_results = sorted(combined_results, key=lambda result: result.get("score", 0.0))

            # Get the first top_k results
            results = sorted_results[:top_k]

            # Filter results whose similarity is below the system configuration threshold (this should be obtained from the system configuration)
            score_filter = 0.6  # default threshold
            results = [item for item in results if item.get("score", 0.0) < score_filter]
            results = await self.post_rerank_model(query, results)

            # Extract context and source
            return extract_sources_from_results(results,results3, top_k)

        except Exception as e:
            logger.error(f"检索上下文时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "contexts": [],
                "sources": []
            }

    async def create_retrieval_template(self, query: str, top_k: int,
                                        prompt_type: str = "system_prompt",
                                        user_info: Optional[Dict[str, Any]] = None,
                                        extended: Optional[Dict[str, Any]] = None,
                                        role_data: Optional[Dict[str, Any]] = None) -> Tuple[
        List[Dict[str, Any]], List[str], str]:
        """Create a prompt word template with search results

Args:
Query: user query
top_k: Number of most similar documents returned
prompt_type: Cue word types
user_info: User Information
Extended: extended parameters
role_data: Role Data

Returns:
(Sources, contexts, prompt) triples, which are the source, context, and final prompt words"""
        # First, understand user intent through middleware
        ai_message = await self.middleware_clear(query)

        # retrieve relevant context
        retrieval_results = await self.retrieve_context(query, ai_message, top_k, user_info)
        contexts = retrieval_results["contexts"]
        sources = retrieval_results["sources"]
        memory= retrieval_results.get("memory", [])

        # merge context
        merged_context = merge_contexts(contexts, user_info)


        # Building cue word parameters
        prompt_kwargs = {
            "context": merged_context,
            "question": query,
            "user": user_info.get("user", "") if user_info else "",
            "memory":"\n".join([item.get("content", "") for item in memory]),
        }

        # Add extension parameters
        if extended:
            prompt_kwargs.update(extended)

        # Add role data
        if role_data:
            from knowledge_api.chat.prompt_utils import prompt_pre
            prompt_kwargs.update({
                "role": prompt_pre(role_data.get("prompt_text", ""), user_info or {}),
                "dialogue": prompt_pre(role_data.get("dialogue", ""), user_info or {}),
                "relationship": prompt_pre(user_info.get("relationship", "") if user_info else "", user_info or {}),
            })

        # Get the closest prompt word from the cache
        cache = CacheManager()

        # Get role information
        role_info = None
        if user_info and user_info.get("role_id"):
            role_info = await cache.get_role(user_info.get("role_id"))

        # Preferential use of worldview control as cue word type
        tem_prompt = role_info.worldview_control if role_info and role_info.worldview_control else prompt_type
        if prompt_type != "system_prompt":
            # Priority is given to prompt_type
            tem_prompt = prompt_type

        # Get prompt word template
        template_obj = await cache.get_nearest_prompt(tem_prompt, 1000)

        # application template
        from knowledge_api.chat.prompt_utils import prompt_pre
        template = template_obj.prompt_text
        prompt = prompt_pre(template, prompt_kwargs)

        return sources, contexts, prompt

    async def middleware_clear(self, message: str) -> str:
        """Middleware processing that understands users' true intentions

Args:
Message: User Message

Returns:
user intent analysis results"""
        # This method requires a subclass implementation, a default implementation is provided here
        logger.warning("middleware_clear need subclass implementation")
        return "Not yet implemented"

    async def post_rerank_model(self, source_sentence, raw):
        """Invoke rerank_model model to sort the list of sentences passed in"""
        if not raw:
            return raw
        try:
            # Construct input format
            sentences_to_compare = [item.get("text", "") for item in raw]

            inputs = {
                'source_sentence': [source_sentence],
                'sentences_to_compare': sentences_to_compare
            }

            # Static methods using TextRankingModel
            from knowledge_manage.rerank_model.ranking_chinese_base_model import TextRankingModel

            # Check if the model has been initialized
            if not TextRankingModel.is_initialized():
                logger.error("The reordering model is not initialized, check if the TextRankingModel.initialize method was called when the application started")
                return raw

            # Reorder
            result = TextRankingModel.rank(inputs)

            # Combine results with original data sources and sort by score
            if 'scores' in result and len(result['scores']) == len(sentences_to_compare):
                scores = result['scores']

                # Update score field in original data source
                for i, score in enumerate(scores):
                    if i < len(raw):
                        raw[i]['score'] = float(score)

                # Sort by score from high to low
                indexed_results = list(enumerate(scores))
                sorted_results = sorted(indexed_results, key=lambda x: x[1], reverse=True)

                # Rearrange raw data according to sorting results
                sorted_raw = [raw[i] for i, _ in sorted_results]

                return sorted_raw
            logger.error("The reordered results are not in the correct format")
            return raw
        except Exception as e:
            logger.error(f"An error occurred while calling the rerank_model model: {e}")
            import traceback
            traceback.print_exc()
            return raw
