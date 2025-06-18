import time
import functools
import logging
import asyncio
from logging import LogRecord
import colorlog


# Configure logger
def setup_logger():
    """Set up and return a logger with color markings"""
    # Create handler
    handler = colorlog.StreamHandler()

    # Create formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    # Apply formatter to handler
    handler.setFormatter(formatter)

    # Create logger and add handler
    logger = logging.getLogger("timer")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicate additions
    if logger.handlers:
        logger.handlers.clear()

    logger.addHandler(handler)

    # Prevent log output duplication
    logger.propagate = False

    return logger


# Create global logger
logger = setup_logger()


def timer(threshold=1.0):
    """
    A decorator for measuring function execution time and printing results using logs
    Supports both synchronous and asynchronous functions
    If execution time exceeds threshold (default 1 second), print using ERROR level (red)
    Otherwise print using INFO level (green)

    Usage:
    # Synchronous function
    @timer()  # Use default threshold of 1 second
    def my_function():
        # function code

    # Asynchronous function
    @timer(threshold=0.5)  # Custom threshold of 0.5 seconds
    async def my_async_function():
        # async function code

    # FastAPI example
    @app.get("/")
    @timer()
    async def read_root():
        return {"Hello": "World"}
    """

    def decorator(func):
        # Check if it's an asynchronous function
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Record start time
                start_time = time.time()

                # Execute original async function
                result = await func(*args, **kwargs)

                # Calculate execution time
                end_time = time.time()
                execution_time = end_time - start_time

                # Decide log level based on execution time
                if execution_time >= threshold:
                    logger.error(f"Async function {func.__name__} execution time: {execution_time:.6f} seconds [exceeds threshold {threshold} seconds]")
                else:
                    logger.info(f"Async function {func.__name__} execution time: {execution_time:.6f} seconds")

                return result

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Record start time
                start_time = time.time()

                # Execute original function
                result = func(*args, **kwargs)

                # Calculate execution time
                end_time = time.time()
                execution_time = end_time - start_time

                # Decide log level based on execution time
                if execution_time >= threshold:
                    logger.error(f"Function {func.__name__} execution time: {execution_time:.6f} seconds [exceeds threshold {threshold} seconds]")
                else:
                    logger.info(f"Function {func.__name__} execution time: {execution_time:.6f} seconds")

                return result

            return sync_wrapper

    # Handle calling without parameters @timer
    if callable(threshold):
        func = threshold
        threshold = 1.0
        return decorator(func)

    # Handle calling with parameters @timer() or @timer(threshold=0.5)
    return decorator


# Usage examples - synchronous function
@timer  # Use default threshold of 1 second
def fast_function(n):
    """A function that executes quickly"""
    result = 0
    for i in range(n):
        result += i
    return result


@timer(threshold=0.01)  # Custom threshold of 0.01 seconds
def slow_function(n):
    """A function that executes slowly"""
    time.sleep(0.02)  # Simulate time-consuming operation
    return sum(range(n))


# Usage examples - asynchronous function
@timer
async def async_fast_function(n):
    """A fast asynchronous function"""
    result = 0
    for i in range(n):
        result += i
    return result


@timer(threshold=0.01)
async def async_slow_function(n):
    """A slow asynchronous function"""
    await asyncio.sleep(0.02)  # Simulate async time-consuming operation
    return sum(range(n))


# FastAPI example
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/fast")
@timer()
async def read_fast():
    # Fast async operation
    return {"status": "fast"}

@app.get("/slow")
@timer(threshold=0.1)
async def read_slow():
    # Simulate slow async operation
    await asyncio.sleep(0.2)
    return {"status": "slow"}
"""

import time
import functools


class ExecutionTimer:
    """
    A utility class for measuring code block execution time
    Can be used as a context manager or decorator
    """

    def __init__(self, description="Code Block"):
        """
        Initialize timer
        :param description: Description of the code block, used for output
        """
        self.description = description
        self.start_time = 0
        self.end_time = 0
        self.execution_time = 0

    def __enter__(self):
        """Entry as a context manager"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit as a context manager"""
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        print(f"{self.description} execution time: {self.execution_time:.6f} seconds")

    def start(self):
        """Manually start timing"""
        self.start_time = time.time()
        return self

    def stop(self):
        """Manually stop timing and print results"""
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        print(f"{self.description} execution time: {self.execution_time:.6f} seconds")
        return self.execution_time

    @staticmethod
    def as_decorator(func):
        """
        Use as a decorator
        :param func: Function to time
        :return: Wrapped function
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"Function {func.__name__} execution time: {end_time - start_time:.6f} seconds")
            return result

        return wrapper


# Function that can be used directly as a decorator
def time_it(func=None, description=None):
    """
    Function decorator for measuring function execution time
    :param func: Function to time
    :param description: Optional description
    :return: Wrapped function
    """
    if func is None:
        return lambda f: time_it(f, description)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        desc = description or f"Function {func.__name__}"
        print(f"{desc} execution time: {end_time - start_time:.6f} seconds")
        return result

    return wrapper


# Tests
if __name__ == "__main__":
    # Test synchronous functions
    result_fast = fast_function(1000000)
    print(f"Fast function result: {result_fast}")

    result_slow = slow_function(1000000)
    print(f"Slow function result: {result_slow}")


    # Test asynchronous functions
    async def test_async():
        result_async_fast = await async_fast_function(1000000)
        print(f"Fast async function result: {result_async_fast}")

        result_async_slow = await async_slow_function(1000000)
        print(f"Slow async function result: {result_async_slow}")


    # Run async tests
    asyncio.run(test_async())