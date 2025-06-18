# 向量存储使用文档

本文档详细介绍如何在项目中使用向量存储组件，包括`ChromaStore`、`FAISSStore`、`QdrantStore`和`LangchainStore`四种实现。

## 目录

- [工厂类使用方法](#工厂类使用方法)
- [ChromaStore使用指南](#chromastore使用指南)
- [FAISSStore使用指南](#faissstore使用指南)
- [QdrantStore使用指南](#qdrantstore使用指南)
- [LangchainStore使用指南](#langchainstore使用指南)
- [基本使用流程](#基本使用流程)
- [性能调优](#性能调优)
- [常见问题解决](#常见问题解决)

## 工厂类使用方法

项目提供了`VectorStoreFactory`类来简化向量存储的创建过程。通过该工厂类，您可以轻松创建不同类型的向量存储实例。

```python
from knowledge_manage.vectorstores.factory import VectorStoreFactory

# 创建向量存储实例
vector_store = await VectorStoreFactory.create(
    db_type="chroma",  # 或 "faiss" 或 "qdrant" 或 "langchain"
    collection_name="my_collection",
    dimension=1536,    # 向量维度，取决于您使用的嵌入模型
    **kwargs           # 其他特定参数
)
```

### 可用的向量存储类型

当前支持四种向量存储类型：

1. `chroma` - 基于ChromaDB的向量存储，支持本地持久化和远程服务器连接
2. `faiss` - 基于Facebook AI Similarity Search (FAISS)的向量存储，性能优越，适合大规模向量检索
3. `qdrant` - 基于Qdrant的向量存储，支持本地存储和远程服务器连接，具有高度可扩展性和灵活的过滤功能
4. `langchain` - 基于LangChain的向量存储包装器，支持所有LangChain支持的向量存储类型

## ChromaStore使用指南

`ChromaStore`是基于ChromaDB的向量存储实现，支持本地持久化和远程服务器连接两种模式。

### 初始化参数

| 参数名 | 类型 | 描述 | 默认值 |
|-------|------|------|-------|
| `collection_name` | str | 集合名称 | 必填 |
| `dimension` | int | 向量维度 | 必填 |
| `metric` | str | 相似度度量方式 | "cosine" |
| `host` | str | ChromaDB服务器主机地址 | None |
| `port` | int | ChromaDB服务器端口 | None |
| `path` | str | 本地存储路径 | None |
| `embedding_function` | callable | 自定义嵌入函数 | None |
| `create_if_not_exists` | bool | 集合不存在时是否创建 | True |

### 使用示例

```python
import asyncio
from knowledge_manage.vectorstores.chroma_store import ChromaStore

async def main():
    # 创建本地存储的ChromaStore实例
    chroma_store = ChromaStore(
        collection_name="documents",
        dimension=1536,
        path="./chroma_db"
    )
    
    # 初始化（必须在使用前调用）
    await chroma_store.initialize()
    
    # 添加文档
    docs = [
        {
            "id": "doc1",
            "text": "这是一个测试文档",
            "vector": [0.1, 0.2, ...],  # 1536维向量
            "metadata": {"source": "test", "author": "user1"}
        }
    ]
    await chroma_store._add_processed_documents(docs)
    
    # 搜索文档
    results = await chroma_store.search(
        query_embedding=[0.1, 0.2, ...],  # 查询向量
        top_k=5,
        filter_str='{"source": "test"}'
    )
    
    # 关闭连接
    await chroma_store.close()

asyncio.run(main())
```

### 远程服务器连接

```python
# 连接到远程ChromaDB服务器
chroma_store = ChromaStore(
    collection_name="documents",
    dimension=1536,
    host="localhost",
    port=8000
)
```

## FAISSStore使用指南

`FAISSStore`是基于Facebook AI Similarity Search (FAISS)的向量存储实现，性能优越，适合大规模向量检索场景。

### 初始化参数

| 参数名 | 类型 | 描述 | 默认值 |
|-------|------|------|-------|
| `collection_name` | str | 集合名称 | 必填 |
| `dimension` | int | 向量维度 | 必填 |
| `metric` | str | 相似度度量方式 | "cosine" |
| `path` | str | 索引存储路径 | "./faiss_indices" |
| `normalize_L2` | bool | 是否对向量进行L2归一化 | False |
| `create_if_not_exists` | bool | 集合不存在时是否创建 | True |

### 使用示例

```python
import asyncio
from knowledge_manage.vectorstores.faiss_store import FAISSStore

async def main():
    # 创建FAISS存储实例
    faiss_store = FAISSStore(
        collection_name="documents",
        dimension=1536,
        path="./faiss_indices",
        normalize_L2=True  # 对于余弦相似度，建议使用L2归一化
    )
    
    # 初始化（必须在使用前调用）
    await faiss_store.initialize()
    
    # 添加文档
    docs = [
        {
            "id": "doc1",
            "text": "这是一个测试文档",
            "vector": [0.1, 0.2, ...],  # 1536维向量
            "metadata": {"source": "test", "author": "user1"}
        }
    ]
    await faiss_store._add_processed_documents(docs)
    
    # 搜索文档
    results = await faiss_store.search(
        query_embedding=[0.1, 0.2, ...],  # 查询向量
        top_k=5,
        filter_str='{"source": "test"}'
    )
    
    # 获取统计信息
    stats = await faiss_store.get_stats()
    print(f"文档数量: {stats['document_count']}")
    
    # 关闭连接
    await faiss_store.close()

asyncio.run(main())
```

## QdrantStore使用指南

`QdrantStore`是基于Qdrant的向量存储实现，支持本地持久化和远程服务器连接，具有高度可扩展性和强大的过滤功能。

### 初始化参数

| 参数名 | 类型 | 描述 | 默认值 |
|-------|------|------|-------|
| `collection_name` | str | 集合名称 | 必填 |
| `dimension` | int | 向量维度 | 必填 |
| `metric` | str | 相似度度量方式 | "cosine" |
| `host` | str | Qdrant服务器主机地址 | None |
| `port` | int | Qdrant服务器端口 | None |
| `path` | str | 本地存储路径 | None |
| `url` | str | Qdrant服务器完整URL | None |
| `api_key` | str | Qdrant API密钥 | None |
| `prefix` | str | URL前缀 | None |
| `timeout` | float | 连接超时时间(秒) | None |
| `on_disk` | bool | 是否使用磁盘存储 | True |
| `create_if_not_exists` | bool | 集合不存在时是否创建 | True |

### 使用示例

```python
import asyncio
from knowledge_manage.vectorstores.qdrant_store import QdrantStore

async def main():
    # 创建本地存储的QdrantStore实例
    qdrant_store = QdrantStore(
        collection_name="documents",
        dimension=1536,
        path="./qdrant_data",
        on_disk=True  # 使用磁盘存储而非内存
    )
    
    # 初始化（必须在使用前调用）
    await qdrant_store.initialize()
    
    # 添加文档
    docs = [
        {
            "id": "doc1",
            "text": "这是一个测试文档",
            "vector": [0.1, 0.2, ...],  # 1536维向量
            "metadata": {"source": "test", "author": "user1"}
        }
    ]
    await qdrant_store._add_processed_documents(docs)
    
    # 搜索文档（支持复杂的过滤条件）
    results = await qdrant_store.search(
        query_embedding=[0.1, 0.2, ...],  # 查询向量
        top_k=5,
        filter_str='{"source": "test", "date": {"gte": "2023-01-01", "lte": "2023-12-31"}}'
    )
    
    # 获取统计信息
    stats = await qdrant_store.get_stats()
    print(f"文档数量: {stats['document_count']}")
    
    # 关闭连接
    await qdrant_store.close()

asyncio.run(main())
```

### 远程服务器连接

```python
# 连接到远程Qdrant服务器
qdrant_store = QdrantStore(
    collection_name="documents",
    dimension=1536,
    host="localhost", 
    port=6333
)

# 或者使用完整URL和API密钥（云服务）
qdrant_store = QdrantStore(
    collection_name="documents",
    dimension=1536,
    url="https://your-qdrant-instance.cloud",
    api_key="your_api_key"
)
```

## LangchainStore使用指南

`LangchainStore`是对LangChain向量存储的包装，允许您在知识管理系统中使用任何LangChain支持的向量存储类型。

### 初始化参数

| 参数名 | 类型 | 描述 | 默认值 |
|-------|------|------|-------|
| `collection_name` | str | 集合名称 | 必填 |
| `dimension` | int | 向量维度 | 必填 |
| `metric` | str | 相似度度量方式 | "cosine" |
| `langchain_client` | LangchainVectorStore | LangChain向量存储实例 | 必填 |
| `fields_schema` | List[Tuple[str, str]] | 字段模式列表 | None |

### 使用示例

```python
import asyncio
from knowledge_manage.vectorstores.langchain_store import LangchainStore
from langchain_community.vectorstores import Chroma, FAISS, Qdrant

async def main():
    # 首先创建一个LangChain向量存储实例
    # 例如Chroma
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings.fake import FakeEmbeddings
    
    # 创建一个LangChain向量存储实例
    langchain_client = Chroma(
        collection_name="langchain_documents",
        embedding_function=FakeEmbeddings(size=1536),
        persist_directory="./langchain_db"
    )
    
    # 使用LangchainStore包装LangChain向量存储
    langchain_store = LangchainStore(
        collection_name="documents",
        dimension=1536,
        langchain_client=langchain_client
    )
    
    # 初始化（必须在使用前调用）
    await langchain_store.initialize()
    
    # 添加文档
    docs = [
        {
            "id": "doc1",
            "text": "这是一个测试文档",
            "vector": [0.1, 0.2, ...],  # 1536维向量
            "metadata": {"source": "test", "author": "user1"}
        }
    ]
    await langchain_store._add_processed_documents(docs)
    
    # 搜索文档
    results = await langchain_store.search(
        query_embedding=[0.1, 0.2, ...],  # 查询向量
        top_k=5,
        filter_str='{"source": "test"}'
    )
    
    # 获取统计信息
    stats = await langchain_store.get_stats()
    print(f"文档数量: {stats['document_count']}")
    
    # 关闭连接
    await langchain_store.close()

asyncio.run(main())
```

### 使用工厂类创建LangchainStore

```python
# 首先创建一个LangChain向量存储实例
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.fake import FakeEmbeddings

# 创建LangChain向量存储实例
langchain_client = FAISS.from_texts(
    texts=["示例文本"],
    embedding=FakeEmbeddings(size=1536)
)

# 使用工厂类创建LangchainStore
vector_store = await VectorStoreFactory.create(
    db_type="langchain",
    collection_name="documents",
    dimension=1536,
    langchain_client=langchain_client
)
```

### 支持的LangChain向量存储类型

`LangchainStore`支持以下LangChain向量存储类型：

- `Chroma` - LangChain封装的ChromaDB实现
- `FAISS` - LangChain封装的FAISS实现
- `Qdrant` - LangChain封装的Qdrant实现
- `Pinecone` - LangChain封装的Pinecone实现
- `Weaviate` - LangChain封装的Weaviate实现
- `Milvus` - LangChain封装的Milvus实现
- `ElasticVectorSearch` - LangChain封装的Elasticsearch向量搜索
- `OpenSearchVectorSearch` - LangChain封装的OpenSearch向量搜索
- 其他所有LangChain支持的向量存储类

## 基本使用流程

无论使用哪种向量存储，基本使用流程如下：

1. **创建实例**：选择合适的向量存储类型并创建实例
2. **初始化**：调用`initialize()`方法初始化存储
3. **添加文档**：调用`_add_processed_documents()`方法添加向量文档
4. **搜索**：调用`search()`方法进行相似性搜索
5. **清理**：使用完成后调用`close()`方法关闭连接

### 文档格式

添加到向量存储的文档必须包含以下字段：

- `id`：文档唯一标识符（字符串）
- `text`：文档文本内容
- `vector`：文档的向量表示（浮点数列表）
- `metadata`：文档元数据（可选），必须是字典类型

## 性能调优

### ChromaStore性能调优

1. **批量添加**：一次性添加多个文档比逐个添加效率更高
2. **远程服务器**：对于大型应用，使用独立的ChromaDB服务器可提高性能
3. **适当的集合大小**：避免在单个集合中存储过多文档，可以根据业务逻辑分割为多个集合

### FAISSStore性能调优

1. **选择合适的指标**：根据实际需求选择合适的距离度量方式（"cosine"、"euclidean"等）
2. **归一化处理**：对于余弦相似度搜索，建议启用`normalize_L2`选项
3. **批量添加**：一次性添加大批量向量比逐个添加效率更高

### QdrantStore性能调优

1. **使用on_disk参数**：根据数据规模选择是否使用磁盘存储
   - 小规模数据集（<100万向量）可以使用内存存储(`on_disk=False`)以获得最佳性能
   - 大规模数据集建议使用磁盘存储(`on_disk=True`)以节省内存
2. **远程部署**：对于生产环境，推荐使用独立的Qdrant服务器部署
3. **选择合适的过滤条件**：使用精确的过滤条件可以显著提高检索效率
4. **数据分片**：对于特别大的数据集，考虑使用多个集合进行分片

### LangchainStore性能调优

1. **选择合适的底层存储**：根据您的使用场景选择合适的LangChain向量存储实现
   - 对于小规模数据集和简单应用，可以使用`Chroma`或`FAISS`
   - 对于大规模生产环境，推荐使用`Qdrant`或`Pinecone`
2. **预先配置底层存储**：在创建LangChain向量存储实例时，确保根据具体实现的最佳实践进行配置
3. **异步化**：尽可能使用异步API以提高性能，特别是在处理大量文档时

## 常见问题解决

### 1. 初始化错误

**问题**：调用`initialize()`方法时报错

**解决方案**：
- 检查依赖库是否正确安装：`chromadb`（ChromaStore）、`faiss`（FAISSStore）、`qdrant-client`（QdrantStore）或`langchain_community`（LangchainStore）
- 检查存储路径是否有写入权限
- 对于远程连接，检查服务器是否可访问

### 2. 向量维度不匹配

**问题**：添加文档时出现维度不匹配错误

**解决方案**：
- 确保所有文档向量的维度与创建存储实例时指定的维度一致
- 检查嵌入模型输出的向量维度是否匹配

### 3. 搜索结果不准确

**问题**：搜索结果相关性不高

**解决方案**：
- 检查向量嵌入质量，确保使用适合的嵌入模型
- 尝试不同的相似度度量方式（"cosine"、"euclidean"、"dot"等）
- 对于FAISS，尝试启用向量归一化（`normalize_L2=True`）
- 对于Qdrant，确保使用与训练嵌入模型时相同的度量方式

### 4. FAISS索引无法序列化

**问题**：保存FAISS索引时出错

**解决方案**：
- 确保存储路径有足够的磁盘空间
- 检查路径是否有写入权限
- 在可能的情况下捕获异常并实现优雅的回退机制

### 5. QdrantStore过滤条件无效

**问题**：使用过滤条件时没有得到预期结果

**解决方案**：
- 确保过滤条件的JSON格式正确
- 检查过滤字段是否存在于文档元数据中
- 对于范围查询，确保使用正确的格式，如`{"date": {"gte": "2023-01-01", "lte": "2023-12-31"}}`

### 6. LangchainStore无法接受向量

**问题**：向LangchainStore添加带向量的文档时报错

**解决方案**：
- 确保底层的LangChain向量存储实现支持外部向量输入
- 对于不支持外部向量输入的实现，考虑使用自定义嵌入函数来处理预计算的向量
- 检查LangChain版本是否最新，某些老版本可能不支持直接添加向量
