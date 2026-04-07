import hashlib
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.orm import relationship

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar
        normalized_email = (self.email or "").strip().lower()
        digest = hashlib.md5(normalized_email.encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s=100"
