from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from typing import Dict, Any, List
import os
from datetime import datetime

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.audio_timbre.crud import AudioTimbreCRUD
from knowledge_api.framework.tts.tts_utils import TTSManager

# Create route
router_tts = APIRouter(prefix="/tts", tags=["Text To Speech"])

# audio file save path
AUDIO_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                              "static", "audio_files")

# Dependency Injection Get TTS Manager Instance
async def get_tts_manager():
    """Provides dependency injection functions for TTS Manager instances

Return:
- TTSManager instance"""
    tts_manager = TTSManager()
    await tts_manager.init_data()
    return tts_manager


@router_tts.post("/text-to-speech")
async def text_to_speech(
    text: str,
    speaker_id: str,
    speed_ratio: float = 1.0,
    volume_ratio: float = 1.0,
    pitch_ratio: float = 1.0,
    save_file: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_session),
    tts_manager: TTSManager = Depends(get_tts_manager)
) -> Dict[str, Any]:
    """Text to Speech API

Parameter:
- text: text content to convert
- speaker_id: Tone ID
- speed_ratio: Speech rate ratio (0.5-2)
- volume_ratio: Volume ratio (0.5-2)
- pitch_ratio: pitch ratio (0.5-2)
- save_file: whether to save as file

Return:
- audio_data: Base64 encoded audio data
- file_path: saved file path (if save_file = True)"""
    # parameter validation
    if not text:
        raise HTTPException(status_code=400, detail="Text content cannot be empty")
    
    if not speaker_id:
        raise HTTPException(status_code=400, detail="Tone ID cannot be empty")
    
    # Check if the timbre exists
    crud = AudioTimbreCRUD(db)
    timbre = await crud.get_by_speaker_id(speaker_id=speaker_id)
    if not timbre:
        raise HTTPException(status_code=404, detail="The timbre doesn't exist.")
    
    # Check timbre status
    if timbre.state != "active":
        raise HTTPException(status_code=400, detail="timbre not activated")
    
    # preparation parameters
    params = {
        "speed_ratio": max(0.5, min(2.0, speed_ratio)),
        "volume_ratio": max(0.5, min(2.0, volume_ratio)),
        "pitch_ratio": max(0.5, min(2.0, pitch_ratio))
    }
    
    # Invoke TTS service
    success, result = await tts_manager.text_to_speech(text, speaker_id, params)
    
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error", "TTS conversion failed"))
    
    # Get audio data
    audio_data = result.get("audio_data", "")
    
    # If you need to save the file
    file_path = ""
    if save_file and audio_data:
        # generate filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{speaker_id}_{timestamp}.mp3"
        file_path = os.path.join(AUDIO_FILES_DIR, file_name)
        
        # Save file asynchronously
        if background_tasks:
            background_tasks.add_task(tts_manager.save_audio_file, audio_data, file_path)
        else:
            await tts_manager.save_audio_file(audio_data, file_path)
            
        # Audition audio to update the tone
        if timbre and not timbre.audition:
            update_data = {"audition": audio_data, "update_at": "system"}
            await crud.update(timbre.id, update_data)
    
    # Return result
    return {
        "success": True,
        "audio_data": audio_data,
        "file_path": file_path if save_file else None
    }


@router_tts.get("/voices")
async def get_voice_list(
    sync_to_db: bool = False,
    db: Session = Depends(get_session),
    tts_manager: TTSManager = Depends(get_tts_manager)
) -> Dict[str, Any]:
    """Get a list of available sounds

Parameter:
- sync_to_db: Whether to synchronize to database

Return:
- voices: list of sounds"""
    # Call the Volcano Engine TTS service to get the sound list
    success, result = await tts_manager.get_voice_list()
    
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get sound list"))
    
    voices = result.get("voices", [])
    
    # If you need to synchronize to the database
    if sync_to_db and voices:
        crud = AudioTimbreCRUD(db)
        for voice in voices:
            await tts_manager.process_voice_data(crud, voice)
    
    # Return result
    return {
        "success": True,
        "voices": voices,
        "total": len(voices)
    }


@router_tts.post("/voices/activate")
async def activate_voices(
    speaker_ids: List[str],
    db: Session = Depends(get_session),
    tts_manager: TTSManager = Depends(get_tts_manager)
) -> Dict[str, Any]:
    """Activate tone

Parameter:
- speaker_ids: List of timbre IDs to activate

Return:
- success: whether it was successful
- message: result message"""
    if not speaker_ids:
        raise HTTPException(status_code=400, detail="Tone ID list cannot be empty")
    
    # Invoke the Volcano Engine TTS service to activate the sound
    success, result = await tts_manager.activate_voice(speaker_ids)
    
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error", "Activation sound failed"))
    
    # Update the timbre status in the database
    crud = AudioTimbreCRUD(db)
    for speaker_id in speaker_ids:
        timbre = await crud.get_by_speaker_id(speaker_id=speaker_id)
        if timbre:
            await crud.update(timbre.id, {"state": "active", "update_at": "system"})
    
    # Return result
    return {
        "success": True,
        "message": result.get("message", "Sound activated successfully")
    }


@router_tts.post("/voices/sync")
async def sync_voices(
    db: Session = Depends(get_session),
    tts_manager: TTSManager = Depends(get_tts_manager)
) -> Dict[str, Any]:
    """Synchronize timbre data

Return:
- success: whether it was successful
- message: result message
- total: number of sounds synchronized"""
    # Call the Volcano Engine TTS service to get the sound list
    success, result = await tts_manager.get_voice_list()
    
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get sound list"))
    
    voices = result.get("voices", [])
    
    # Synchronize to database
    if voices:
        crud = AudioTimbreCRUD(db)
        for voice in voices:
            await tts_manager.process_voice_data(crud, voice)
    
    # Return result
    return {
        "success": True,
        "message": "Timbre data synced successfully",
        "total": len(voices)
    }
