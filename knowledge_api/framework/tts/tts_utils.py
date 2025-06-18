import base64
import json
import os
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
import aiohttp

from .tts_service import ByteDanceTTS, VolcanoTTS
from .config import (DEFAULT_SPEECH_PARAMS)
from knowledge_api.mapper.audio_timbre.crud import AudioTimbreCRUD
from knowledge_api.mapper.audio_timbre.base import AudioTimbreCreate, AudioTimbreUpdate
from ..redis.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class TTSManager:
    """TTS manager for text-to-speech and sound management"""
    
    def __init__(self):
        """Initialize TTS Manager"""
        # Initialize ByteDance TTS
        self.config=None
        self.bytedance_tts = None
        # Initialize Volcano Engine TTS (if configured)
        self.volcano_tts = None


    async def init_data(self):
        config = json.loads(await CacheManager().get_system_config("BYTE_DANCE_TTS_CONFIG"))
        self.config = config
        self.bytedance_tts = ByteDanceTTS(
            appid=config.get("appid"),
            access_token=config.get("access_token"),
            cluster=config.get("cluster")
        )

        # Initialize Volcano Engine TTS (if configured)
        self.volcano_tts = None
        if config.get("ak") and config.get("sk"):
            self.volcano_tts = VolcanoTTS(
                ak=config.get("ak"),
                sk=config.get("sk")
            )
    
    async def text_to_speech(self, 
                           text: str, 
                           speaker_id: str, 
                           params: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """Text to Speech

@Param text: text to convert
@Param speaker_id: Tone ID
@Param params: conversion parameters
@Return: (success flag, data dictionary) - successful return (True, {"audio_data": base64 audio data}), failed return (False, {"error": error message})"""
        if not text or not speaker_id:
            return False, {"error": "Text or timbre ID cannot be empty"}
        
        if not params:
            params = DEFAULT_SPEECH_PARAMS.copy()
        
        try:
            # Invoke the ByteDance TTS service
            result = self.bytedance_tts.text_to_speech(
                text=text,
                voice_type=speaker_id,
                speed_ratio=params.get("speed_ratio", 1.0),
                volume_ratio=params.get("volume_ratio", 1.0),
                pitch_ratio=params.get("pitch_ratio", 1.0),
                encoding=params.get("encoding", "mp3")
            )
            
            # Inspection results
            if "data" in result:
                return True, {"audio_data": result["data"]}
            else:
                error_msg = result.get("error", "unknown error")
                logger.error(f"TTS转换失败: {error_msg}")
                return False, {"error": error_msg}
                
        except Exception as e:
            logger.exception(f"TTS转换异常: {str(e)}")
            return False, {"error": f"TTS转换异常: {str(e)}"}
    
    async def get_voice_list(self) -> Tuple[bool, Dict[str, Any]]:
        """Get a list of available sounds

@Return: (success flag, data dictionary) - successful return (True, {"voices": timbre list}), failed return (False, {"error": error message})"""
        DEFAULT_APP_ID = self.config.get("appid")
        if not self.volcano_tts or not DEFAULT_APP_ID:
            return False, {"error": "Volcano Engine TTS not configured or application ID not set"}
        
        # try:
            # Get a list of sounds
        result =await self.volcano_tts.list_mega_tts_train_status(app_id=DEFAULT_APP_ID)

        # Inspection results
        if "Result" in result and "Statuses" in result["Result"]:
            voices = result["Result"]["Statuses"]
            return True, {"voices": voices}
        else:
            error_msg = result.get("ResponseMetadata", {}).get("Error", {}).get("Message", "unknown error")
            logger.error(f"获取音色列表失败: {error_msg}")
            return False, {"error": error_msg}
                
        # except Exception as e:
        #     Logger.exception (f "get tone list exception: {str (e) }")
        #     Returns False, {"error": f "Get tone list exception: {str (e) }"}
    
    async def activate_voice(self, speaker_ids: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """Activate tone

@Param speaker_ids: List of tone IDs to activate
@Return: (success flag, data dictionary) - return on success (True, {"message": "activation successful"}), return on failure (False, {"error": error message})"""
        DEFAULT_APP_ID = self.config.get("appid")
        if not self.volcano_tts or not DEFAULT_APP_ID:
            return False, {"error": "Volcano Engine TTS not configured or application ID not set"}
        
        if not speaker_ids:
            return False, {"error": "Tone ID list cannot be empty"}
        
        try:
            # Activate tone
            result = await self.volcano_tts.activate_mega_tts_train_status(
                app_id=DEFAULT_APP_ID,
                speaker_ids=speaker_ids
            )
            
            # Inspection results
            if "Result" in result and result["Result"].get("Success", False):
                return True, {"message": "Sound activated successfully"}
            else:
                error_msg = result.get("ResponseMetadata", {}).get("Error", {}).get("Message", "unknown error")
                logger.error(f"激活音色失败: {error_msg}")
                return False, {"error": error_msg}
                
        except Exception as e:
            logger.exception(f"激活音色异常: {str(e)}")
            return False, {"error": f"激活音色异常: {str(e)}"}
    
    @staticmethod
    async def save_audio_file(audio_data: str, file_path: str) -> bool:
        """Save audio file

@Param audio_data: Base64 encoded audio data
@Param file_path: save path
@Return: whether the save was successful"""
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Decode and save
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(audio_data))
            
            return True
        except Exception as e:
            logger.exception(f"保存音频文件失败: {str(e)}")
            return False
    
    @staticmethod
    async def process_voice_data(crud: AudioTimbreCRUD, voice_data: Dict[str, Any]) -> None:
        """Process timbre data, update or create timbre records

@param crud: AudioTimbreCRUD object
@Param voice_data: timbre data"""
        try:
            # Get timbre information
            speaker_id = voice_data.get("SpeakerID")
            if not speaker_id:
                return
            
            # Search for existing records
            existing = await crud.get_by_speaker_id(speaker_id=speaker_id)
            
            # Prepare timbre data
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expire_time = voice_data.get("ExpireTime", "")
            if expire_time:
                # Convert timestamps returned by Volcano Engine to datetime
                try:
                    expire_timestamp = int(expire_time) / 1000  # Convert to second timestamp
                    expire_time = datetime.fromtimestamp(expire_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    expire_time = ""
            
            # state mapping
            state_map = {
                "Success": "active",
                "UNAVAILABLE": "inactive",
                "TRAINING": "training"
            }

            # Get audio data
            audition = None
            demo_audio_url = voice_data.get("DemoAudio")
            if demo_audio_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(demo_audio_url) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                audition = base64.b64encode(audio_data).decode('utf-8')
                except Exception as e:
                    logger.error(f"获取音频数据失败: {str(e)}")
            
            # Update or create
            if existing:
                # Update existing records
                update_data = AudioTimbreUpdate(
                    alias=voice_data.get("Alias", existing.alias),
                    version=voice_data.get("Version", existing.version),
                    expire_time=expire_time or existing.expire_time,
                    state=state_map.get(voice_data.get("State"), "inactive"),
                    update_at="system",
                    audition=audition if audition else existing.audition
                )
                await crud.update(existing.id, update_data)
            else:
                # Create a new record
                create_data = AudioTimbreCreate(
                    alias=voice_data.get("Alias", ""),
                    speaker_id=speaker_id,
                    version=voice_data.get("Version", ""),
                    expire_time=expire_time or None,
                    state=state_map.get(voice_data.get("State"), "inactive"),
                    craete_at="system",
                    audition=audition
                )
                await crud.create(timbre=create_data)
                
        except Exception as e:
            logger.exception(f"处理音色数据异常: {str(e)}")
    
    @staticmethod
    def get_audio_base64(file_path: str) -> Optional[str]:
        """Get the Base64 encoding of the audio file

@Param file_path: audio file path
@Return: Base64 encoded audio data"""
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, "rb") as f:
                audio_data = f.read()
            
            return base64.b64encode(audio_data).decode("utf-8")
        except Exception as e:
            logger.exception(f"获取音频Base64编码失败: {str(e)}")
            return None 