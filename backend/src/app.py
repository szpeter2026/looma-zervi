"""
Flask application factory.
Registers all blueprints, middleware, and error handlers.
"""
from flask import Flask, jsonify
from flask_cors import CORS

from src.config import Config, _refresh_config


def create_app(env="development"):
    app = Flask(__name__)
    _refresh_config()  # re-read env vars so per-test overrides are picked up
    app.config.from_object(Config)

    # CORS
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    # --- Register blueprints ---
    from src.api.routes.auth_routes import auth_bp
    from src.api.routes.game_routes import game_bp
    from src.api.routes.enterprise_routes import enterprise_bp
    from src.api.routes.ask_routes import ask_bp
    from src.api.routes.jobs_routes import jobs_bp
    from src.api.routes.resume_routes import resume_bp
    from src.api.routes.reports_routes import reports_bp
    from src.api.routes.referral_routes import referral_bp
    from src.api.routes.quota_routes import quota_bp
    from src.api.routes.poetry_routes import poetry_bp

    app.register_blueprint(auth_bp, url_prefix="/v1/auth")
    app.register_blueprint(game_bp, url_prefix="/v1/game")
    app.register_blueprint(enterprise_bp, url_prefix="/v1/enterprise")
    app.register_blueprint(ask_bp, url_prefix="/v1")
    app.register_blueprint(jobs_bp, url_prefix="/v1/jobs")
    app.register_blueprint(resume_bp, url_prefix="/v1/resume")
    app.register_blueprint(reports_bp, url_prefix="/v1/reports")
    app.register_blueprint(referral_bp, url_prefix="/v1/referral")
    app.register_blueprint(quota_bp, url_prefix="/v1")
    app.register_blueprint(poetry_bp, url_prefix="/v1/poetry")

    # --- Health check ---
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(status="ok", service="looma-backend")

    # --- Root: API info (so visiting localhost:5200 in browser is helpful) ---
    @app.route("/", methods=["GET"])
    def api_info():
        return jsonify(
            service="looma-backend",
            status="ok",
            version="v1",
            endpoints={
                "auth": [
                    "POST /v1/auth/register",
                    "POST /v1/auth/login",
                    "POST /v1/auth/wechat",
                    "POST /v1/auth/bind",
                    "GET  /v1/auth/profile",
                    "POST /v1/auth/refresh",
                    "POST /v1/auth/bridge",
                ],
                "game": [
                    "GET  /v1/game/profile",
                    "POST /v1/game/profile-sync",
                    "POST /v1/game/mission-complete",
                    "POST /v1/game/fleet/create",
                    "POST /v1/game/fleet/join",
                    "GET  /v1/game/fleet/mine",
                    "POST /v1/game/fleet/leave",
                ],
                "ask": ["POST /v1/ask", "POST /v1/feedback/rate", "GET  /v1/feedback/last-query"],
                "quota": ["GET /v1/quota"],
                "jobs": ["POST /v1/jobs/match", "GET /v1/jobs/list"],
                "resume": ["POST /v1/resume/parse", "POST /v1/resume/upload"],
                "reports": ["POST /v1/reports/generate", "GET /v1/reports/list"],
                "referral": ["POST /v1/referral/create", "POST /v1/referral/use", "GET /v1/referral/my-codes"],
                "enterprise": [
                    "POST /v1/enterprise/create",
                    "POST /v1/enterprise/join",
                    "GET  /v1/enterprise/profile",
                    "GET  /v1/enterprise/candidates",
                    "POST /v1/enterprise/candidates/add",
                ],
            },
        )

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="not_found", message=str(e)), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="server_error", message=str(e)), 500

    # --- Initialize database on first request ---
    from src.db.manager import DatabaseManager

    @app.before_request
    def init_db():
        if not getattr(app, "_db_initialized", False):
            db = DatabaseManager(app.config["DATABASE_PATH"])
            db.init_schema()
            app._db = db
            app._db_initialized = True

    return app
