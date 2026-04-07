from jinja2 import TemplateNotFound
from flask import jsonify, render_template, request


def _wants_json():
    # Keep fallback simple and safe if templates are missing.
    return request.accept_mimetypes.best == "application/json"


def _render_error(status_code: int, template_name: str, message: str):
    try:
        return render_template(template_name), status_code
    except TemplateNotFound:
        if _wants_json():
            return jsonify({"error": message}), status_code
        return f"{status_code} {message}", status_code


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning("404 Not Found: %s", error)
        return _render_error(404, "errors/404.html", "Not Found")

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("500 Internal Server Error: %s", error)
        return _render_error(500, "errors/500.html", "Internal Server Error")

    @app.errorhandler(Exception)
    def generic_error(error):
        app.logger.exception("Unhandled exception: %s", error)
        return _render_error(500, "errors/500.html", "Internal Server Error")
