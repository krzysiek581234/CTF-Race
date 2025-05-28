import os
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import string
import secrets

from sqlmodel import select

from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PROD")  # ☝️
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# -------- password helpers --------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -------- JWT helpers --------
def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": subject}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_unique_activation_code(session, length: int = 8) -> str:
    import secrets, string
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        exists = session.exec(select(User).where(User.activation_code == code)).first()
        if not exists:
            return code