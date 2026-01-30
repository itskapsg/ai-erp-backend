from app.database import SessionLocal
from app.models.core import User, UserRole
from app.services.auth_service import AuthService

db = SessionLocal()
try:
    user = db.query(User).filter_by(username="admin").first()
    if not user:
        print("Creating admin user...")
        user = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            hashed_password=AuthService.get_password_hash("admin"),
            is_active=True
        )
        db.add(user)
        db.commit()
        print("Admin user created.")
    else:
        print("Admin user exists. Resetting password...")
        user.hashed_password = AuthService.get_password_hash("admin")
        user.is_active = True
        db.commit()
        print("Admin password reset to 'admin'.")
finally:
    db.close()
