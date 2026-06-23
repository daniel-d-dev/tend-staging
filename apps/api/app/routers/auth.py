from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix = "/auth", tags = ["auth"])

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = None # accepts Bearer token for mobile or httponly cookie for web

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Not authenticated.")

    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "This token is invalid or expired.")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "User not found.")
    
    return user

@router.post("/register", response_model = UserResponse, status_code = status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # email must be unique, reject if it's already in use
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "This email has already been registered.")
    user = User(
        email = user_in.email,
        hashed_password = hash_password(user_in.password),
        first_name = user_in.first_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model = Token)
def login(user_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    # deliberately vague, not revealing whether the email exists or not
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Incorrect email or password.")
    token = create_access_token(user.id)
    response.set_cookie(
        key = "access_token",
        value = token,
        httponly = True,
        samesite = "lax",
        secure = False # set to True in production when serving over HTTPS
    )
    return Token(access_token = token)

@router.post("/logout")
def logout(response: Response):
    # no auth check is needed as clearing a cookie that doesn't exist does no harm
    response.delete_cookie(key = "access_token")
    return {"message": "Logged out"}

@router.get("/me", response_model = UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user