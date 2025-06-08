import random 
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from passlib.hash import argon2
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.models.auth_model import User
from app.database.db_connect import config, get_db
from fastapi import APIRouter


router = APIRouter(prefix="/users", tags=["Users"])

SECRET_KEY = config["JWT_SECRET_KEY"]
ALGORITHM = config["JWT_ALGORITHM"]
ACCESS_TOKEN_EXPIRE_HOURS = config["ACCESS_TOKEN_EXPIRE_HOURS"]

SMTP_SERVER = config["SMTP_SERVER"]
SMTP_PORT = config["SMTP_PORT"]
SENDER_EMAIL = config["SENDER_EMAIL"]
SENDER_PASSWORD = config["SENDER_PASSWORD"]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token") # only for Swagger

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload["sub"], "role": payload["role"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_roles(*allowed_roles: list[int]):
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: insufficient role"
            )
        return user
    return role_checker


class UserInput(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]
    email_address: Annotated[EmailStr, Field(max_length=100)]
    password: Annotated[str, Field(min_length=1, max_length=255, strip_whitespace=True)]
    i_user_role: int

class LoginInput(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]
    password: Annotated[str, Field(min_length=1, max_length=255, strip_whitespace=True)]

class UserRoleInput(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]


def user_exists(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def generate_password(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def send_email(recipient: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")


@router.post("/add_user")
async def add_user(user_data: UserInput, db: Session = Depends(get_db), _: dict = Depends(require_roles(1))):
    if user_exists(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with that username already exists"
        )

    hashed_password = argon2.hash(user_data.password)
    user = User(
        username=user_data.username,
        email_address=user_data.email_address,
        password_hash=hashed_password,
        i_user_role=user_data.i_user_role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"i_user": user.i_user}


@router.get("/get_user")
async def get_user(username: str, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    user = user_exists(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"i_user": user.i_user, "username": user.username, "email_address": user.email_address, "i_user_role": user.i_user_role}


@router.put("/update_user")
async def update_user(user_data: UserInput, db: Session = Depends(get_db), _: dict = Depends(require_roles(1))):
    user = user_exists(db, user_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.email_address = user_data.email_address
    user.password_hash = argon2.hash(user_data.password)
    user.i_user_role = user_data.i_user_role

    db.commit()
    db.refresh(user)
    return {"i_user": user.i_user}


@router.delete("/delete_user")
async def delete_user(username: str, db: Session = Depends(get_db), _: dict = Depends(require_roles(1))):
    user = user_exists(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    return {"i_user": user.i_user}


def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
async def login(user_data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not argon2.verify(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_token(
        {"sub": user.username, "role": user.i_user_role}, 
        timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def users_me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "role": user["role"]}


@router.post("/set_temp_password")
async def set_temp_password(username: str, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    user = user_exists(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    new_password = generate_password()

    hashed_password = argon2.hash(new_password)
    user.password_hash = hashed_password
    db.commit()
    db.refresh(user)

    subject = "Password Reset Notification"
    body = f"Hello {user.username},\n\nYour new password is: {new_password}\nPlease change it during login."
    print(body)
    #send_email(user.email_address, subject, body)

    return {"i_user": user.i_user }


@router.post("/update_password")
async def update_password(username: str, temp_password: str, new_password: str, db: Session = Depends(get_db),  _: dict = Depends(require_roles(1, 2))):
    user = user_exists(db, username)
    if not user or not argon2.verify(temp_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.password_hash = argon2.hash(new_password)

    db.commit()
    db.refresh(user)
    return {"i_user": user.i_user}



@router.post("/token")  # only for Swagger
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not argon2.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(
        {"sub": user.username, "role": user.i_user_role},
        timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    return {"access_token": token, "token_type": "bearer"}
