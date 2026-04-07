from datetime import datetime

from sqlalchemy.orm import relationship

from app.extensions import db

post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("blog_posts.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)

post_categories = db.Table(
    "post_categories",
    db.Column("post_id", db.Integer, db.ForeignKey("blog_posts.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(100))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    slug = db.Column(db.String(280), unique=True, nullable=True, index=True)
    status = db.Column(db.String(20), nullable=True, default="published")
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = relationship("Comment", back_populates="parent_post", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
    categories = relationship("Category", secondary=post_categories, back_populates="posts")


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

    posts = relationship("BlogPost", secondary=post_tags, back_populates="tags")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

    posts = relationship("BlogPost", secondary=post_categories, back_populates="categories")
