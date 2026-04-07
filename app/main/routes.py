import smtplib

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_

from app.models import BlogPost, Category, Tag

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def get_all_posts():
    page = request.args.get("page", 1, type=int)
    search = (request.args.get("q") or "").strip()
    selected_tag = (request.args.get("tag") or "").strip()
    selected_category = (request.args.get("category") or "").strip()

    query = BlogPost.query
    if not (current_user.is_authenticated and current_user.is_admin):
        query = query.filter_by(status="published")
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(BlogPost.title.ilike(pattern), BlogPost.body.ilike(pattern)))
    if selected_tag:
        query = query.join(BlogPost.tags).filter(Tag.name.ilike(selected_tag))
    if selected_category:
        query = query.join(BlogPost.categories).filter(Category.name.ilike(selected_category))

    posts = query.distinct().order_by(BlogPost.id.desc()).paginate(page=page, per_page=5, error_out=False)
    all_tags = Tag.query.order_by(Tag.name.asc()).all()
    all_categories = Category.query.order_by(Category.name.asc()).all()
    return render_template(
        "index.html",
        all_posts=posts.items,
        pagination=posts,
        search_query=search,
        selected_tag=selected_tag,
        selected_category=selected_category,
        all_tags=all_tags,
        all_categories=all_categories,
    )


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message_body = request.form.get("message")

        username = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")
        recipient = current_app.config.get("MAIL_TO")

        if not username or not password:
            flash("Email sender is not configured. Please set MAIL_USERNAME and MAIL_PASSWORD.", "danger")
            current_app.logger.error("Contact email is not configured")
            return redirect(url_for("main.contact"))

        try:
            with smtplib.SMTP_SSL(
                current_app.config.get("MAIL_SERVER"),
                current_app.config.get("MAIL_PORT"),
            ) as connection:
                connection.login(user=username, password=password)
                connection.sendmail(
                    from_addr=username,
                    to_addrs=recipient or username,
                    msg=(
                        "Subject: New Contact Form Submission\n\n"
                        f"Name: {name}\n"
                        f"Email: {email}\n"
                        f"Phone: {phone}\n\n"
                        f"Message:\n{message_body}"
                    ),
                )
            flash("Your message has been sent successfully.", "success")
            current_app.logger.info("Contact form message sent from: %s", email)
        except smtplib.SMTPException as exc:
            current_app.logger.exception("SMTP error while sending contact form")
            flash(f"An error occurred while sending your message: {exc}", "danger")
        except Exception as exc:
            current_app.logger.exception("Unexpected error while sending contact form")
            flash(f"An unexpected error occurred: {exc}", "danger")

        return redirect(url_for("main.contact"))

    return render_template("contact.html")
