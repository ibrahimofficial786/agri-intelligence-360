from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import current_user, profile_of
from app.core.security import create_token, hash_password, verify_password
from app.database.db import get_db
from app.models.models import FarmerProfile, User
from app.schemas.schemas import LoginIn, ProfileUpdate, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_out(db, user) -> UserOut:
    p = profile_of(db, user)
    return UserOut(id=user.id, email=user.email, full_name=p.full_name, district=p.district, mandal=p.mandal,
                   language=p.language, is_demo=user.is_demo)


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == body.email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user); db.flush()
    db.add(FarmerProfile(user_id=user.id, full_name=body.full_name, district=body.district, mandal=body.mandal,
                         language=body.language))
    db.commit()
    return TokenOut(access_token=create_token(user.id), user=user_out(db, user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return TokenOut(access_token=create_token(user.id), user=user_out(db, user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_out(db, user)


@router.put("/me", response_model=UserOut)
def update_me(body: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = profile_of(db, user)
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(p, k, v)
    db.commit()
    return user_out(db, user)
