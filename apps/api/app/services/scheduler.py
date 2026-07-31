from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import SessionLocal
from app.models.user import User
from app.models.checkin import CheckIn
from app.models.notification import Notification
from app.services.inference import run_inference
from app.services.nudge_delivery import queue_notification
from app.services.evaluation import evaluate_pending_nudges
from app.services.coordinator import coordinator_job
from app.routers.checkins import score_and_evaluate_checkin
import httpx

scheduler = BackgroundScheduler()

def catch_up_missed_scores():
    with SessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes = 15) # gives the original background task a fair chance to actually finish, rather than assuming it's stuck when it's just still running
        stuck_ids = [
            c.id for c in db.query(CheckIn.id).filter(
                CheckIn.sentiment_score == None,
                CheckIn.created_at < cutoff
            ).all()
        ]
    # score_and_evaluate_checkin opens its own database session for each checkin, same as it does when the original background task calls it. This closes the session above first, instead of keeping two open at once
    for checkin_id in stuck_ids:
        score_and_evaluate_checkin(checkin_id)

def run_nightly_inference():
    catch_up_missed_scores() # catches any checkin that never got scored like something crashing or failing part of the way through before checking everyone's trends below, which needs sentiment_score to already be filled in
    with SessionLocal() as db:
        users = db.query(User).all()
        for user in users:
            flag = run_inference(user.id, db)
            if flag:
                queue_notification(flag, db)

def send_push_notifications():
    with SessionLocal() as db:
        pending = db.query(Notification).filter(Notification.pushed_at == None).all() # only unsent notifications
        for notification in pending:
            recipient = db.query(User).filter(User.id == notification.recipient_id).first()
            if recipient and recipient.push_token:
                response = httpx.post("https://exp.host/--/api/v2/push/send", json = {
                    "to": recipient.push_token,
                    "title": "Tend",
                    "body": notification.message
                })
                if response.status_code == 200 and response.json().get("data", {}).get("status") == "ok":
                    notification.pushed_at = datetime.now(timezone.utc)
        db.commit()

def run_post_nudge_evaluation():
    with SessionLocal() as db:
        evaluate_pending_nudges(db)

def start_scheduler():
    scheduler.add_job(run_nightly_inference, CronTrigger(hour = 0, minute = 0)) # midnight utc
    scheduler.add_job(send_push_notifications, CronTrigger(hour = 9, minute = 0)) # 9am utc after nightly inference
    scheduler.add_job(run_post_nudge_evaluation, CronTrigger(hour = 10, minute = 0)) # 10am utc after push notifs sent
    scheduler.add_job(coordinator_job, CronTrigger(hour = 11, minute = 0)) # daily coordinator check, cooldown logic decides whether to post or not. 11am utc after evaluation job
    scheduler.start()