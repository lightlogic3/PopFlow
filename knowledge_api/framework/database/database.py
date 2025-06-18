from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from functools import lru_cache
import threading
import uuid
import logging
from contextlib import contextmanager

from knowledge_api.framework.database.db_config import get_db_settings

# configuration log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database settings
db_settings = get_db_settings()

# thread local storage
_thread_local = threading.local()


@lru_cache
def get_engine():
    """Create and return the database engine, using LRU caching to avoid duplicate creation

Returns:
SQLAlchemy engine instance"""
    connection_string = db_settings.DATABASE_URL

    # Create a database engine
    engine = create_engine(
        connection_string,
        echo=db_settings.DB_ECHO,
        echo_pool=db_settings.DB_ECHO_POOL,
        # connection pool configuration
        pool_size=db_settings.DB_POOL_SIZE,
        max_overflow=db_settings.DB_MAX_OVERFLOW,
        pool_recycle=db_settings.DB_POOL_RECYCLE,
        pool_pre_ping=db_settings.DB_POOL_PRE_PING,
        pool_timeout=db_settings.DB_POOL_TIMEOUT,
        # Set up specific configurations based on database type
        connect_args=db_settings.CONNECT_ARGS
    )

    return engine


def create_db_and_tables():
    """* Create data databases & tables for all models
*/"""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """* Session dependency, for FastAPI dependency injection, each request gets an independent session
*
* @yields database session object
*/"""
    engine = get_engine()
    with Session(engine) as session:
        yield session


def get_thread_local_session():
    """Get the session object of the current thread and create a new one if it doesn't exist
Warning: To use this method, you need to close the session manually
*
* @returns
Database session for the current thread
*/"""
    thread_id = threading.get_ident()

    # If there is no session in the thread local storage or the session ID does not match the thread ID, create a new session
    if not hasattr(_thread_local, 'session') or not hasattr(_thread_local,
                                                            'thread_id') or _thread_local.thread_id != thread_id:
        # Make sure the previous session is closed
        if hasattr(_thread_local, 'session'):
            try:
                _thread_local.session.close()
            except:
                pass

        # Create a new session and store the thread ID
        _thread_local.session = Session(get_engine())
        _thread_local.thread_id = thread_id
        logger.info(f"为线程 {thread_id} 创建新会话")

    return _thread_local.session


@contextmanager
def get_db_session():
    """Secure session context manager that creates a new session for each invocation
Make sure the session closes properly when exiting
*
* @yields new database session object
*/"""
    session_id = str(uuid.uuid4())[:8]  # Session ID for log identification
    engine = get_engine()
    session = Session(engine)

    logger.info(f"创建会话 {session_id}")

    try:
        yield session
        # commit transaction
        try:
            session.commit()
            logger.info(f"会话 {session_id} 提交成功")
        except Exception as e:
            logger.error(f"会话 {session_id} 提交失败: {str(e)}")
            session.rollback()
            raise
    except Exception as e:
        # Any exception rolls back the transaction
        logger.error(f"会话 {session_id} 异常: {str(e)}")
        try:
            session.rollback()
        except Exception as rollback_error:
            logger.error(f"会话 {session_id} 回滚失败: {str(rollback_error)}")
        raise
    finally:
        # Make sure to always close the session
        try:
            session.close()
            logger.info(f"会话 {session_id} 已关闭")
        except Exception as close_error:
            logger.error(f"会话 {session_id} 关闭失败: {str(close_error)}")


@contextmanager
def thread_session_scope():
    """* Thread session scope, reuse thread local sessions
Automatically commit but do not close the session after each call
* Note: This method is suitable for multiple uses in the same thread
*
* @yields
Database session for the current thread
*/"""
    session = get_thread_local_session()
    thread_id = threading.get_ident()

    try:
        yield session
        session.commit()
        logger.info(f"线程 {thread_id} 会话提交成功")
    except Exception as e:
        logger.error(f"线程 {thread_id} 会话异常: {str(e)}")
        session.rollback()
        raise


def close_thread_session():
    """Close and clean up the session of the current thread
It should be called after the thread has completed all database operations
*/"""
    if hasattr(_thread_local, 'session'):
        try:
            _thread_local.session.close()
            logger.info(f"线程 {_thread_local.thread_id} 会话已关闭")
        except Exception as e:
            logger.error(f"关闭线程会话失败: {str(e)}")
        finally:
            delattr(_thread_local, 'session')
            delattr(_thread_local, 'thread_id')


def reset_database_state():
    """Reset the database connection pool
*/"""
    close_thread_session()
    get_engine.cache_clear()
    logger.info("The database state has been reset")