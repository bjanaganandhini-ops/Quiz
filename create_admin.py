from app import app
from models import db, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

with app.app_context():

    hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")

    admin = User(
        username="admin",
        email="admin@gmail.com",
        password=hashed_password,
        role="admin"
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin created successfully!")