from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import SessionLocal
from app.models.user import User
from app.models.notification import Notification
from app.services.inference import run_inference
from app.services.nudge_delivery import deliver
from app.services.evaluation import evaluate_pending_nudges
from app.services.coordinator import coordinator_job
import httpx

scheduler = BackgroundScheduler()

def run_nightly_inference():
    with SessionLocal() as db:
        users = db.query(User).all()
        for user in users:
            flag = run_inference(user.id, db)
            if flag:
                deliver(flag, db)

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
                if response.status_code == 200:
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