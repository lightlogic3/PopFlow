"""Snowflake Implementation - Distributed Unique ID Generator

Features:
Generate 64-bit long integer IDs
- globally unique
- Increasing trend (MySQL index friendly)
- Includes timestamp, machine ID, serial number
- Resolved clock rollback issue

Components (64-bit):
- 1 bit: sign bit, fixed to 0, indicating a positive number
41-Bit: timestamp, millisecond, can be used for about 69 years
- 10 digits: machine ID, supports up to 1024 machines
- 12 digits: Serial number, 4096 IDs can be generated in the same millisecond

Clock Rollback Solutions:
1. Cache history serial number
2. timestamp auto-increment (does not depend on system time)
3. Wait for the clock to return to normal"""

import time
import logging
import threading
import os
from typing import Optional, Dict, List, Callable
from datetime import datetime

logger = logging.getLogger("snowflake")

class SnowflakeGenerator:
    """Snowflake Algorithm ID Generator
An improved version that supports handling clock rollback issues"""

    # Default startimestamp: 2023-01-01 00:00:00
    DEFAULT_EPOCH = int(datetime(2023, 1, 1, 0, 0, 0).timestamp() * 1000)
    
    # Number of bits occupied by each part
    TIMESTAMP_BITS = 41  # Timestamp occupancy
    MACHINE_ID_BITS = 10  # Machine ID occupancy
    SEQUENCE_BITS = 12    # Serial number occupancy number
    
    # shift calculation
    MACHINE_ID_SHIFT = SEQUENCE_BITS  # Machine ID left shift by number of digits
    TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS  # Timestamp left shift by number of digits
    
    # Partial maximum
    MAX_MACHINE_ID = -1 ^ (-1 << MACHINE_ID_BITS)  # Maximum machine ID (1023)
    MAX_SEQUENCE = -1 ^ (-1 << SEQUENCE_BITS)  # Maximum serial number (4095)
    
    # Clock Rollback Maximum Tolerable Milliseconds
    MAX_BACKWARD_MS = 5000  # Tolerate up to 5 seconds of clock rewind
    
    def __init__(self, machine_id: Optional[int] = None, epoch: Optional[int] = None,
                 clock_callback: Optional[Callable[[], int]] = None):
        """Initialize Snowflake Algorithm ID Generator

Args:
machine_id: Machine ID, range [0, 1023]. If None, try to generate automatically
Epoch: Start timestamp (milliseconds). If None, use default
clock_callback: Get the callback function of the current time for customizing the time source"""
        # Verify and set the machine ID.
        if machine_id is None:
            #Get machine ID from configuration environment variables
            machine_id = int(os.environ.get("MACHINE_ID", -1))
            if machine_id == -1:
                # Attempt to generate a machine ID based on the hostname or process ID
                machine_id = self._generate_machine_id()
        
        if not 0 <= machine_id <= self.MAX_MACHINE_ID:
            raise ValueError(f"机器ID必须在 0 到 {self.MAX_MACHINE_ID} 之间")
        
        self.machine_id = machine_id
        self.epoch = epoch if epoch is not None else self.DEFAULT_EPOCH
        self.clock_callback = clock_callback
        
        # Serial number and last timestamp
        self.sequence = 0
        self.last_timestamp = -1
        
        # Timestamp auto-increment mode: used when handling clock rollbacks
        self.auto_timestamp_mode = False
        self.auto_timestamp = -1
        
        # Clockback Detection: Save the last MAX_BACKWARD_MS milliseconds serial number
        self.recent_timestamps: Dict[int, List[int]] = {}
        
        # thread-safe lock
        self.lock = threading.Lock()
        
        logger.info(f"雪花算法ID生成器初始化: machine_id={self.machine_id}, epoch={self.epoch}")
    
    def _generate_machine_id(self) -> int:
        """Automatically generate machine IDs
Generate a unique identifier based on host name, process ID, and other information

Returns:
Generated machine ID (0-1023)"""
        # Generate a relatively unique value based on the hostname and process ID
        hostname = os.uname().nodename if hasattr(os, 'uname') else os.environ.get('HOSTNAME', 'unknown')
        pid = os.getpid()
        
        # Simple hash combination and modulo
        machine_id = (hash(hostname) + pid) % (self.MAX_MACHINE_ID + 1)
        return machine_id
    
    def _get_current_time(self) -> int:
        """Get the current timestamp (milliseconds)

Returns:
Current timestamp (milliseconds)"""
        if self.clock_callback:
            return self.clock_callback()
        return int(time.time() * 1000)
    
    def _wait_next_millis(self, last_timestamp: int) -> int:
        """Wait for the next millisecond

Args:
last_timestamp: Previous timestamp

Returns:
New timestamp (milliseconds)"""
        timestamp = self._get_current_time()
        while timestamp <= last_timestamp:
            timestamp = self._get_current_time()
        return timestamp
    
    def _handle_clock_backwards(self, current_timestamp: int) -> int:
        """Processing clock rollback

Strategy:
1. If the callback time is within the tolerance range, switch to timestamp auto-increment mode
2. Throw an exception if it exceeds the tolerance range

Args:
current_timestamp: current timestamp

Returns:
Adjusted timestamp

Raises:
RuntimeError: If the clock is rolled back beyond tolerance"""
        backwards_ms = self.last_timestamp - current_timestamp
        
        if backwards_ms <= self.MAX_BACKWARD_MS:
            logger.warning(f"检测到时钟回拨: {backwards_ms}ms, 切换到时间戳自增模式")
            # Switch to timestamp increment mode
            self.auto_timestamp_mode = True
            self.auto_timestamp = self.last_timestamp
            return self.auto_timestamp
        else:
            # The clock is set back too much to handle
            logger.error(f"严重的时钟回拨: {backwards_ms}ms, 超出容忍范围")
            raise RuntimeError(f"时钟回拨 {backwards_ms}ms 超出容忍范围 {self.MAX_BACKWARD_MS}ms")
    
    def next_id(self) -> int:
        """Generate the next ID

Returns:
Generated unique ID

Raises:
RuntimeError: If a severe clock rollback occurs"""
        with self.lock:
            # Get the current timestamp
            current_timestamp = self._get_current_time()
            
            # Check if it is in timestamp increment mode
            if self.auto_timestamp_mode:
                # If the current time is greater than the last saved time, the clock has returned to normal
                if current_timestamp > self.auto_timestamp:
                    logger.info("The clock has returned to normal, exit timestamp auto-increment mode")
                    self.auto_timestamp_mode = False
                    self.last_timestamp = current_timestamp
                else:
                    # Continue to use autoincrement timestamp
                    current_timestamp = self.auto_timestamp
            
            # Clock Rollback Detection and Processing
            if current_timestamp < self.last_timestamp:
                current_timestamp = self._handle_clock_backwards(current_timestamp)
            
            # In the same millisecond, the serial number is incremented
            if current_timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                # The serial number has reached the maximum value within the same millisecond, wait for the next millisecond
                if self.sequence == 0:
                    # In auto-increment mode, directly increase the timestamp
                    if self.auto_timestamp_mode:
                        self.auto_timestamp += 1
                        current_timestamp = self.auto_timestamp
                    else:
                        # In normal mode, wait for the next millisecond.
                        current_timestamp = self._wait_next_millis(self.last_timestamp)
            # Different milliseconds, serial number reset to 0
            else:
                self.sequence = 0
            
            # Update the timestamp of the last generated ID
            self.last_timestamp = current_timestamp
            
            # generate ID
            timestamp_diff = current_timestamp - self.epoch
            return ((timestamp_diff << self.TIMESTAMP_SHIFT) |
                    (self.machine_id << self.MACHINE_ID_SHIFT) |
                    self.sequence)
    
    def parse_id(self, snowflake_id: int) -> Dict:
        """Parsing the ID generated by the snowflake algorithm

Args:
snowflake_id: Snowflake Algorithm ID

Returns:
Result, including timestamp, machine ID, and serial number"""
        sequence = snowflake_id & self.MAX_SEQUENCE
        machine_id = (snowflake_id >> self.MACHINE_ID_SHIFT) & self.MAX_MACHINE_ID
        timestamp = (snowflake_id >> self.TIMESTAMP_SHIFT) + self.epoch
        
        return {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp / 1000),
            "machine_id": machine_id,
            "sequence": sequence
        }


# Singleton Mode, Global ID Generator
_global_snowflake: Optional[SnowflakeGenerator] = None

def init_snowflake(machine_id: Optional[int] = None, epoch: Optional[int] = None) -> SnowflakeGenerator:
    """Initialize the Global Snowflake Algorithm ID Generator

Args:
machine_id: Machine ID, range [0, 1023]. If None, try to generate automatically
Epoch: Start timestamp (milliseconds). If None, use default

Returns:
Snowflake algorithm ID generator example"""
    global _global_snowflake
    _global_snowflake = SnowflakeGenerator(machine_id, epoch)
    return _global_snowflake

def get_snowflake() -> SnowflakeGenerator:
    """Get Global Snowflake Algorithm ID Generator

Returns:
Snowflake algorithm ID generator example

Raises:
RuntimeError: if the global ID generator has not been initialized"""
    if _global_snowflake is None:
        raise RuntimeError("The global snowflake algorithm ID generator has not been initialized, please call init_snowflake () first")
    return _global_snowflake

def generate_id() -> int:
    """Generate a new unique ID

Returns:
Generated unique ID

Raises:
RuntimeError: if the global ID generator has not been initialized"""
    return get_snowflake().next_id() 