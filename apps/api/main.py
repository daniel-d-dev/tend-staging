from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
from app.models.user import User # noqa: F401
from app.models.checkin import CheckIn  # noqa: F401
from app.models.nudge import NudgeFlag # noqa: F401
from app.models.group import Group, GroupMember, FriendAssignment # noqa: F401
from app.models.notification import Notification # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.groups import router as groups_router
from app.routers.checkins import router as checkins_router
from app.routers.notifications import router as notifications_router
from app.routers.nudges import router as nudges_router
from app.core.sentiment import load_model

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tend API")

load_model() # load sentiment model on startup so it's ready on the first request

# allow requests from the web app and mobile dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(checkins_router)
app.include_router(groups_router)
app.include_router(nudges_router)
app.include_router(notifications_router)

@app.get("/health")
def health():
    return {"status": "ok"}