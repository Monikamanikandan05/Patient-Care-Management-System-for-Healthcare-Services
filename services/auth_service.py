from sqlalchemy.orm import Session
from models.models import User
from core.security import hash_password, verify_password

def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None

def register_user(db: Session, name: str, email: str, password: str, role: str, gender: str, phone: str):
    existing = db.query(User).filter(User.email == email.strip().lower()).first()
    if existing:
        raise ValueError("An account with this email address already exists.")
    
    hashed = hash_password(password)
    new_user = User(
        full_name=name.strip(),
        email=email.strip().lower(),
        password_hash=hashed,
        role=role,
        gender=gender,
        phone=phone.strip()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
