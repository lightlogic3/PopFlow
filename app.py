# app.py
import time
import os
import sys

# SQLite3 version patch - must be executed before any module imports ChromaDB
print("🔧 Applying SQLite3 patch...")
try:
    import pysqlite3.dbapi2 as sqlite3_new

    sys.modules['sqlite3'] = sqlite3_new
    sys.modules['sqlite3.dbapi2'] = sqlite3_new
    print(f"✅ SQLite3 upgraded to version: {sqlite3_new.sqlite_version}")

    # Verify patch immediately
    import sqlite3

    print(f"🔍 Verification: Current sqlite3 version: {sqlite3.sqlite_version}")

except ImportError as e:
    print(f"❌ SQLite3 patch failed: {e}")
    print("Please install: pip install pysqlite3-binary")

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi_pagination import add_pagination

from card_game.app_router import card_game
from knowledge_api.config import API_TITLE, API_DESCRIPTION, API_VERSION
from knowledge_api.manage.api_router import manage_router
from knowledge_api.manage.ws.game_play import wx_manage_router
from knowledge_api.mapper.cache_mid.cache.init_redis_cache import redis_cache_lifespan, get_cache_manager
from app_rag_chat.app_router import app_router
from knowledge_api.utils.log_config import get_logger
from knowledge_api.framework.auth.auth_middleware import setup_auth_middleware
from knowledge_api.framework.exception.exception_handlers import setup_exception_handlers
from knowledge_api.framework.exception.response_wrapper import setup_response_wrapper
from knowledge_api.framework.redis.config import reset_redis_config
from plugIns.memory_system.graphiti_memory.disable_neo4j_logs import disable_all_neo4j_logs

# Disable Neo4j logs immediately
disable_all_neo4j_logs()
# Get logger
logger = get_logger()


# Load environment configuration
def load_environment(env_file='.env'):
    """
    Load environment configuration file
    
    Args:
        env_file: Environment configuration file path, default is .env
    """
    # Check if environment variables have been loaded
    if os.environ.get('ENV_LOADED') == 'true':
        logger.info("Environment configuration already loaded, skipping reload")
        return

    # Load environment variables
    try:
        logger.info(f"Loading environment configuration: {env_file}")
        # Force reload environment variables
        load_dotenv(env_file, override=True)
        # Mark environment variables as loaded
        os.environ['ENV_LOADED'] = 'true'
        # Reset Redis configuration (using newly loaded environment variables)
        reset_redis_config()
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        # Try using default .env file
        if env_file != '.env':
            try:
                logger.info("Trying to load default .env file")
                load_dotenv('.env', override=True)
                os.environ['ENV_LOADED'] = 'true'
                reset_redis_config()
            except Exception as e2:
                logger.error(f"Failed to load default environment configuration: {e2}")
                sys.exit(1)

    # Check critical environment variables
    check_environment_vars()


def check_environment_vars():
    """Check necessary environment variables"""
    required_vars = []  # Add necessary environment variables

    for var in required_vars:
        if not os.environ.get(var):
            logger.error(f"Missing environment variable: {var}")
            sys.exit(1)


# Get configuration from environment variables
env_file = os.environ.get('ENV_FILE', '.env.bink.card')

# Load environment variables
load_environment(env_file)

# Get Redis cache manager - must be called after environment variables are loaded
cache_manager = get_cache_manager()

# Use Redis cache lifecycle manager instead of original memory cache
lifespan = redis_cache_lifespan

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="./static/dist", html=True), name="static")
app.mount("/assets", StaticFiles(directory="./static/dist/assets", html=True), name="static")
app.mount("/touchflow", StaticFiles(directory="./static/touchflow", html=True), name="static")


@app.get("/new/endpoint/", operation_id="new_endpoint")
async def new_endpoint():
    return {"message": "Hello, world!"}


mcp = FastApiMCP(app,
                 # include_operations=["create_card_series","create_card","get_all_blind_boxes","create_blind_box"]
                 include_tags=[
                     "Card Game-Cards",
                     "Card Challenge",
                     "Card Rewards",
                     "Card Game-Card Series",
                     "Card Game-Card Unlock",
                     "Card Game-User Points Record"
                 ]
                 )  # Add MCP server to the FastAPI app
mcp.mount()  # MCP server

# Add CORS middleware (must be placed first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all sources, should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set response wrapper middleware
setup_response_wrapper(app)

# Set global exception handlers
setup_exception_handlers(app)

# Set JWT authentication middleware
setup_auth_middleware(
    app,
    exclude_paths=[
        # Whitelist paths
        "/docs.*",
        "/redoc.*",
        "/openapi.json",
        "/static/.*",
        "/api/auth/login",
        "/api/auth/register",
        "/auth/register",
        "/health",
        # Client API temporarily without authentication
        "/app/.*",
        "/assets/.*",
        "/static.*",
        "/touchflow.*",
        "OPTIONS:.*",  # All OPTIONS requests exempted
        "/ws/.*",  # WebSocket connections exempted
        "/new/endpoint/",  # New endpoint exempted
        "/mcp/.*",  # MCP related endpoints exempted
        "/mcp"
    ]
)

# Add pagination functionality
add_pagination(app)


# # Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Register management routes
app.include_router(manage_router)

# Register client routes
app.include_router(app_router)

# Register dataset routes
app.include_router(wx_manage_router)
# Register card game related routes
app.include_router(card_game)

mcp.setup_server()
print(f"Total interfaces: {len(app.routes)}")

# If this file is run directly
if __name__ == "__main__":
    # Command line argument parsing, only valid when running directly
    import argparse


    def parse_arguments():
        """
        Parse command line arguments
        
        Returns:
            argparse.Namespace: Parsed arguments
        """
        parser = argparse.ArgumentParser(description='AI Game Chat API Service')
        parser.add_argument('--env', type=str,
                            default=os.environ.get('ENV_FILE', '.env'),
                            help='Specify environment configuration file path, default is .env or file specified by ENV_FILE environment variable')
        parser.add_argument('--port', type=int,
                            default=int(os.environ.get('APP_PORT', 7878)),
                            help='Specify API server port number, default is APP_PORT environment variable or 7878')
        parser.add_argument('--host', type=str,
                            default=os.environ.get('APP_HOST', '0.0.0.0'),
                            help='Specify API server host address, default is APP_HOST environment variable or 0.0.0.0')
        return parser.parse_args()


    # Parse command line arguments
    args = parse_arguments()

    # Reload environment variables
    load_environment(args.env)
    logger.info(f"Port number: {args.port}")
    # Start server
    uvicorn.run("app:app", host=args.host, port=args.port)
