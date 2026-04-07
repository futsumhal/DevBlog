from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from forms import Loginform, RegisterForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("You have already registered with that email. Please log in.", "danger")
            current_app.logger.info("Registration blocked for existing email: %s", form.email.data)
            return redirect(url_for("auth.login"))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length=8,
        )
        new_user = User(
            name=form.username.data,
            email=form.email.data,
            password=hash_and_salted_password,
            role="user",
        )
        db.session.add(new_user)
        db.session.commit()
        current_app.logger.info("User registered: %s", new_user.email)
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = Loginform()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            current_app.logger.info("User logged in: %s", user.email)
            return redirect(url_for("main.get_all_posts"))
        if user and not check_password_hash(user.password, password):
            flash("Password incorrect. Please try again.", "danger")
            current_app.logger.warning("Failed login attempt (wrong password): %s", email)
            return redirect(url_for("auth.login"))

        flash("The email does not exist. Please try again.", "danger")
        current_app.logger.warning("Failed login attempt (unknown email): %s", email)
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    current_app.logger.info("User logged out")
    return redirect(url_for("main.get_all_posts"))
