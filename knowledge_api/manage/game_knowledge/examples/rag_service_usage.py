"""RAG Service Simplified Usage Example - Shows New Invoking Methods"""

import asyncio
import uuid

from knowledge_api.manage.game_knowledge.services.rag_manager import RAGManager
from knowledge_api.chat.base_chat import BaseChat


async def simple_rag_example():
    """Demonstrate a simple way to use RAG services"""
    print("=== Simple RAG service usage example ===")
    
    # Get RAG Manager (singleton)
    rag_manager = RAGManager()
    
    # Acquire Role RAG Service
    role_service = await rag_manager.get_service("role")
    
    # Add test documentation
    doc_id = str(uuid.uuid4())
    test_data = {
        "text": "Zhang San is a programmer who specializes in Python development and is currently learning artificial intelligence.",
        "role_id": "zhangsan",
        "type": "basic",
        "title": "Zhang San's occupation",
        "grade": 1.0
    }
    
    # Add text
    print("Add Documentation...")
    result = await role_service.add_text(test_data, doc_id)
    print(f"添加结果: {result['success']}")
    
    # query
    print("\ nExecute query...")
    query_result = await role_service.query(
        "What job does Zhang San do?", 
        top_k=3, 
        user_info={"role_id": "zhangsan", "level": 2}
    )
    
    # Show results
    if query_result["success"] and query_result["results"]:
        print(f"找到 {len(query_result['results'])} 条结果:")
        for i, item in enumerate(query_result["results"], 1):
            print(f"结果 {i}: {item['text']}")
    
    # Delete test document
    print("\ nClean up test data...")
    await role_service.delete_by_ids([doc_id])
    
    # Disable RAG service
    await rag_manager.close_service("role")


async def chat_service_example():
    """Show how to use chat services based on RAGManager"""
    print("\ N === Example of chat service usage ===")
    
    # Create a chat service (no more incoming roles and world services required)
    chat_service = BaseChat(chat_type="example")
    
    # Initialize the service (this step will obtain the required RAG service through RAGManager)
    print("Initialization Service...")
    await chat_service.init_data()
    
    # Create a session
    print("Create a chat session...")
    session_id = str(uuid.uuid4())
    await chat_service.init_session(session_id)
    
    # Other features of the chat service...
    print(f"会话ID: {session_id}")
    
    # shutdown service
    await chat_service.close()


if __name__ == "__main__":
    # run example
    asyncio.run(simple_rag_example())
    asyncio.run(chat_service_example()) 