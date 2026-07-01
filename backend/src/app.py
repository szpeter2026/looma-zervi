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
    from src.api.routes.credit_routes import credit_bp
    from src.api.routes.quota_routes import quota_bp
    from src.api.routes.payment_routes import payment_bp
    from src.api.routes.poetry_routes import poetry_bp
    from src.api.routes.narrative_routes import narrative_bp
    from src.api.routes.compliance_routes import compliance_bp
    from src.api.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp, url_prefix="/v1/auth")
    app.register_blueprint(game_bp, url_prefix="/v1/game")
    app.register_blueprint(enterprise_bp, url_prefix="/v1/enterprise")
    app.register_blueprint(ask_bp, url_prefix="/v1")
    app.register_blueprint(jobs_bp, url_prefix="/v1/jobs")
    app.register_blueprint(resume_bp, url_prefix="/v1/resume")
    app.register_blueprint(reports_bp, url_prefix="/v1/reports")
    app.register_blueprint(referral_bp, url_prefix="/v1/referral")
    app.register_blueprint(credit_bp, url_prefix="/v1/credit")
    app.register_blueprint(compliance_bp, url_prefix="/v1/compliance")
    app.register_blueprint(quota_bp, url_prefix="/v1")
    app.register_blueprint(payment_bp, url_prefix="/v1")
    app.register_blueprint(poetry_bp, url_prefix="/v1/poetry")
    app.register_blueprint(analytics_bp, url_prefix="/v1")
    app.register_blueprint(narrative_bp, url_prefix="/v1/narrative")

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
                "jobs": [
                    "GET  /v1/jobs/list",
                    "POST /v1/jobs/upload",
                    "POST /v1/jobs/parse",
                    "POST /v1/jobs/match",
                ],
                "resume": [
                    "POST /v1/resume/parse",
                    "POST /v1/resume/upload",
                    "POST /v1/resume/improve",
                ],
                "reports": ["POST /v1/reports/generate", "GET /v1/reports/list"],
                "payment": [
                    "GET  /v1/payment/plans",
                    "GET  /v1/payment/status",
                    "POST /v1/payment/upgrade",
                ],
                "credit": [
                    "POST /v1/credit/analyze",
                    "POST /v1/credit/check-company",
                ],
                "referral": ["POST /v1/referral/create", "POST /v1/referral/use", "GET /v1/referral/my-codes"],
                "narrative": [
                    "POST /v1/narrative/start",
                    "POST /v1/narrative/event",
                    "POST /v1/narrative/end",
                    "POST /v1/narrative/feedback",
                    "GET  /v1/narrative/stats",
                ],
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

            # Auto-seed beta users in dev mode
            if app.config.get("ENV") == "development":
                try:
                    seeded = db.seed_beta_users()
                    if seeded:
                        app.logger.info(f"[dev] Seeded {len(seeded)} beta users: {seeded}")
                except Exception as e:
                    app.logger.warning(f"[dev] seed_beta_users skipped: {e}")

            app._db = db
            app._db_initialized = True

    return app
