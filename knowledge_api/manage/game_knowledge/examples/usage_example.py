"""RAG service usage example"""

import asyncio
import uuid

from knowledge_api.manage.game_knowledge.services import RAGManager, RoleRAGService

async def role_knowledge_example():
    """Role Knowledge Base Usage Example"""
    print("=== Role Knowledge Base Usage Example ===")
    
    # Get RAG Manager
    rag_manager = RAGManager()
    
    # Acquire Role RAG Service
    role_service = await rag_manager.get_service("role")
    
    # Add test text
    doc_id = str(uuid.uuid4())
    test_data = {
        "text": "Zhang San is a brave soldier who has rescued his comrades on the battlefield many times.",
        "role_id": "zhangsan",
        "type": "basic",
        "title": "Zhang San's battlefield deeds",
        "grade": 1.0
    }
    
    # Add document
    print("Add Documentation...")
    result = await role_service.add_text(test_data, doc_id)
    print(f"添加结果: {result['success']}, 消息: {result['message']}")
    
    # query
    print("\ nExecute query...")
    query_result = await role_service.query(
        "What did Zhang San do?", 
        top_k=3, 
        user_info={"role_id": "zhangsan", "level": 2}
    )
    
    print(f"查询结果: {query_result['success']}, 消息: {query_result['message']}")
    if query_result['success'] and query_result['results']:
        for i, result in enumerate(query_result['results'], 1):
            print(f"结果 {i}:")
            print(f"  文本: {result.get('text')}")
            print(f"  标题: {result.get('title')}")
            print(f"  角色ID: {result.get('role_id')}")
    
    # Delete test document
    print("Delete test document...")
    await role_service.delete_by_ids([doc_id])
    print("Delete complete")
    
    # shutdown service
    await rag_manager.close_all()

async def custom_rag_service_example():
    """Custom RAG service example"""
    print("\ N === Custom RAG Service Example ===")
    
    # Create a RAG service instance directly
    custom_service = RoleRAGService(
        collection_name="custom_role",  # custom collection name
        embedding_type="huggingface",   # Embed with HuggingFace
        model_name="./model/models--BAAI--bge-small-zh-v1.5"  # specify model
    )
    
    # initialization service
    await custom_service.initialize()
    
    # Add test text
    doc_id = str(uuid.uuid4())
    test_data = {
        "text": "Li Si is an excellent doctor who is good at dealing with various intractable diseases.",
        "role_id": "lisi",
        "type": "basic",
        "title": "Li Si's medical skills",
        "grade": 1.0
    }
    
    # Add document
    print("Add Documentation...")
    result = await custom_service.add_text(test_data, doc_id)
    print(f"添加结果: {result['success']}, 消息: {result['message']}")
    
    # query
    print("\ nExecute query...")
    query_result = await custom_service.query(
        "What does Li Si do?", 
        top_k=3, 
        user_info={"role_id": "lisi", "level": 2}
    )
    
    print(f"查询结果: {query_result['success']}, 消息: {query_result['message']}")
    if query_result['success'] and query_result['results']:
        for i, result in enumerate(query_result['results'], 1):
            print(f"结果 {i}:")
            print(f"  文本: {result.get('text')}")
            print(f"  标题: {result.get('title')}")
            print(f"  角色ID: {result.get('role_id')}")
    
    # Delete test document
    print("Delete test document...")
    await custom_service.delete_by_ids([doc_id])
    print("Delete complete")
    
    # shutdown service
    await custom_service.close()

if __name__ == "__main__":
    asyncio.run(role_knowledge_example())
    asyncio.run(custom_rag_service_example()) 