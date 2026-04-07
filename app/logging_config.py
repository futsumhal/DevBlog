import logging
import os
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    log_level_name = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    app.logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Avoid duplicate handlers when app factory is called multiple times.
    app.logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    if not app.debug and not app.testing:
        log_dir = app.config.get("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    app.logger.info("Logging configured. level=%s", log_level_name)
