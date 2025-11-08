from sqlalchemy import update, func
from app.models.user import Profile as User

def add_role(db, user_id: int, role: str):
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(roles=func.array_append(func.coalesce(User.roles, '{}'), role))
    )
    db.execute(stmt)
    db.commit()