import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.database.db import get_db
from app.models.models import Crop, FarmerProfile, User

bearer = HTTPBearer(auto_error=False)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        uid = int(decode_token(creds.credentials)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user


def profile_of(db: Session, user: User) -> FarmerProfile:
    return db.query(FarmerProfile).filter_by(user_id=user.id).one()


def owned_crop(db: Session, user: User, crop_id: int) -> Crop:
    """404 (not 403) for other users' records so ids are not revealed."""
    crop = db.get(Crop, crop_id)
    if not crop or crop.user_id != user.id:
        raise HTTPException(404, "Crop not found")
    return crop
