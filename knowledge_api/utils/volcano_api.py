import hashlib
import hmac
import json
import base64
from datetime import datetime
import urllib.parse
import aiohttp
import httpx
from typing import Dict, Any, Optional, Union, Tuple


class VolcanoAPIClient:
    """Volcano Engine API client side, handling request signing and authentication"""
    
    DEFAULT_HOST = "open.volcengineapi.com"
    DEFAULT_VERSION = "2024-01-01"
    DEFAULT_REGION = "cn-beijing"
    DEFAULT_SERVICE = "ark"
    
    def __init__(
        self, 
        access_key_id: str, 
        secret_access_key: str, 
        host: str = DEFAULT_HOST,
        region: str = DEFAULT_REGION,
        service: str = DEFAULT_SERVICE
    ):
        """Initialize Volcano Engine API client side

@Param {string} access_key_id - Access Key ID
@Param {string} secret_access_key - access key key
@Param {string} host - API host address, default is open.volcengineapi.com
@Param {string} region - region, default is cn-Beijing
@Param {string} service - service name, default is ark"""
        self.access_key_id = access_key_id
        # Check if secret_access_key is Base64 encoded, decode if so
        try:
            decoded = base64.b64decode(secret_access_key).decode('utf-8')
            if len(decoded) == 32 or len(decoded) == 40:  # Standard key length
                self.secret_access_key = decoded
            else:
                self.secret_access_key = secret_access_key
        except:
            self.secret_access_key = secret_access_key
            
        self.host = host
        self.region = region
        self.service = service
        
    def _hash(self, data: Union[str, bytes]) -> bytes:
        """Calculate the SHA256 hash value

@Param {string | bytes} data - data to hash
@Return {bytes} - hash result"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).digest()
    
    def _hex_encode(self, data: bytes) -> str:
        """Convert binary data to hexadecimal string

@Param {bytes} data - binary data to encode
@return {string} - hexadecimal string"""
        return data.hex()
    
    def _hmac_sha256(self, key: bytes, msg: str) -> bytes:
        """Calculate HMAC-SHA256

