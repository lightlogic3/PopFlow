# ... existing code ...
import logging
import os
import pprint
import sys
from datetime import datetime
import colorlog
from fastapi import FastAPI, Request
from typing import Callable, Dict, Any, Optional, List, Union
class EnhancedLogger(logging.Logger):
    """Enhanced Logger class to support print-like multi-parameter printing"""

    def _log_multi_args(self, level: int, args: tuple, kwargs: dict) -> None:
        """Handling multi-parameter logging

@Param {int} level - log level
@Param {tuple} args - positional argument
@Param {dict} kwargs - keyword arguments"""
        if not args:
            return

        # If there is only one parameter, use standard logging
        if len(args) == 1:
            self._log(level, args[0], (), **kwargs)
            return

        # Handling multiple parameters
        parts = []
        for arg in args:
            if isinstance(arg, (dict, list, tuple, set)):
                # Formatting complex objects
                parts.append(pprint.pformat(arg, indent=2))
            else:
                parts.append(str(arg))

        # Connect all parts with spaces
        message = " ".join(parts)
        self._log(level, message, (), **kwargs)

    def debug(self, *args, **kwargs) -> None:
        """Enhanced debug method with support for multiple parameters"""
        self._log_multi_args(logging.DEBUG, args, kwargs)

    def info(self, *args, **kwargs) -> None:
        """Enhanced info method with support for multiple parameters"""
        self._log_multi_args(logging.INFO, args, kwargs)

    def warning(self, *args, **kwargs) -> None:
        """Enhanced warning method with support for multiple parameters"""
        self._log_multi_args(logging.WARNING, args, kwargs)

    def error(self, *args, **kwargs) -> None:
        """Enhanced error method with support for multiple parameters"""
        self._log_multi_args(logging.ERROR, args, kwargs)

    def critical(self, *args, **kwargs) -> None:
        """Enhanced critical methods with multi-parameter support"""
        self._log_multi_args(logging.CRITICAL, args, kwargs)

    # Add an alias for warning
    warn = warning

class LogConfig:
    """Log configuration class to set basic parameters for logging"""

    def __init__(
            self,
            log_level: str = "INFO",
            log_format: str = "%(log_color)s[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            date_format: str = "%Y-%m-%d %H:%M:%S",
            log_dir: str = "logs",
            app_name: str = "fastapi-app",
            console_log: bool = True,
            file_log: bool = True,
            log_colors: Optional[Dict[str, str]] = None
    ):
        """Initialize log configuration

@Param {string} log_level - Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
@Param {string} log_format - log format
@Param {string} date_format - date format
@param {string} log_dir - log directory
@Param {string} app_name - application name for log file names
@Param {boolean} console_log - whether to output to console
@Param {boolean} file_log - whether to output to file
@Param {Dict [str, str]} log_colors - Log Color Configuration"""
        self.log_level = log_level
        self.log_format = log_format
        self.date_format = date_format
        self.log_dir = log_dir
        self.app_name = app_name
        self.console_log = console_log
        self.file_log = file_log

        if log_colors is None:
            self.log_colors = {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        else:
            self.log_colors = log_colors


class APILogger:
    """Logging utility class for FastAPI applications"""
    # Class variables are used to store global instances
    _instance = None
    _logger = None

    @classmethod
    def get_instance(cls, config: Optional[LogConfig] = None, recreate: bool = False) -> 'APILogger':
        """Get a singleton instance of APILogger

@Param {LogConfig} config - log configuration, if None use default configuration
@Param {bool} recreate - whether to recreate the instance
@return {APILogger} APILogger instance"""
        if cls._instance is None or recreate:
            cls._instance = cls(config)
        return cls._instance

    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize logging tool

@Param {LogConfig} config - log configuration, if None use default configuration"""
        self.config = config or LogConfig()
        self.setup_logger()
        # Added special handling for Uvicorn logs
        self._fix_uvicorn_logger()

    def setup_logger(self) -> None:
        """Set up a logger"""
        # Add the following code before creating the logger
        logging.getLogger("uvicorn.error").propagate = False
        logging.getLogger("uvicorn.access").propagate = False
        logging.getLogger("uvicorn").propagate = False
        # Get log level
        log_level = getattr(logging, self.config.log_level)

        # Register the enhanced Logger class
        logging.setLoggerClass(EnhancedLogger)

        # Create logger
        self.logger = logging.getLogger(self.config.app_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        # Clear existing processors to avoid duplicate additions
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Add Console Processor
        if self.config.console_log:
            console_handler = colorlog.StreamHandler(stream=sys.stdout)
            formatter = colorlog.ColoredFormatter(
                self.config.log_format,
                datefmt=self.config.date_format,
                log_colors=self.config.log_colors
            )
            console_handler.setFormatter(formatter)
            console_handler.setLevel(log_level)
            self.logger.addHandler(console_handler)

        # Add a file processor
        if self.config.file_log:
            # Make sure the log directory exists
            os.makedirs(self.config.log_dir, exist_ok=True)

            # Create a log file name in date format
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(
                self.config.log_dir,
                f"{self.config.app_name}_{today}.log"
            )

            # Create file processor
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                self.config.log_format.replace('%(log_color)s', ''),
                datefmt=self.config.date_format
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(log_level)
            self.logger.addHandler(file_handler)

        # Update class variables for easy global access
        APILogger._logger = self.logger

    def _fix_uvicorn_logger(self):
        """Fix Uvicorn's access log format issue"""
        # Get Uvicorn's access logger
        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_access.handlers = []
        uvicorn_access.propagate = False

        # Use our format to reconfigure
        if self.config.console_log:
            handler = colorlog.StreamHandler()
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s[%(asctime)s] [%(levelname)s] [uvicorn] %(message)s",
                datefmt=self.config.date_format,
                log_colors=self.config.log_colors
            )
            handler.setFormatter(formatter)
            uvicorn_access.addHandler(handler)


    def get_logger(self) -> EnhancedLogger:
        """Get the configured logger instance

@Return {EnhancedLogger} configured logger instance"""
        return self.logger

    @classmethod
    def get_logger_instance(cls) -> EnhancedLogger:
        """Get global logger instance

@return {EnhancedLogger} global logger instance"""
        if cls._logger is None:
            cls.get_instance()
        return cls._logger




# The global function is used to obtain the logger, adding an explicit return type
# The global function is used to obtain the logger, adding an explicit return type
def get_logger() -> EnhancedLogger:
    """Get a global logger instance with type hints for the editor to provide code completion
Support multi-parameter printing function similar to print

@Return {EnhancedLogger} global logger instance, you can use debug, info, warning, error, critical and other methods"""
    return APILogger.get_logger_instance()
