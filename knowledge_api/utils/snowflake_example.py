"""Snowflake algorithm (Snowflake) usage example

This example demonstrates:
1. How to Initialize Snowflake Algorithm ID Generator
2. How to generate a unique ID
3. How to resolve IDs
4. How to handle clock rollback issues"""

import time
from typing import List
import logging
from datetime import datetime

# configuration log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import snowflake algorithm module
from knowledge_api.utils.snowflake import (
    SnowflakeGenerator, 
    init_snowflake, 
    get_snowflake, 
    generate_id
)

def basic_usage_example():
    """Basic Usage Examples"""
    print("\ N === Basic Usage Example ===")
    
    # Method 1: Create an instance directly
    snowflake = SnowflakeGenerator(machine_id=1)
    
    # generate ID
    uid = snowflake.next_id()
    print(f"生成的ID: {uid}")
    
    # parse ID
    parsed = snowflake.parse_id(uid)
    print(f"ID解析结果:")
    print(f"  - 时间戳: {parsed['timestamp']} ({parsed['datetime']})")
    print(f"  - 机器ID: {parsed['machine_id']}")
    print(f"  - 序列号: {parsed['sequence']}")
    
    # Method 2: Using a Global Singleton
    # Initialize the global snowflake algorithm generator
    init_snowflake(machine_id=2)
    
    # Generate multiple IDs
    ids = [generate_id() for _ in range(5)]
    print(f"生成的5个ID: {ids}")
    
    # Validation ID monotonically increases
    is_increasing = all(ids[i] < ids[i+1] for i in range(len(ids)-1))
    print(f"ID单调递增: {is_increasing}")

def benchmark_example(num_ids: int = 10000):
    """Performance test example

Args:
num_ids: Number of generated IDs"""
    print("\ N === Performance test example ===")
    
    # Create a snowflake algorithm generator
    snowflake = SnowflakeGenerator(machine_id=3)
    
    # Measure the time required to generate the specified number of IDs
    start_time = time.time()
    ids = [snowflake.next_id() for _ in range(num_ids)]
    end_time = time.time()
    
    # computing performance
    elapsed = end_time - start_time
    ids_per_second = num_ids / elapsed
    
    print(f"生成 {num_ids} 个ID耗时: {elapsed:.4f}秒")
    print(f"每秒生成ID数: {ids_per_second:.2f}")
    
    # verify uniqueness
    is_unique = len(ids) == len(set(ids))
    print(f"所有ID唯一: {is_unique}")

def clock_backwards_example():
    """Example of clock rollback processing
Simulate clock rollback and demonstrate processing strategies"""
    print("\ N === Example of clock rollback processing ===")
    
    # Custom clock callback function for analog clock callback
    current_time = int(time.time() * 1000)  # Current time milliseconds
    time_sequence = [
        current_time,                    # normal time
        current_time + 1000,             # 1 second forward
        current_time + 2000,             # 1 second forward
        current_time - 1000,             # Dial back 2 seconds (within tolerance)
        current_time + 3000,             # Back to normal
    ]
    
    time_index = 0
    
    def mock_clock() -> int:
        """Analog clock, returns time in preset sequence"""
        nonlocal time_index
        result = time_sequence[time_index]
        time_index = (time_index + 1) % len(time_sequence)
        return result
    
    # Create a generator that uses an analog clock
    snowflake = SnowflakeGenerator(
        machine_id=5, 
        clock_callback=mock_clock
    )
    
    # Generate an ID and observe the clock rollback process
    print("Generate ID sequence (encounter clock callback will be handled automatically):")
    
    ids = []
    parsed_results = []
    
    try:
        for i in range(10):
            # generate ID
            uid = snowflake.next_id()
            ids.append(uid)
            
            # parse ID
            parsed = snowflake.parse_id(uid)
            parsed_results.append(parsed)
            
            # Display results
            print(f"ID {i+1}: {uid} - 时间戳: {parsed['timestamp']} - "
                  f"时间: {parsed['datetime']} - 序列号: {parsed['sequence']}")
            
            # Pause for easy observation
            time.sleep(0.1)
    
    except RuntimeError as e:
        print(f"发生异常: {e}")
    
    # Check the uniqueness and monotonic increment of ID after clock rollback
    is_unique = len(ids) == len(set(ids))
    is_increasing = all(ids[i] < ids[i+1] for i in range(len(ids)-1))
    
    print(f"所有ID唯一: {is_unique}")
    print(f"ID单调递增: {is_increasing}")

