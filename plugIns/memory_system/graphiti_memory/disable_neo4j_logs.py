"""
Neo4j日志禁用模块

这个模块提供了禁用所有Neo4j相关日志的功能，可以导入到需要的任何地方
"""
import logging
import sys

def disable_all_neo4j_logs():
    """
    禁用所有Neo4j相关的日志输出
    
    将所有neo4j相关的logger级别设置为CRITICAL，确保不会输出任何日志
    """
    neo4j_loggers = [
        "neo4j",
        "neo4j.io",
        "neo4j.pool",
        "neo4j.bolt",
        "neo4j.connection",
        "neo4j.driver",
        "neo4j.graph",
        "neo4j.work",
        "neo4j.session",
        "neo4j.transaction",
        "neo4j.workspace",
        "neo4j.routing",
        "neo4j.debug",
        "neo4j.resolve",
        "neo4j.time",
    ]
    
    for logger_name in neo4j_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        # 移除所有处理器
        if logger.handlers:
            logger.handlers.clear()
        # 禁止传播日志
        logger.propagate = False
    
    # 添加空处理器以确保日志不会通过根logger传播
    null_handler = logging.NullHandler()
    for logger_name in neo4j_loggers:
        logging.getLogger(logger_name).addHandler(null_handler)
    
    # 打印禁用信息到标准输出，但只在交互模式下
    if sys.stdin.isatty():
        print(f"已彻底禁用所有Neo4j相关的日志输出")

# 立即执行禁用操作
disable_all_neo4j_logs() 