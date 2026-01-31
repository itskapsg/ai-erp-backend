import sys
import os
sys.path.append(os.getcwd())

import bcrypt
from app.database import SessionLocal
from app.models.core import User, UserRole

def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

db = SessionLocal()
try:
    user = db.query(User).filter_by(username="admin").first()
    if not user:
        print("Creating admin user...")
        user = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            password_hash=get_password_hash("admin"),
            is_active=True
        )
        db.add(user)
        db.commit()
        print("Admin user created.")
        print("Admin user exists. Resetting password...")
        user.password_hash = get_password_hash("admin")
        user.is_active = True
        db.commit()
        print("Admin password reset to 'admin'.")
finally:
    db.close()
