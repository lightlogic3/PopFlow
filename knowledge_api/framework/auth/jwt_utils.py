from datetime import datetime, timedelta
import json
import uuid
import jwt
from typing import Dict, Optional, List, Any
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time

# JWT configuration, which should be read from the configuration file in practical applications
SECRET_KEY = "your-super-secret-key-please-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 240  # 4 hours


class JWTUtils:
    """JWT utility class for generating, validating, and parsing JWT tokens"""

    @staticmethod
    def create_access_token(
        user_id: int, 
        username: str,
        session_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token - slim version that stores only the necessary identification information

Args:
user_id: User ID
Username: username
session_id: Session ID, automatically generated if None
expires_delta: expiration date

Returns:
STR: JWT token string"""
        # If no session ID is provided, a new UUID is generated.
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # Only key identifying information is retained
        to_encode = {
            "user_id": user_id,
            "username": username,
            "session_id": session_id,
            "iat": datetime.utcnow(),  # issue time
        }
        
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict:
        """Decode JWT Token

Args:
Token: JWT token string

Returns:
Dict: Decoded data"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            # Use specific error codes to facilitate front-end identification of token expiration
            raise HTTPException(
                status_code=401, 
                detail={
                    "code": 50014,  # Use a specific error code to identify token expiration
                    "message": "The token has expired, please log in again"
                }
            )
        except jwt.InvalidTokenError:
            # Use a specific error code to facilitate front-end identification of invalid tokens
            raise HTTPException(
                status_code=401, 
                detail={
                    "code": 50015,  # Use a specific error code to identify an invalid token
                    "message": "Invalid token, please log in again"
                }
            )
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """Verify that the token is valid

Args:
Token: JWT token string

Returns:
Bool: Does it work?"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True
        except:
            return False
    
    @staticmethod
    def get_token_expire_time(token: str) -> int:
        """Get token expiration timestamp

Args:
Token: JWT token string

Returns:
Int: timestamp"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("exp", 0)
        except:
            return 0
    
    @staticmethod
    def refresh_token(token: str, new_expiry: Optional[timedelta] = None) -> str:
        """refresh token

Args:
Token: original JWT token string
new_expiry: new expiration time

Returns:
STR: new JWT token string"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Retain the original session ID and user information
            user_id = payload.get("user_id")
            username = payload.get("username") 
            session_id = payload.get("session_id")
            
            if not user_id or not username or not session_id:
                raise HTTPException(status_code=401, detail="Invalid token content")
                
            # Create a new token
            return JWTUtils.create_access_token(
                user_id=user_id,
                username=username, 
                session_id=session_id,
                expires_delta=new_expiry
            )
        except:
            raise HTTPException(status_code=401, detail="Failed to refresh token")

    @staticmethod
    def get_session_id(token: str) -> Optional[str]:
        """Get the session ID from the token

Args:
Token: JWT token string

Returns:
Optional [str]: Session ID"""
        try:
            payload = JWTUtils.decode_token(token)
            return payload.get("session_id")
        except:
            return None


class JWTBearer(HTTPBearer):
    """JWT token validation class for FastAPI routing dependencies"""

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Dict:
        """Verify the JWT token in the request

Args:
Request: request object

Returns:
Dict: Decoded token data"""
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            payload = self.verify_jwt_token(credentials.credentials)
            return payload
        else:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    def verify_jwt_token(self, jwt_token: str) -> Dict:
        """Verify JWT Token

Args:
jwt_token: JWT token string

Returns:
Dict: Decoded data"""
        return JWTUtils.decode_token(jwt_token) 