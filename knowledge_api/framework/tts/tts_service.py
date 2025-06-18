import base64
import json
import uuid
import datetime
import hashlib
import hmac
from urllib.parse import quote
from typing import Optional, Dict, Any
import httpx


class ByteDanceTTS:
    """ByteDance TTS Service"""
    def __init__(self, appid: str, access_token: str, cluster: str):
        """Initialize ByteDance TTS

@Param appid: app id
@Param access_token: access token
@param cluster: cluster"""
        self.appid = appid
        self.access_token = access_token
        self.cluster = cluster
        self.host = "openspeech.bytedance.com"
        self.api_url = f"https://{self.host}/api/v1/tts"
        self.header = {"Authorization": f"Bearer;{self.access_token}"}

    async def text_to_speech(self, 
                     text: str, 
                     voice_type: str, 
                     speed_ratio: float = 1.0,
                     volume_ratio: float = 1.0,
                     pitch_ratio: float = 1.0,
                     encoding: str = "mp3") -> Dict[str, Any]:
        """Text to Speech

@Param text: text to convert
@Param voice_type: Tone Type
@Param speed_ratio: Speech rate ratio
@Param volume_ratio: volume ratio
@Param pitch_ratio: pitch ratio
@param encoding: encoding format
@Return: response dictionary containing audio data"""
        request_json = {
            "app": {
                "appid": self.appid,
                "token": "access_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "388808087185088"
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": encoding,
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.api_url, 
                    json=request_json, 
                    headers=self.header
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}


class VolcanoTTS:
    """Volcano Engine TTS Service"""
    # Volcano Engine TTS Constant
    SERVICE = "speech_saas_prod"
    VERSION = "2023-11-07"
    REGION = "cn-north-1"
    HOST = "open.volcengineapi.com"
    CONTENT_TYPE = "application/json; charset=utf-8"
    
    def __init__(self, ak: str, sk: str):
        """Initialize Volcano Engine TTS

@param ak: AccessKey
@param sk: SecretKey"""
        self.ak = ak
        self.sk = sk
    
    @staticmethod
    def _norm_query(params: Dict) -> str:
        """normalized query parameters

@Param params: parameter dictionary
@Return: normalized query string"""
        query = ""
        for key in sorted(params.keys()):
            if type(params[key]) == list:
                for k in params[key]:
                    query = (
                            query + quote(key, safe="-_.~") + "=" + quote(k, safe="-_.~") + "&"
                    )
            else:
                query = (query + quote(key, safe="-_.~") + "=" + quote(params[key], safe="-_.~") + "&")
        query = query[:-1]
        return query.replace("+", "%20")
    
    @staticmethod
    def _hmac_sha256(key: bytes, content: str) -> bytes:
        """HMAC-SHA256 encryption

@param key: key
@param content: content
@return: encrypted result"""
        return hmac.new(key, content.encode("utf-8"), hashlib.sha256).digest()
    
    @staticmethod
    def _hash_sha256(content: str) -> str:
        """SHA256 hash

@param content: content
@Return: hash result"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    async def _request(self, method: str, date: datetime.datetime, query: Dict, 
               header: Dict, action: str, body: Optional[str]) -> Dict:
        """Send a signature request

@param method: HTTP method
@param date: date time
@param query: query parameters
@param header: request header
@Param action: action name
@param body: request body
@return: response result"""
        # Initialize the proof of identity structure
        credential = {
            "access_key_id": self.ak,
            "secret_access_key": self.sk,
            "service": self.SERVICE,
            "region": self.REGION,
        }
        
        # Initialize signature structure
        request_param = {
            "body": body if body is not None else "",
            "host": self.HOST,
            "path": "/",
            "method": method,
            "content_type": self.CONTENT_TYPE,
            "date": date,
            "query": {"Action": action, "Version": self.VERSION, **query},
        }
        
        # Initialize the structure of the signature result
        x_date = request_param["date"].strftime("%Y%m%dT%H%M%SZ")
        short_x_date = x_date[:8]
        x_content_sha256 = self._hash_sha256(request_param["body"])
        sign_result = {
            "Host": request_param["host"],
            "X-Content-Sha256": x_content_sha256,
            "X-Date": x_date,
            "Content-Type": request_param["content_type"],
        }
        
        # Compute Signature Signature
        signed_headers_str = ";".join(
            ["content-type", "host", "x-content-sha256", "x-date"]
        )
        
        canonical_request_str = "\n".join(
            [request_param["method"].upper(),
             request_param["path"],
             self._norm_query(request_param["query"]),
             "\n".join(
                 [
                     "content-type:" + request_param["content_type"],
                     "host:" + request_param["host"],
                     "x-content-sha256:" + x_content_sha256,
                     "x-date:" + x_date,
                 ]
             ),
             "",
             signed_headers_str,
             x_content_sha256,
             ]
        )
        
        hashed_canonical_request = self._hash_sha256(canonical_request_str)
        credential_scope = "/".join([short_x_date, credential["region"], credential["service"], "request"])
        string_to_sign = "\n".join(["HMAC-SHA256", x_date, credential_scope, hashed_canonical_request])
        
        k_date = self._hmac_sha256(credential["secret_access_key"].encode("utf-8"), short_x_date)
        k_region = self._hmac_sha256(k_date, credential["region"])
        k_service = self._hmac_sha256(k_region, credential["service"])
        k_signing = self._hmac_sha256(k_service, "request")
        signature = self._hmac_sha256(k_signing, string_to_sign).hex()
        
        sign_result["Authorization"] = "HMAC-SHA256 Credential={}, SignedHeaders={}, Signature={}".format(
            credential["access_key_id"] + "/" + credential_scope,
            signed_headers_str,
            signature,
        )
        
        header = {**header, **sign_result}
        
        # Send HTTP request
        async with httpx.AsyncClient() as client:
            r = await client.request(
                method=method,
                url="https://{}{}".format(request_param["host"], request_param["path"]),
                headers=header,
                params=request_param["query"],
                data=request_param["body"],
            )
            
            return r.json()
    
    async def list_mega_tts_train_status(self, app_id: str, speaker_ids: Optional[list] = None) -> Dict:
        """Get a list of training states

@Param app_id: App ID
@Param speaker_ids: List of sound IDs
@Return: Timbre training status list"""
        now = datetime.datetime.utcnow()
        
        body_dict = {"AppID": app_id}
        if speaker_ids:
            body_dict["SpeakerIDs"] = speaker_ids
            
        body = json.dumps(body_dict)
        
        return await self._request("POST", now, {}, {}, "ListMegaTTSTrainStatus", body)
    
    async def activate_mega_tts_train_status(self, app_id: str, speaker_ids: list) -> Dict:
        """Activate training state

@Param app_id: App ID
@Param speaker_ids: List of sound IDs
@return: activation result"""
        now = datetime.datetime.utcnow()
        
        body = json.dumps({
            "AppID": app_id,
            "SpeakerIDs": speaker_ids,
        })
        
        return await self._request("POST", now, {}, {}, "ActivateMegaTTSTrainStatus", body) 