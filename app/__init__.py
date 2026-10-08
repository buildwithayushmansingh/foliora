import os

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from config import DevConfig, ProdConfig
from app.db import init_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_TEMPLATES_DIR = os.path.join(BASE_DIR, "portfolio_templates")


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    if config_object is None:
        config_object = ProdConfig if os.getenv("FLASK_ENV") == "production" else DevConfig
    app.config.from_object(config_object)

    app.config.setdefault("DATABASE_PATH", os.path.join(app.instance_path, "foliora.db"))
    init_db(app)

    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        FileSystemLoader(PORTFOLIO_TEMPLATES_DIR),
    ])

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_site():
        c = app.config
        return {
            "site": {
                "name": c["STARTUP_NAME"],
                "email": c["CONTACT_EMAIL"],
                "github": c["GITHUB_URL"],
                "linkedin": c["LINKEDIN_URL"],
            }
        }

    @app.context_processor
    def inject_current_user():
        from flask import session
        from app.db import get_user_by_id
        user_id = session.get("user_id")
        return {"current_user": get_user_by_id(user_id) if user_id else None}

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    return app