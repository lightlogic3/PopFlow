"""Snowflake FastAPI Integration Example

This example demonstrates how to integrate the snowflake algorithm ID generator in a Fast API application:
1. Initialize the ID generator at application startup
2. Create ID generation API endpoints
3. Provide ID resolution function
Step 4 Health check"""

import os
from typing import Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import snowflake algorithm
from knowledge_api.utils.snowflake import (
    SnowflakeGenerator, 
    init_snowflake,
    get_snowflake
)

# Create a FastAPI application
app = FastAPI(
    title="Snowflake algorithm ID generation service",
    description="Distributed unique ID generation service based on Fast API, using improved snowflake algorithm",
    version="1.0.0"
)

# Define the request and response model
class GenerateResponse(BaseModel):
    """ID generation response"""
    id: int
    timestamp: int
    datetime: str
    machine_id: int
    sequence: int

class ParseRequest(BaseModel):
    """ID resolution request"""
    id: int

class ParseResponse(BaseModel):
    """ID resolution response"""
    id: int
    timestamp: int
    datetime: str
    machine_id: int
    sequence: int
    binary: str

class HealthResponse(BaseModel):
    """Health Check Response"""
    status: str
    machine_id: int
    version: str


# Create dependencies to ensure a snowflake generator is available on every request
def get_snowflake_generator():
    """Get the dependencies of the snowflake algorithm ID generator"""
    try:
        return get_snowflake()
    except RuntimeError:
        # If the global ID generator has not been initialized, initialize it
        machine_id = int(os.environ.get("SNOWFLAKE_MACHINE_ID", "1"))
        return init_snowflake(machine_id=machine_id)


@app.on_event("startup")
async def startup_event():
    """Initialize snowflake algorithm ID generator at application startup"""
    # Read machine IDs from environment variables or configuration files
    machine_id = int(os.environ.get("SNOWFLAKE_MACHINE_ID", "1"))
    
    # Initialize Snowflake Algorithm ID Generator
    init_snowflake(machine_id=machine_id)


@app.get("/", response_model=HealthResponse)
async def root(snowflake: SnowflakeGenerator = Depends(get_snowflake_generator)):
    """Root Path Health Check"""
    return {
        "status": "healthy",
        "machine_id": snowflake.machine_id,
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(snowflake: SnowflakeGenerator = Depends(get_snowflake_generator)):
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "machine_id": snowflake.machine_id,
        "version": "1.0.0"
    }


@app.get("/generate", response_model=GenerateResponse)
async def generate_id(snowflake: SnowflakeGenerator = Depends(get_snowflake_generator)):
    """Generate a new unique ID"""
    try:
        # generate ID
        uid = snowflake.next_id()
        
        # parse ID
        parsed = snowflake.parse_id(uid)
        
        return {
            "id": uid,
            "timestamp": parsed["timestamp"],
            "datetime": parsed["datetime"].isoformat(),
            "machine_id": parsed["machine_id"],
            "sequence": parsed["sequence"]
        }
    except RuntimeError as e:
        # Handling errors such as clock rollbacks
        raise HTTPException(status_code=500, detail=f"生成ID失败: {str(e)}")


@app.post("/parse", response_model=ParseResponse)
async def parse_id(
    request: ParseRequest,
    snowflake: SnowflakeGenerator = Depends(get_snowflake_generator)
):
    """Parse existing snowflake algorithm IDs"""
    try:
        # parse ID
        parsed = snowflake.parse_id(request.id)
        
        return {
            "id": request.id,
            "timestamp": parsed["timestamp"],
            "datetime": parsed["datetime"].isoformat(),
            "machine_id": parsed["machine_id"],
            "sequence": parsed["sequence"],
            "binary": bin(request.id)[2:].zfill(64)  # binary representation
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析ID失败: {str(e)}")


@app.get("/generate_batch/{count}")
async def generate_batch(
    count: int,
    snowflake: SnowflakeGenerator = Depends(get_snowflake_generator)
):
    """Batch generation of unique IDs

Args:
Count: The number of IDs to be generated, up to 100"""
    if count <= 0 or count > 100:
        raise HTTPException(status_code=400, detail="The count must be between 1 and 100")
    
    try:
        # batch generation of IDs
        ids = [snowflake.next_id() for _ in range(count)]
        return {"ids": ids}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"生成ID失败: {str(e)}")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """General Exception Handling"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器错误: {str(exc)}"}
    )


# If you run this file directly, start the Uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 