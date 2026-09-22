import re

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.hashing import MAX_PASSWORD_BYTES, hash_password, verify_password
from app.auth.jwt_middleware import create_access_token
from app.db.models import User, get_db
from app.auth.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Hashed once at import so login takes similar time whether or not the
# email exists (prevents user enumeration via response timing).
_DUMMY_HASH = hash_password("dummy-password-for-timing-only")


def validate_password_policy(password: str, email: str | None = None) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain a digit")
    if email and email.split("@")[0].lower() in password.lower():
        raise ValueError("Password must not contain your email name")
    return password


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_policy(v)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    points: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterBody, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    email = body.email.lower()

    try:
        validate_password_policy(body.password, email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=email, password_hash=hash_password(body.password), points=0)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return TokenOut(access_token=token, user=UserOut(id=user.id, email=user.email, points=user.points))


@router.post("/login", response_model=TokenOut)
def login(body: LoginBody, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    check_rate_limit(request)

    user = db.query(User).filter(User.email == body.email.lower()).first()

    # Always run one hash verification, even for unknown emails.
    hash_to_check = user.password_hash if user else _DUMMY_HASH
    password_correct = verify_password(body.password, hash_to_check)

    if not user or not password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, user.email)
    return TokenOut(access_token=token, user=UserOut(id=user.id, email=user.email, points=user.points))