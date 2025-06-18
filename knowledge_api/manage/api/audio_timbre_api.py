from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.audio_timbre.base import AudioTimbreResponse, AudioTimbreCreate, AudioTimbre, AudioTimbreUpdate
from knowledge_api.mapper.audio_timbre.crud import AudioTimbreCRUD

router_audio_timbre = APIRouter(prefix="/audio-timbre", tags=["timbre management"])


@router_audio_timbre.post("/", response_model=AudioTimbreResponse)
async def create_audio_timbre(
        timbre: AudioTimbreCreate,
        db: Session = Depends(get_session)
) -> AudioTimbre:
    """Create timbre"""
    crud = AudioTimbreCRUD(db)
    return await crud.create(timbre=timbre)


@router_audio_timbre.get("/{timbre_id}", response_model=AudioTimbreResponse)
async def get_audio_timbre(
        timbre_id: int,
        db: Session = Depends(get_session)
) -> AudioTimbre:
    """Get a single tone"""
    crud = AudioTimbreCRUD(db)
    timbre = await crud.get_by_id(timbre_id=timbre_id)
    if not timbre:
        raise HTTPException(status_code=404, detail="The timbre doesn't exist.")
    return timbre


@router_audio_timbre.get("/speaker/{speaker_id}", response_model=AudioTimbreResponse)
async def get_audio_timbre_by_speaker_id(
        speaker_id: str,
        db: Session = Depends(get_session)
) -> AudioTimbre:
    """Get timbre according to sound ID"""
    crud = AudioTimbreCRUD(db)
    timbre = await crud.get_by_speaker_id(speaker_id=speaker_id)
    if not timbre:
        raise HTTPException(status_code=404, detail="The timbre doesn't exist.")
    return timbre


@router_audio_timbre.get("/", response_model=List[AudioTimbreResponse])
async def list_audio_timbres(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        state: str = None,
        db: Session = Depends(get_session)
) -> List[AudioTimbre]:
    """Get a list of sounds"""
    crud = AudioTimbreCRUD(db)
    if state:
        return await crud.get_by_state(state=state, skip=skip, limit=limit)
    return await crud.get_all(skip=skip, limit=limit)


@router_audio_timbre.put("/{timbre_id}", response_model=AudioTimbreResponse)
async def update_audio_timbre(
        timbre_id: int,
        timbre_update: AudioTimbreUpdate,
        db: Session = Depends(get_session)
) -> AudioTimbre:
    """update tone"""
    crud = AudioTimbreCRUD(db)
    timbre = await crud.update(timbre_id, timbre_update)
    if not timbre:
        raise HTTPException(status_code=404, detail="The timbre doesn't exist.")
    return timbre


@router_audio_timbre.delete("/{timbre_id}", response_model=bool)
async def delete_audio_timbre(
        timbre_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete timbre"""
    crud = AudioTimbreCRUD(db)
    success = await crud.delete(timbre_id=timbre_id)
    if not success:
        raise HTTPException(status_code=404, detail="The timbre doesn't exist.")
    return True 