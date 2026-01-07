# app/core/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from sqlalchemy import update, func
from app.models.user import Profile as User


security = HTTPBearer()


def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and verify Firebase ID token from the Authorization Bearer header.

    Returns the decoded Firebase token (claims) on success.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization token")

    try:
        # Verify ID token and check for revocation on every protected request
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or revoked token: {e}")


def get_current_user(decoded_token: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)):
    """Dependency that returns user info derived from Firebase ID token and local DB user record.

    - Verifies presence of uid/email in token
    - Ensures a corresponding local `Profile` exists (creates on demand)
    - Returns a dict with `user_id`, `email`, `db_user`, and full `claims`
    """
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    if not firebase_uid or not email:
        raise HTTPException(status_code=401, detail="Invalid Firebase token payload")

    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == firebase_uid).first()

    # Create local user record if missing (keeps backend stateless regarding auth)
    if not db_user:
        db_user = ProfileModel(
            firebase_uid=firebase_uid,
            email=email,
            full_name=decoded_token.get("name", "Unnamed User"),
            profile_picture_url=decoded_token.get("picture", ""),
            phone_number=decoded_token.get("phone_number", None),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    return {"user_id": firebase_uid, "email": email, "db_user": db_user, "claims": decoded_token}


def _has_role_in_claims(claims: dict, role: str) -> bool:
    """Check for role presence in Firebase custom claims.

    Preferred source: `roles` custom claim (list).
    Fallback: boolean claim with role name or DB lookup.
    """
    roles = claims.get("roles")
    if isinstance(roles, (list, tuple)):
        return role in roles

    # boolean-style custom claim (e.g. {"admin": True})
    flag = claims.get(role)
    if isinstance(flag, bool) and flag:
        return True

    return False


def check_role(role: str):
    def role_checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        claims = current_user.get("claims", {})
        if _has_role_in_claims(claims, role):
            return True

        # Fallback to DB roles stored on Profile
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")

        db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not db_user.roles or role not in db_user.roles:
            raise HTTPException(status_code=403, detail=f"Not authorized as {role}")

        return True
    return role_checker


def check_any_role(roles: list[str]):
    def role_checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        claims = current_user.get("claims", {})
        # Check token claims first
        if any(_has_role_in_claims(claims, r) for r in roles):
            return True

        # Fallback to DB roles
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")

        db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not db_user.roles or not any(role in db_user.roles for role in roles):
            raise HTTPException(status_code=403, detail=f"Not authorized with required roles")

        return True
    return role_checker


def add_role(db, user_id: int, role: str):
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(roles=func.array_append(func.coalesce(User.roles, '{}'), role))
    )
    db.execute(stmt)
    db.commit()