@param {bytes} key - key
@param {string} msg - message
@return {bytes} - HMAC result"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    def _get_canonical_headers(self, headers: Dict[str, str]) -> Tuple[str, str]:
        """build specification header

@param {Dict [str, str]} headers - request headers
@Return {Tuple [str, str]} - List of specification headers and signature headers"""
        canonical_headers = ""
        signed_headers = []
        
        # Make sure the header name is lowercase
        headers = {k.lower(): v for k, v in headers.items()}
        
        for header_name, header_value in sorted(headers.items()):
            canonical_headers += f"{header_name}:{header_value}\n"
            signed_headers.append(header_name)
        
        return canonical_headers, ";".join(signed_headers)
    
    def _get_canonical_request(
        self, 
        method: str, 
        uri: str, 
        query_string: str,
        headers: Dict[str, str],
        payload: str
    ) -> Tuple[str, str]:
        """build specification request

@Param {string} method - HTTP method
@param {string} uri - URI path
@param {string} query_string - query string
@param {Dict [str, str]} headers - request headers
@param {string} payload - request body
@Return {Tuple [str, str]} - specification request and signature header"""
        payload_hash = self._hex_encode(self._hash(payload))
        canonical_headers, signed_headers = self._get_canonical_headers(headers)
        
        canonical_request = f"{method}\n{uri}\n{query_string}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        
        return canonical_request, signed_headers
    
    def _get_signature_key(self, date_stamp: str) -> bytes:
        """Compute the signing key

@Param {string} date_stamp - date stamp in YYYYMMDD format
@Return {bytes} - Signing key"""
        k_secret = self.secret_access_key.encode('utf-8')
        k_date = self._hmac_sha256(k_secret, date_stamp)
        k_region = self._hmac_sha256(k_date, self.region)
        k_service = self._hmac_sha256(k_region, self.service)
        k_signing = self._hmac_sha256(k_service, "request")
        return k_signing
    
    def _sign_request(
        self, 
        method: str, 
        uri: str, 
        query_params: Dict[str, str],
        headers: Dict[str, str], 
        payload: Dict[str, Any]
    ) -> Dict[str, str]:
        """Signature Request

@Param {string} method - HTTP method
@param {string} uri - URI path
@Param {Dict [str, str]} query_params - query parameters
@param {Dict [str, str]} headers - request headers
@param {Dict [str, Any]} payload - request body
@Return {Dict [str, str]} - Signed request header"""
        # Get the current time as X-Date
        now = datetime.utcnow()
        amz_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = now.strftime('%Y%m%d')
        
        # Prepare request body
        payload_str = json.dumps(payload) if payload else '{}'
        payload_hash = self._hex_encode(self._hash(payload_str))
        
        # Prepare canonical query string
        canonical_query_string = ""
        if query_params:
            # Sorting and URL encoding parameter names and values
            sorted_params = sorted(query_params.items())
            canonical_query_string = "&".join(
                f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
                for k, v in sorted_params
            )
        
        # Prepare request headers
        headers_to_sign = {
            'host': self.host,
            'x-content-sha256': payload_hash,
            'x-date': amz_date
        }
        
        # Merge other request headers
        for key, value in headers.items():
            headers_to_sign[key.lower()] = value
        
        # build specification request
        canonical_request, signed_headers = self._get_canonical_request(
            method, uri, canonical_query_string, headers_to_sign, payload_str
        )
        
        # Build Signature Range
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/request"
        
        # Build pending string
        string_to_sign = (
            f"HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
            f"{self._hex_encode(self._hash(canonical_request))}"
        )
        
        # Compute the signing key
        signing_key = self._get_signature_key(date_stamp)
        
        # Compute signature
        signature = self._hex_encode(self._hmac_sha256(signing_key, string_to_sign))
        
        # Build authorization header
        authorization = (
            f"HMAC-SHA256 Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        
        # Prepare the final request header
        final_headers = {
            'Authorization': authorization,
            'Content-Type': 'application/json',
            'X-Content-Sha256': payload_hash,
            'X-Date': amz_date,
            'Host': self.host
        }
        
        # Merge custom request headers
        for key, value in headers.items():
            if key.lower() not in [k.lower() for k in final_headers]:
                final_headers[key] = value
        
        return final_headers
    
    def _build_url(self, action: str, version: Optional[str] = None) -> str:
        """build request URL

@Param {string} action - API action name
@param {string | None} version - API version
@return {string} - full URL"""
        version = version or self.DEFAULT_VERSION
        return f"https://{self.host}/?Action={action}&Version={version}"
    
    def _get_url_with_params(self, query_params: Dict[str, str]) -> str:
        """Building a URL with parameters

@Param {Dict [str, str]} query_params - query parameters
@Return {string} - URL with parameters"""
        url = f"https://{self.host}/?"
        url_params = []
        for k, v in sorted(query_params.items()):
            url_params.append(f"{k}={urllib.parse.quote(str(v))}")
        return url + "&".join(url_params)
    
    async def request_async(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        uri: str = "/",
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        version: Optional[str] = None,
        url: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Send API requests asynchronously

@Param {string} action - API action name
@param {Dict [str, Any] | None} payload - request body
@Param {string} method - HTTP method, defaults to POST
@Param {string} uri - URI path, default is "/"
@Param {Dict [str, str] | None} query_params - query parameters
@Param {Dict [str, str] | None} headers - custom request headers
@param {string | None} version - API version
@Param {string | None} url - custom URL, build automatically if not provided
@Param {int} timeout - request timed out in seconds
@Return {Dict [str, Any]} - API response"""
        headers = headers or {}
        query_params = query_params or {}
        payload = payload or {}
        version = version or self.DEFAULT_VERSION
        
        # If an Action is provided, add it to the query parameters
        if action:
            query_params['Action'] = action
        
        # If a version is provided, add it to the query parameters
        if version:
            query_params['Version'] = version

        # Signature Request
        signed_headers = self._sign_request(method, uri, query_params, headers, payload)
        
        # Build URL
        if not url:
            url = self._get_url_with_params(query_params)
        
        # Send request
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=signed_headers,
                json=payload,
                timeout=timeout
            ) as response:
                response_json = await response.json()
                return response_json
    
    def request(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        uri: str = "/",
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        version: Optional[str] = None,
        url: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Send API requests synchronously

@Param {string} action - API action name
@param {Dict [str, Any] | None} payload - request body
@Param {string} method - HTTP method, defaults to POST
@Param {string} uri - URI path, default is "/"
@Param {Dict [str, str] | None} query_params - query parameters
@Param {Dict [str, str] | None} headers - custom request headers
@param {string | None} version - API version
@Param {string | None} url - custom URL, build automatically if not provided
@Param {int} timeout - request timed out in seconds
@Return {Dict [str, Any]} - API response"""
        headers = headers or {}
        query_params = query_params or {}
        payload = payload or {}
        version = version or self.DEFAULT_VERSION
        
        # If an Action is provided, add it to the query parameters
        if action:
            query_params['Action'] = action
        
        # If a version is provided, add it to the query parameters
        if version:
            query_params['Version'] = version
        
        # Signature Request
        signed_headers = self._sign_request(method, uri, query_params, headers, payload)
        
        # Build URL
        if not url:
            url = self._get_url_with_params(query_params)
        
        # Send request
        with httpx.Client(timeout=timeout) as client:
            response = client.request(
                method=method,
                url=url,
                headers=signed_headers,
                json=payload,
            )
            return response.json() 