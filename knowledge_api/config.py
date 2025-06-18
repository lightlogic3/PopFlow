import os

# Vector Database: DashVector Configuration
DASHVECTOR_API_KEY = os.getenv("DASHVECTOR_API_KEY", "sk-3fNzo9W6u9Sg2qqlTacN85q34jk6U31DF035D071211F080D44652ACA1ED05")
DASHVECTOR_ENDPOINT = os.getenv("DASHVECTOR_ENDPOINT", "vrs-cn-v3m46pl7n000bq.dashvector.cn-hangzhou.aliyuncs.com")

# Embedded model configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
EMBEDDING_MODEL_DEVICE = os.getenv("EMBEDDING_MODEL_DEVICE", "cpu")  # 'CPU 'or'cuda'

# collection name configuration
BASE_COLLECTION_NAME = os.getenv("BASE_COLLECTION_NAME", "knowledge_base")


# Get model short name for collection suffix
def get_model_suffix(model_name: str) -> str:
    """Extracting short names from full model names as set suffixes"""
    parts = model_name.split("/")
    model_short_name = parts[-1].lower()
    # Remove characters that could cause naming issues
    model_short_name = model_short_name.replace(".", "-").replace("_", "-")
    return model_short_name


# Generate collection names with model suffixes
def get_collection_name(base_name: str = BASE_COLLECTION_NAME) -> str:
    """Generate collection names with model suffixes"""
    model_suffix = get_model_suffix(EMBEDDING_MODEL_NAME)
    return f"{base_name}_{model_suffix}"


# API configuration
API_TITLE = "Knowledge Base Management API"
API_DESCRIPTION = "Provide knowledge base content import, query and management functions"
API_VERSION = "1.0.0"
API_PREFIX = "/api"
APP_PREFIX = "/app"

# Other configurations
MAX_CHUNK_SIZE = 2000
CHUNK_OVERLAP = 50



