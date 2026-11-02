from app.database import SessionLocal
from app.models import User
from app.security import hash_password, verify_password

email = "test@example.com"
password = "Test@12345"

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(name="Test User", email=email, password_hash=hash_password(password))
        db.add(user)
        print("created new user")
    else:
        user.password_hash = hash_password(password)
        user.is_active = True
        print("updated existing user")
    db.commit()

    db.refresh(user)
    print("hash length:", len(user.password_hash))
    print("match:", verify_password(password, user.password_hash))
finally:
    db.close()