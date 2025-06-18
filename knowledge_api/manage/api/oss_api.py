import uuid

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlmodel import Session
from typing import Dict, Any, Optional
import os
from datetime import datetime
import shutil
import tempfile

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.oss.oss_utils import OSSManager

# Create route
router_oss = APIRouter(prefix="/oss", tags=["object storage"])

# Temporary file directory
TEMP_DIR = os.path.join(tempfile.gettempdir(), "ai-game-chat-upload")
os.makedirs(TEMP_DIR, exist_ok=True)

# Dependency Injection Get OSS Manager Instance
async def get_oss_manager():
    """Provides dependency injection functions for OSS Manager instances

Return:
- OSSManager instance"""
    oss_manager = OSSManager()
    await oss_manager.init_client()
    return oss_manager


@router_oss.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = Form("upload"),
    oss_manager: OSSManager = Depends(get_oss_manager)
) -> Dict[str, Any]:
    """Upload files to OSS

Parameter:
- file: uploaded file
- folder: stored directory path (optional)

Return:
- success: whether it was successful
- file_url: file URL
- key: object key name"""
    if not file:
        raise HTTPException(status_code=400, detail="File cannot be empty")
    
    try:
        # Get file extension
        _, file_ext = os.path.splitext(file.filename)
        
        # Generate temporary file path
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_file_path = os.path.join(TEMP_DIR, f"temp_{timestamp}{file_ext}")
        
        # Save the uploaded file to a temporary directory
        with open(temp_file_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
        # Generate object key names
        if folder:
            key = f"{folder}/{os.path.basename(file.filename)}"
        else:
            key = f"upload/{uuid.uuid4()}-{os.path.basename(file.filename)}"
        
        # Upload files to OSS
        success, result = await oss_manager.upload_file(temp_file_path, key)
        
        # Delete Temporary File
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        if not success:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to upload file"))
        
        # Return result
        return {
            "success": True,
            "file_url": result.get("file_url", ""),
            "key": result.get("key", ""),
            "etag": result.get("etag", "")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")
    finally:
        # Close file
        await file.close()


@router_oss.post("/upload-base64")
async def upload_base64(
    base64_data: str,
    file_ext: str = ".png",
    folder: Optional[str] = "images",
    oss_manager: OSSManager = Depends(get_oss_manager)
) -> Dict[str, Any]:
    """Upload Base64 encoded data to OSS

Parameter:
- base64_data: Base64 encoded data
- file_ext: file extension
- folder: stored directory path (optional)

Return:
- success: whether it was successful
- file_url: file URL
- key: object key name"""
    if not base64_data:
        raise HTTPException(status_code=400, detail="Base64 data cannot be empty")
    
    try:
        # Generate object key names
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        key = f"{folder}/{timestamp}{file_ext}" if folder else f"upload/{timestamp}{file_ext}"
        
        # Upload Base64 data to OSS
        success, result = await oss_manager.upload_base64(base64_data, file_ext, key)
        
        if not success:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to upload Base64 data"))
        
        # Return result
        return {
            "success": True,
            "file_url": result.get("file_url", ""),
            "key": result.get("key", ""),
            "etag": result.get("etag", "")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传Base64数据失败: {str(e)}")


@router_oss.get("/get-url/{key}")
async def get_object_url(
    key: str,
    oss_manager: OSSManager = Depends(get_oss_manager)
) -> Dict[str, Any]:
    """Get the URL of the object

Parameter:
- key: object key name

Return:
- success: whether it was successful
- file_url: file URL"""
    if not key:
        raise HTTPException(status_code=400, detail="Object key name cannot be empty")
    
    try:
        # Get object URL
        file_url = await oss_manager.get_object_url(key)
        
        # Return result
        return {
            "success": True,
            "file_url": file_url,
            "key": key
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对象URL失败: {str(e)}") 