from sqlalchemy.orm import Session

from src.exchange.database.models import User


def find_user(db: Session, user_id: str = None, email: str = None) -> User | bool:
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif email:
        user = db.query(User).filter(User.email == email).first()
    else:
        raise ValueError("Either user_id or email must be provided.")

    if not user:
        return False

    return user
