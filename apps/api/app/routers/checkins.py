from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import tempfile
import os
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
from app.core.database import get_db
from app.core.sentiment import score_text
from app.models.checkin import CheckIn
from app.routers.auth import get_current_user
from app.schemas.checkin import CheckInCreate, CheckInUpdate, CheckInResponse
from app.models.user import User
from app.services.prompts import get_todays_prompt
from app.services.transcription import transcribe_audio
from app.services.audio_emotion import score_audio

router = APIRouter(prefix = "/checkins", tags = ["checkins"])

@router.get("/prompt/today")
def get_prompt_today(current_user: User = Depends(get_current_user)):
    return {"prompt": get_todays_prompt()}

@router.post("/note/transcribe")
async def transcribe_note(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    with tempfile.NamedTemporaryFile(delete = False, suffix = ".m4a") as tmp: # delete = false keeps the file on disk (temporarily) after closing so whisper can read it
        tmp.write(await audio.read())
        tmp_path = tmp.name
    try:
        transcript = transcribe_audio(tmp_path)
        audio_emotion = score_audio(tmp_path)
        return {"transcript": transcript, "audio_emotion": audio_emotion}
    finally:
        os.remove(tmp_path) # always runs even if the transcription fails

@router.post("/", response_model = CheckInResponse)
def submit_checkin (
    data: CheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(CheckIn).filter(
        CheckIn.user_id == current_user.id,
        CheckIn.checkin_date == date.today()
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "You have already checked in today.") # only 1 check in per day allowed
    
    scoring_result = score_text(data.prompt_response) # returns None if the model fails and stored as null in the db

    checkin = CheckIn(
        user_id = current_user.id,
        checkin_date = date.today(),
        prompt_question = data.prompt_question,
        prompt_response = data.prompt_response,
        journal_text = data.journal_text,
        sleep_hours = data.sleep_hours,
        step_count = data.step_count,
        sentiment_score = scoring_result["formula_g"] if scoring_result else None,
        band_label = scoring_result["band"] if scoring_result else None,
        audio_emotion_score = data.audio_emotion_score
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin

@router.get("/today", response_model = CheckInResponse)
def get_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    checkin = db.query(CheckIn).filter(
        CheckIn.user_id == current_user.id,
        CheckIn.checkin_date == date.today()
    ).first()

    if not checkin:
        raise HTTPException(status_code = 404, detail = "No check-in found for today.")
    
    return checkin

@router.patch("/today", response_model = CheckInResponse)
def update_today(
    data: CheckInUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)   
):
    checkin = db.query(CheckIn).filter(
        CheckIn.user_id == current_user.id,
        CheckIn.checkin_date == date.today()
    ).first()

    if not checkin:
        raise HTTPException(status_code = 404, detail = "No check-in found for today.")
    
    if data.prompt_response is not None:
        checkin.prompt_response = data.prompt_response
    if data.journal_text is not None:
        checkin.journal_text = data.journal_text
    if data.sleep_hours is not None:
        checkin.sleep_hours = data.sleep_hours
    if data.step_count is not None:
        checkin.step_count = data.step_count
    if data.audio_emotion_score is not None:
        checkin.audio_emotion_score = data.audio_emotion_score
    
    db.commit()
    db.refresh(checkin)
    return checkin

@router.get("/me", response_model = list[CheckInResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    checkins = db.query(CheckIn).filter(
        CheckIn.user_id == current_user.id
    ).order_by(CheckIn.checkin_date.desc()).all()

    return checkins