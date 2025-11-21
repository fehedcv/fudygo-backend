from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from app.schemas.user import User
from app.core.auth import get_current_user, create_session_cookie, logout_user
from firebase_admin import auth
import datetime
from app.schemas.auth import SessionLoginRequest

router = APIRouter()


# 🔹 Create session cookie and ensure user exists in DB
@router.post("/session-login", description="Exchange Firebase ID token for a secure session cookie")
def session_login(
    data: SessionLoginRequest,  # 👈 The body will contain { "idToken": "..." }
    response: Response,
    db: Session = Depends(get_db)
):
    id_token = data.idToken  # Extract from JSON body

    # 🔹 Verify ID token from Firebase
    try:
        decoded_token = auth.verify_id_token(id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase ID token: {e}")

    # 🔹 Extract Firebase user info
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    name = decoded_token.get("name", "")
    picture = decoded_token.get("picture", "")
    phone = decoded_token.get("phone_number", None)

    if not firebase_uid or not email:
        raise HTTPException(status_code=400, detail="Invalid Firebase token payload")

    # 🔹 Check or create user in local DB
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == firebase_uid).first()

    if not db_user:
        db_user = ProfileModel(
            firebase_uid=firebase_uid,
            email=email,
            full_name=name or "Unnamed User",
            profile_picture_url=picture,
            phone_number=phone
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    else:
        # Optional: update existing info if changed in Firebase
        updated = False
        if db_user.full_name != name:
            db_user.full_name = name
            updated = True
        if db_user.profile_picture_url != picture:
            db_user.profile_picture_url = picture
            updated = True
        if db_user.phone_number != phone:
            db_user.phone_number = phone
            updated = True
        if updated:
            db.commit()
            db.refresh(db_user)

    # 🔹 Create long-lived session cookie (2 weeks)
    session_cookie = create_session_cookie(id_token)
    expires_in = datetime.timedelta(days=14)
    # 🔹 Set cookie on response
    response.set_cookie(
        key="session",
        value=session_cookie,
        max_age=int(expires_in.total_seconds()),
        httponly=True,
        secure=True,  # ⚠️ Set True in production (HTTPS)
        samesite="lax"
    )

    return {
        "message": "Session cookie created successfully",
        "user_id": firebase_uid,
        "email": email,
        "name": name,
    }

# 🔹 Logout
@router.post("/logout")
def logout(response: Response, current_user=Depends(get_current_user)):
    logout_user(current_user["user_id"])
    response.delete_cookie("session")
    return {"message": "Logged out"}

# 🔹 Protected route example
@router.get("/me", response_model=User)
def get_profile(current_user=Depends(get_current_user)):
    db_user = current_user["db_user"]
    return db_user
