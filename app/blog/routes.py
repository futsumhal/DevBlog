from datetime import date
from functools import wraps
import re
from typing import Optional

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import BlogPost, Category, Comment, Tag
from forms import CreatecommentForm, CreatePostForm

blog_bp = Blueprint("blog", __name__)


def admins_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return abort(403)
        return func(*args, **kwargs)

    return wrapper


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug or "post"


def _unique_slug(title: str, current_post_id: Optional[int] = None) -> str:
    base = _slugify(title)
    candidate = base
    counter = 2
    while True:
        query = BlogPost.query.filter_by(slug=candidate)
        if current_post_id is not None:
            query = query.filter(BlogPost.id != current_post_id)
        if query.first() is None:
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1


def _parse_csv_names(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _sync_taxonomy(post: BlogPost, tags_csv: str, categories_csv: str):
    tag_names = _parse_csv_names(tags_csv)
    category_names = _parse_csv_names(categories_csv)

    post.tags = []
    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
        post.tags.append(tag)

    post.categories = []
    for name in category_names:
        category = Category.query.filter_by(name=name).first()
        if not category:
            category = Category(name=name)
        post.categories.append(category)


def _safe_next_url():
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/"):
        return next_url
    return None


@blog_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get_or_404(post_id)
    if requested_post.status == "draft" and (not current_user.is_authenticated or not current_user.is_admin):
        return abort(404)

    comment_page = request.args.get("cpage", 1, type=int)
    reply_to = request.args.get("reply_to", type=int)
    form = CreatecommentForm()
    if reply_to and request.method == "GET":
        form.parent_id.data = str(reply_to)
    elif not reply_to and form.parent_id.data:
        try:
            reply_to = int(form.parent_id.data)
        except (TypeError, ValueError):
            reply_to = None
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to log in to leave a comment.", "danger")
            return redirect(url_for("auth.login"))
        parent_comment = None
        if form.parent_id.data:
            try:
                parent_comment_id = int(form.parent_id.data)
                parent_comment = Comment.query.filter_by(
                    id=parent_comment_id,
                    post_id=requested_post.id,
                ).first()
            except ValueError:
                parent_comment = None
        new_comment = Comment(
            text=form.body.data,
            comment_author=current_user,
            parent_post=requested_post,
            approved=bool(current_user.is_admin),
            parent=parent_comment,
        )
        db.session.add(new_comment)
        db.session.commit()
        current_app.logger.info(
            "Comment added to post_id=%s by user_id=%s approved=%s",
            post_id,
            current_user.id,
            new_comment.approved,
        )
        return redirect(url_for("blog.show_post", post_id=post_id))

    comments_query = Comment.query.filter_by(post_id=requested_post.id, parent_id=None)
    if not (current_user.is_authenticated and current_user.is_admin):
        comments_query = comments_query.filter_by(approved=True)
    comments = comments_query.order_by(Comment.id.desc()).paginate(
        page=comment_page,
        per_page=5,
        error_out=False,
    )

    return render_template("post.html", post=requested_post, form=form, comments=comments, reply_to=reply_to)


@blog_bp.route("/new-post", methods=["GET", "POST"])
@admins_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        requested_status = form.status.data or "draft"
        status = requested_status if current_user.is_admin else "draft"
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            slug=_unique_slug(form.title.data),
            status=status,
            author_name=current_user.name,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
        )
        _sync_taxonomy(new_post, form.tags.data, form.categories.data)
        db.session.add(new_post)
        db.session.commit()
        current_app.logger.info("Post created id=%s by user_id=%s", new_post.id, current_user.id)
        return redirect(url_for("main.get_all_posts"))
    return render_template("make-post.html", form=form, is_edit=False)


@blog_bp.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admins_only
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body,
        tags=", ".join(tag.name for tag in post.tags),
        categories=", ".join(category.name for category in post.categories),
        status=post.status,
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        post.slug = _unique_slug(edit_form.title.data, current_post_id=post.id)
        if current_user.is_admin:
            post.status = edit_form.status.data
        _sync_taxonomy(post, edit_form.tags.data, edit_form.categories.data)
        db.session.commit()
        current_app.logger.info("Post updated id=%s by user_id=%s", post.id, current_user.id)
        return redirect(url_for("blog.show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)


@blog_bp.route("/delete/<int:post_id>")
@admins_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get_or_404(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    current_app.logger.info("Post deleted id=%s by user_id=%s", post_id, current_user.id)
    next_url = _safe_next_url()
    if next_url:
        return redirect(next_url)
    return redirect(url_for("main.get_all_posts"))


@blog_bp.route("/posts/<int:post_id>/publish")
@admins_only
def publish_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post.status = "published"
    db.session.commit()
    flash("Post published.", "success")
    next_url = _safe_next_url()
    if next_url:
        return redirect(next_url)
    return redirect(url_for("blog.show_post", post_id=post.id))


@blog_bp.route("/posts/<int:post_id>/unpublish")
@admins_only
def unpublish_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post.status = "draft"
    db.session.commit()
    flash("Post moved to draft.", "success")
    next_url = _safe_next_url()
    if next_url:
        return redirect(next_url)
    return redirect(url_for("blog.show_post", post_id=post.id))


@blog_bp.route("/comments/<int:comment_id>/approve")
@admins_only
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.approved = True
    db.session.commit()
    flash("Comment approved.", "success")
    next_url = _safe_next_url()
    if next_url:
        return redirect(next_url)
    cpage = request.args.get("cpage", 1, type=int)
    return redirect(url_for("blog.show_post", post_id=comment.post_id, cpage=cpage))


@blog_bp.route("/comments/<int:comment_id>/delete")
@admins_only
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "success")
    next_url = _safe_next_url()
    if next_url:
        return redirect(next_url)
    cpage = request.args.get("cpage", 1, type=int)
    return redirect(url_for("blog.show_post", post_id=post_id, cpage=cpage))


@blog_bp.route("/admin")
@admins_only
def admin_dashboard():
    draft_posts = BlogPost.query.filter_by(status="draft").order_by(BlogPost.id.desc()).all()
    approved_comments_count = Comment.query.filter_by(approved=True).count()
    pending_comments_count = Comment.query.filter_by(approved=False).count()
    pending_comments = (
        Comment.query.filter_by(approved=False)
        .order_by(Comment.id.desc())
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        draft_posts=draft_posts,
        pending_comments=pending_comments,
        approved_comments_count=approved_comments_count,
        pending_comments_count=pending_comments_count,
    )
