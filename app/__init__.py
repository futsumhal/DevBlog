import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import current_user
from sqlalchemy import inspect, text

from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from app.errors import register_error_handlers
from app.extensions import ckeditor, db, login_manager, migrate
from app.logging_config import configure_logging

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    config_name = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).lower()
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    app.config.from_object(config_map.get(config_name, DevelopmentConfig))

    configure_logging(app)
    app.logger.info("Creating app with '%s' config", config_name)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_user_helpers():
        return {
            "is_admin": current_user.is_authenticated and getattr(current_user, "is_admin", False)
        }

    from app.auth.routes import auth_bp
    from app.blog.routes import blog_bp
    from app.main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.logger.info("Blueprints registered: main, auth, blog")
    register_error_handlers(app)

    with app.app_context():
        if app.config.get("DB_CREATE_ALL_FALLBACK", True):
            db.create_all()
        _ensure_backward_compat_schema()
        app.logger.info("Database compatibility checks completed")

    return app


def _ensure_backward_compat_schema():
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" not in user_columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
            connection.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
    with db.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE users SET role = 'admin' "
                "WHERE id = 1 AND (role IS NULL OR role = 'user') "
                "AND NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin')"
            )
        )

    if "bio" not in user_columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
    if "avatar" not in user_columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR(500)"))
    if "created_at" not in user_columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))

    table_names = set(inspector.get_table_names())
    if "blog_posts" in table_names:
        post_columns = {column["name"] for column in inspector.get_columns("blog_posts")}
        if "slug" not in post_columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE blog_posts ADD COLUMN slug VARCHAR(280)"))
        if "status" not in post_columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE blog_posts ADD COLUMN status VARCHAR(20) DEFAULT 'published'"))
                connection.execute(text("UPDATE blog_posts SET status = 'published' WHERE status IS NULL"))
        if "updated_at" not in post_columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE blog_posts ADD COLUMN updated_at DATETIME"))

    if "comments" in table_names:
        comment_columns = {column["name"] for column in inspector.get_columns("comments")}
        if "approved" not in comment_columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE comments ADD COLUMN approved BOOLEAN DEFAULT 1"))
                connection.execute(text("UPDATE comments SET approved = 1 WHERE approved IS NULL"))
        if "parent_id" not in comment_columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE comments ADD COLUMN parent_id INTEGER"))
