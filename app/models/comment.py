from sqlalchemy.orm import relationship

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, nullable=True, default=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)
    replies = relationship("Comment", backref=db.backref("parent", remote_side=[id]))
