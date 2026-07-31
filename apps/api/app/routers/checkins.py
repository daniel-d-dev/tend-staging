from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from starlette.concurrency import run_in_threadpool
import tempfile
import os
from sqlalchemy.orm import Session
from datetime import date
from app.core.database import get_db, SessionLocal
from app.core.sentiment import score_text
from app.models.checkin import CheckIn
from app.routers.auth import get_current_user
from app.schemas.checkin import CheckInCreate, CheckInUpdate, CheckInResponse
from app.models.user import User
from app.services.prompts import get_todays_prompt
from app.services.transcription import transcribe_audio, get_audio_duration
from app.services.audio_emotion import score_audio
from app.services.inference import run_inference
from app.services.nudge_delivery import queue_notification, needs_friend_assignment

router = APIRouter(prefix = "/checkins", tags = ["checkins"])

MAX_RECORDING_SECONDS = 180 # an 8.3-minute recording took over 10 minutes to transcribe on this hardware. keeps the worst case from taking too long. The mobile app already stops recording at the same limit - this is just the backstop on the server side

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
        try:
            duration = await run_in_threadpool(get_audio_duration, tmp_path)
        except Exception:
            duration = None # malformed audio. let the transcription error handling below catch it properly, rather than reporting a duration-specific error for an unrelated failure
        if duration is not None and duration > MAX_RECORDING_SECONDS:
            raise HTTPException(status_code = 422, detail = f"Recordings are limited to {MAX_RECORDING_SECONDS // 60} minutes. Please keep it a bit shorter.")
        try: # transcribe_audio and score_audio both keep the processor busy while they run, and don't hand control back until they're finished. calling them directly inside this async would block the whole event loop, freezing the server for every other user, not just the one submitting it. run_in_threadpool moves that work onto a separate thread instead, so the event loop stays free for everyone else, and this request just waits for its own result like normal
            transcript = await run_in_threadpool(transcribe_audio, tmp_path)
        except Exception: # a corrupt/invalid recording (interrupted upload, bad codec, empty file) raised an unhandled error from whisper/ffmpeg. That showed up as a raw 500, or a connection reset in one case. either way, nothing the app could show the user. Genuinely silent but valid audio still works fine though, it transcribes cleanly to an empty string, so this only catches the files that are actually broken
            raise HTTPException(status_code = 422, detail = "Couldn't process that recording. Please try again or type your response instead.")
        audio_emotion = await run_in_threadpool(score_audio, tmp_path) # already defensive, returns None on failure rather than raising
        return {"transcript": transcript, "audio_emotion": audio_emotion}
    finally:
        os.remove(tmp_path) # always runs even if the transcription fails

def score_and_evaluate_checkin(checkin_id: int):
    with SessionLocal() as db:
        checkin = db.query(CheckIn).filter(
            CheckIn.id == checkin_id
        ).first()
        if not checkin:
            return

        scoring_result = score_text(checkin.text_for_scoring)
        checkin.sentiment_score = scoring_result["mean_score"] if scoring_result else None
        db.flush() # makes the score visible to run_inference's own queries within this same transaction, without committing yet

        flag = run_inference(checkin.user_id, db)
        if flag:
            queue_notification(flag, db) # checked immediately here rather than waiting for the nightly job so distress gets caught as soon as it's scored

        # committing sentiment_score separately, before run_inference ran, meant other sessions could see "scored" while the flag decision was still in flight. one commit here means sentiment_score and any resulting flag always become visible together, or not at all
        db.commit()

@router.post("/", response_model = CheckInResponse)
def submit_checkin (
    data: CheckInCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(CheckIn).filter(
        CheckIn.user_id == current_user.id,
        CheckIn.checkin_date == date.today()
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "You have already checked in today.") # only 1 check in per day allowed

    if needs_friend_assignment(current_user.id, db): # blocks group members specifically. not being in a group yet is a separate, earlier step. Someone who joins a group but never submits a check-in never reaches this check at all
        raise HTTPException(status_code = 400, detail = "Please assign a designated friend in your group before checking in, so someone knows to reach out if you ever need support.")

    checkin = CheckIn(
        user_id = current_user.id,
        checkin_date = date.today(),
        prompt_question = data.prompt_question,
        prompt_response = data.prompt_response,
        journal_text = data.journal_text,
        sleep_hours = data.sleep_hours,
        step_count = data.step_count,
        sentiment_score = None, # filled in by the background task once the scoring finishes
        audio_emotion_score = data.audio_emotion_score
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    background_tasks.add_task(score_and_evaluate_checkin, checkin.id) # scoring can take some time so it runs after the response instead of blocking it

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
    background_tasks: BackgroundTasks,
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

    # an edit here never re-triggered scoring or nudge evaluation. A check-in that started out mundane and was later edited to disclose real distress could go unnoticed for up to 24 hours, until the next nightly job ran and even then sentiment_score itself would stay the same, since nothing was actually rescoring it. Requeuing the same background task the POST endpoint already uses keeps both in sync with whatever the check-in currently says
    background_tasks.add_task(score_and_evaluate_checkin, checkin.id)

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