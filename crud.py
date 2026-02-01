from sqlalchemy.orm import Session
from models import User
from extensions import db
from extensions import bcrypt
from typing import List, Dict

# Get user by email
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

# Create user
def create_user(email, password):
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user

# Verify password
def verify_password(db: Session, email: str, password: str):
    user = get_user_by_email(email)
    return user and bcrypt.check_password_hash(user.password, password)

def update_user_password(db: Session, email: str, new_password: str):
    user = get_user_by_email(email)
    if user:
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        db.refresh(user)
        return user
    return None

def delete_user(db: Session, email: str):
    user = get_user_by_email(email)
    if user:
        db.session.delete(user)
        db.session.commit()