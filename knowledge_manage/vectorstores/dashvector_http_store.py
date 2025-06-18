# vectorstores/dashvector_http_store.py
import json
import httpx
from typing import List, Dict, Any

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.vectorstores.base import VectorStore


logger= get_logger()
class DashVectorHTTPStore(VectorStore):
    """使用阿里云DashVector HTTP API的向量数据库实现"""

    def __init__(
            self,
            api_key: str,
            endpoint: str,
            collection_name: str = "knowledge_base",
            dimension: int = 1536,
            metric: str = "cosine",
            dtype: str = "FLOAT",
            fields_schema: Dict[str, str] = None,
            create_if_not_exists: bool = True,
            is_init_collection=False, # 是否初始化集合
    ):
        """
        初始化DashVector HTTP向量数据库

        Args:
            api_key: DashVector API密钥
            endpoint: DashVector集群端点（不包含协议前缀）
            collection_name: 集合名称
            dimension: 向量维度
            metric: 距离度量方式 (cosine, dotproduct, euclidean)
            dtype: 向量数据类型，必须是 "FLOAT" 或 "BINARY"
            fields_schema: 字段定义 (字段名到类型的映射，类型必须是 "STRING", "INT", "FLOAT", "DOUBLE" 其中之一)
            create_if_not_exists: 如果集合不存在，是否创建
        """
        super().__init__(collection_name, dimension, metric, fields_schema)
        # 确保endpoint不包含协议前缀
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            endpoint = endpoint.split("://", 1)[1]

        self.api_key = api_key
        self.endpoint = f"https://{endpoint}"
        self.collection_name = collection_name
        self.dimension = dimension
        self.metric = metric
        self.dtype = dtype

        # 设置默认字段架构（如果没有提供）
        if fields_schema is None:
            self.fields_schema = {
                "text": "STRING",
                "metadata": "STRING",
                "source": "STRING"
            }
        else:
            self.fields_schema = fields_schema

        # 初始化请求头
        self.headers = {
            "dashvector-auth-token": api_key,
            "Content-Type": "application/json"
        }

        # 创建异步HTTP客户端
        self.client = httpx.AsyncClient(timeout=30.0)

        # 检查集合是否存在，不存在则创建
        self.create_if_not_exists = create_if_not_exists
        self.is_init_collection = is_init_collection

    async def initialize(self):
        """显式初始化集合方法，需要在异步上下文中调用"""
        if self.create_if_not_exists and self.is_init_collection:
            await self._initialize_collection()

    async def _make_request(self, method: str, url: str, data: dict = None) -> dict:
        """
        异步发送HTTP请求到DashVector API

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            url: API URL
            data: 请求数据

        Returns:
            响应JSON
        """
        try:
            if method == "GET":
                response = await self.client.get(url, headers=self.headers)
            elif method == "POST":
                response = await self.client.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = await self.client.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = await self.client.request(
                    method="DELETE",
                    url=url,
                    headers=self.headers,
                    json=data
                )
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            # 检查HTTP状态码
            response.raise_for_status()

            # 解析JSON响应
            result = response.json()

            # 检查API响应码
            if result.get("code", -1) != 0:
                error_msg = result.get("message", "未知错误")
                raise Exception(f"DashVector API错误 (代码: {result.get('code')}): {error_msg}")

            return result
        except httpx.RequestError as e:
            logger.error(f"HTTP请求错误: {e}")
            raise
        except json.JSONDecodeError:
            logger.error(f"JSON解析错误，响应内容: {response.text}")
            raise
        except Exception as e:
            logger.error(f"请求处理错误: {e}")
            raise

    async def _initialize_collection(self):
        """异步初始化DashVector集合，如果不存在则创建"""
        # 检查集合是否存在
        try:
            result = await self._make_request(
                "GET",
                f"{self.endpoint}/v1/collections/{self.collection_name}"
            )
            logger.info(f"连接到现有DashVector集合: {self.collection_name}")

            # 获取集合统计信息
            stats = await self._make_request(
                "GET",
                f"{self.endpoint}/v1/collections/{self.collection_name}/stats"
            )
            if "output" in stats and "total_doc_count" in stats["output"]:
                doc_count = stats["output"]["total_doc_count"]
                logger.info(f"集合包含 {doc_count} 个文档")
        except Exception as e:
            # 集合不存在，创建新集合
            logger.info(f"集合 {self.collection_name} 不存在或无法访问，正在创建新集合...")
            try:
                # 创建集合
                result = await self._make_request(
                    "POST",
                    f"{self.endpoint}/v1/collections",
                    {
                        "name": self.collection_name,
                        "dimension": self.dimension,
                        "metric": self.metric,
                        "dtype": self.dtype,
                        "fields_schema": self.fields_schema
                    }
                )
                logger.info(f"成功创建集合: {self.collection_name}")
            except Exception as create_error:
                logger.info(f"创建集合时出错: {create_error}")
                raise

    def _convert_metadata_to_str(self, metadata: Dict[str, Any]) -> str:
        """将元数据转换为字符串"""
        return json.dumps(metadata, ensure_ascii=False)

    def _parse_metadata_str(self, metadata_str: str) -> Dict[str, Any]:
        """解析元数据字符串"""
        try:
            return json.loads(metadata_str)
        except:
            return {"text": metadata_str}

    async def _add_processed_documents(self, processed_docs: List[Dict[str, Any]]) -> int:
        """
        异步将预处理后的文档添加到DashVector

        Args:
            processed_docs: 预处理后的文档列表

        Returns:
            添加的文档数量
        """
        docs_to_insert = []
        for doc in processed_docs:
            temp_doc = doc.copy()
            del temp_doc["vector"]
            if hasattr(temp_doc,"id"):
                del temp_doc["id"]
            if hasattr(temp_doc,"doc_id"):
                del temp_doc["doc_id"]
            docs_to_insert.append({
                "id": doc.get("id"),
                "fields": temp_doc,
                "vector": doc.get("vector"),
            })

        # 批量插入文档
        try:
            result = await self._make_request(
                "POST",
                f"{self.endpoint}/v1/collections/{self.collection_name}/docs",
                {"docs": docs_to_insert}
            )
            success_count = 0
            if "output" in result:
                # 计算成功插入的文档数
                success_count = sum(1 for doc_result in result["output"] if doc_result.get("code", -1) == 0)
                logger.info(f"成功插入 {success_count} 个文档")
            else:
                logger.info(f"无法确定插入结果")
            return success_count
        except Exception as e:
            logger.error(f"插入文档时出错: {e}")
            import traceback
            traceback.print_exc()
            return 0

    async def search(self, query_embedding: List[float]=None, top_k: int = 5, filter_str: str = None) -> List[Dict[str, Any]]:
        """
        异步使用嵌入向量搜索相似文档

        Args:
            query_embedding: 查询的嵌入向量
            top_k: 返回的最相似文档数量
            filter: 过滤条件
        Returns:
            相似文档列表
        """
        # if not query_embedding:
        #     return []

        try:
            # 构建查询请求
            query_data = {
                "topk": top_k,
                "include_vector": False
            }
            if query_embedding:
                query_data["vector"] = query_embedding

            if filter_str:
                query_data["filter"] = filter_str

            # 执行查询
            result = await self._make_request(
                "POST",
                f"{self.endpoint}/v1/collections/{self.collection_name}/query",
                query_data
            )

            # 处理结果
            matches = []
            if "output" in result:
                for i, item in enumerate(result["output"]):
                    #         # 获取字段
                    fields = item.get("fields", {})
                    match = fields
                    match.update({"score": item.get("score", 0.0)})
                    matches.append(match)

            return matches
        except Exception as e:
            logger.error(f"搜索时出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_stats(self):
        """异步获取集合统计信息"""
        try:
            result = await self._make_request(
                "GET",
                f"{self.endpoint}/v1/collections/{self.collection_name}/stats"
            )

            if "output" in result:
                return {
                    "total_doc_count": result["output"].get("total_doc_count", "0"),
                    "index_completeness": result["output"].get("index_completeness", 0.0),
                    "collection_name": self.collection_name
                }
            else:
                return {"error": "无法获取统计信息"}
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            return {"error": str(e)}
            
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    async def delete_by_ids(self, ids: list[str]):
        """
        根据文档ID列表删除文档

        Args:
            ids: 要删除的文档ID列表

        Returns:
            dict: 删除操作的结果
        """
        try:
            result = await self._make_request(
                "DELETE",
                f"{self.endpoint}/v1/collections/{self.collection_name}/docs",
                {"ids": ids}
            )
            
            if "output" in result:
                success_count = sum(1 for doc_result in result["output"] if doc_result.get("code", -1) == 0)
                logger.info(f"成功删除 {success_count} 个文档")
                return result
            else:
                logger.error("删除文档时未收到有效响应")
                return {"error": "删除文档时未收到有效响应"}
                
        except Exception as e:
            logger.error(f"删除文档时出错: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}