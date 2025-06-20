import os
import alibabacloud_oss_v2 as oss
from typing import Dict, Any, Tuple, Optional
import base64
import uuid
from datetime import datetime


class OSSManager:
    """Alibaba Cloud Object Storage Manager
Upload file and get file URL"""
    
    def __init__(self):
        """Initialize OSS Manager"""
        self.client = None
        self.region = os.environ.get('OSS_REGION', 'cn-beijing')
        self.bucket = os.environ.get('OSS_BUCKET', 'ai-game-chat-test')
        self.endpoint = os.environ.get('OSS_ENDPOINT', f'oss-{self.region}.aliyuncs.com')
        
    async def init_client(self) -> None:
        """Initialize the OSS client side"""
        if self.client is not None:
            return
            
        # Load credential information from environment variables
        credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
        
        # Load SDK default configuration
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = self.region
        cfg.endpoint = self.endpoint
        
        # Creating the OSS client side
        self.client = oss.Client(cfg)
    
    async def upload_file(self, file_path: str, key: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Upload local files to OSS

Parameter:
- file_path: local file path
- key: object name, automatically generated by default

Return:
- (success, result): success status and result"""
        try:
            # Initialize client side
            await self.init_client()
            
            # Check if the file exists
            if not os.path.exists(file_path):
                return False, {"error": f"文件不存在: {file_path}"}
                
            # Generate object name
            if not key:
                file_ext = os.path.splitext(file_path)[1]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                key = f"upload/{uuid.uuid4().hex}_{timestamp}{file_ext}"
            
            # Read file content
            with open(file_path, 'rb') as file:
                data = file.read()
            
            # Upload file
            result = self.client.put_object(oss.PutObjectRequest(
                bucket=self.bucket,
                key=key,
                body=data,
            ))
            
            # generate URL
            file_url = f"https://{self.bucket}.{self.endpoint}/{key}"
            
            return True, {
                "file_url": file_url,
                "key": key,
                "status_code": result.status_code,
                "etag": result.etag,
                "content_md5": result.content_md5
            }
            
        except Exception as e:
            return False, {"error": f"上传文件失败: {str(e)}"}
    
    async def upload_bytes(self, data: bytes, key: Optional[str] = None, file_ext: str = '.bin') -> Tuple[bool, Dict[str, Any]]:
        """Upload byte data to OSS

Parameter:
- data: byte data
- key: object name, automatically generated by default
- file_ext: file extension

Return:
- (success, result): success status and result"""
        try:
            # Initialize client side
            await self.init_client()
            
            # Generate object name
            if not key:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                key = f"upload/{uuid.uuid4().hex}_{timestamp}{file_ext}"
            
            # upload data
            result = self.client.put_object(oss.PutObjectRequest(
                bucket=self.bucket,
                key=key,
                body=data,
            ))
            
            # generate URL
            file_url = f"https://{self.bucket}.{self.endpoint}/{key}"
            
            return True, {
                "file_url": file_url,
                "key": key,
                "status_code": result.status_code,
                "etag": result.etag,
                "content_md5": result.content_md5
            }
            
        except Exception as e:
            return False, {"error": f"上传数据失败: {str(e)}"}
    
    async def upload_base64(self, base64_data: str, file_ext: str = '.png', key: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Upload Base64 encoded data to OSS

Parameter:
- base64_data: Base64 encoded data
- file_ext: file extension
- key: object name, automatically generated by default

Return:
- (success, result): success status and result"""
        try:
            # Decode Base64 data
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            
            binary_data = base64.b64decode(base64_data)
            
            # Upload Byte Data
            return await self.upload_bytes(binary_data, key, file_ext)
            
        except Exception as e:
            return False, {"error": f"上传Base64数据失败: {str(e)}"}
    
    async def get_object_url(self, key: str) -> str:
        """Get the URL of the object

Parameter:
- key: object name

Return:
- Object URL"""
        return f"https://{self.bucket}.{self.endpoint}/{key}" 