def severe_clock_backwards_example():
    """Severe clock callback example
Demonstrates what happens when the clock goes back beyond tolerance"""
    print("\ N === Severe clock callback example ===")
    
    # Custom clock callback function to simulate severe clock callback
    current_time = int(time.time() * 1000)
    time_sequence = [
        current_time,                     # normal time
        current_time + 1000,              # 1 second forward
        current_time - 10000,             # Dial back 11 seconds (out of tolerance)
    ]
    
    time_index = 0
    
    def mock_severe_clock() -> int:
        """Analog Severe Clock Rollback"""
        nonlocal time_index
        result = time_sequence[time_index]
        time_index = (time_index + 1) % len(time_sequence)
        return result
    
    # Create a generator that uses an analog clock
    snowflake = SnowflakeGenerator(
        machine_id=6, 
        clock_callback=mock_severe_clock
    )
    
    # Attempting to generate an ID should throw an exception
    try:
        print("Attempt to generate ID (expected to fail due to severe clock rollback):")
        
        # The first ID should be generated normally
        uid1 = snowflake.next_id()
        print(f"生成的ID 1: {uid1}")
        
        # The second ID should be generated normally
        uid2 = snowflake.next_id()
        print(f"生成的ID 2: {uid2}")
        
        # The third ID should have failed due to a severe clock rollback
        uid3 = snowflake.next_id()
        print(f"生成的ID 3: {uid3}") # This line should not be executed
        
    except RuntimeError as e:
        print(f"捕获到预期异常: {e}")
        print("In practical applications, failure recovery logic can be added here, such as:")
        print("1. Wait for the clock to resume")
        print("2. Switch to an alternate node")
        print("3. Enable alternate machine ID")

def distributed_example():
    """Distributed environment example
Simulate multiple nodes to generate IDs simultaneously"""
    print("\ N === Distributed Environment Example ===")
    
    # Simulate a generator with 3 different nodes
    node1 = SnowflakeGenerator(machine_id=1)
    node2 = SnowflakeGenerator(machine_id=2)
    node3 = SnowflakeGenerator(machine_id=3)
    
    # Each node generates some IDs.
    node1_ids = [node1.next_id() for _ in range(3)]
    node2_ids = [node2.next_id() for _ in range(3)]
    node3_ids = [node3.next_id() for _ in range(3)]
    
    print(f"节点1生成的ID: {node1_ids}")
    print(f"节点2生成的ID: {node2_ids}")
    print(f"节点3生成的ID: {node3_ids}")
    
    # Merge all IDs and check for uniqueness
    all_ids = node1_ids + node2_ids + node3_ids
    is_unique = len(all_ids) == len(set(all_ids))
    print(f"所有节点生成的ID唯一: {is_unique}")
    
    # Parse an ID to show that the machine ID is indeed different
    for node_id, node_name, ids in [
        (1, "Node 1", node1_ids),
        (2, "Node 2", node2_ids),
        (3, "Node 3", node3_ids)
    ]:
        parsed = node1.parse_id(ids[0])
        print(f"{node_name}的ID解析: 机器ID={parsed['machine_id']}, "
              f"时间={parsed['datetime']}, 序列号={parsed['sequence']}")

def main():
    """Main function, running all examples"""
    print("=== Snowflake Example ===")
    
    # Run each example
    basic_usage_example()
    benchmark_example(num_ids=10000)
    clock_backwards_example()
    severe_clock_backwards_example()
    distributed_example()
    
    print("All examples are completed!")

if __name__ == "__main__":
    main() 