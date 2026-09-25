import os

from flask import Flask

from config import DevConfig, ProdConfig


def create_app(config_object=None):
    app = Flask(__name__)
    if config_object is None:
        config_object = ProdConfig if os.getenv("FLASK_ENV") == "production" else DevConfig
    app.config.from_object(config_object)

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)
    # Later phases: register catalog, auth, billing, portfolio, admin blueprints here.

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

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    return app
