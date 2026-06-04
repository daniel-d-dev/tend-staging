from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix = "/auth", tags = ["auth"])

@router.post("/register", response_model = UserResponse, status_code = status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # email must be unique, reject if it's already in use
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "This email has already been registered.")
    user = User(
        email = user_in.email,
        hashed_password = hash_password(user_in.password),
        display_name = user_in.display_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model = Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    # deliberately vague, not revealing whether the email exists or not
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Incorrect email or password.")
    token = create_access_token(user.id)
    return Token(access_token = token)