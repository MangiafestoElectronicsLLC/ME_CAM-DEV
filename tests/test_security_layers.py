from pathlib import Path

import pytest
from flask import Flask, jsonify, session

from src.core import config_manager, user_auth
from src.core.security import APIAuth, CSRF, InputValidator, RateLimiter, SecurityAudit, SecurityHeaders, rate_limit, require_https
from src.core.security_middleware import SecurityMiddleware, hash_password, secure_filename, verify_password


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY="test-secret", TESTING=True)
    app.debug = False
    security = SecurityMiddleware(app, enabled=True)
    app.limiter = RateLimiter()

    @app.route("/login", methods=["GET", "POST"])
    def login():
        return jsonify(ok=True)

    @app.route("/secure")
    @require_https
    def secure():
        return jsonify(ok=True)

    @app.route("/limited")
    @rate_limit("/api/auth")
    def limited():
        return jsonify(ok=True)

    @app.route("/protected", methods=["POST"])
    @security.require_auth_and_csrf
    def protected():
        return jsonify(ok=True)

    @app.route("/auth-session")
    def auth_session():
        session["authenticated"] = True
        return jsonify(ok=True)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_input_validator_and_sanitizer():
    assert InputValidator.validate("camera_01", "username")
    assert not InputValidator.validate("bad space", "username")
    assert InputValidator.sanitize("hello\x00world\x01") == "helloworld"


def test_csrf_and_api_auth_helpers():
    token = CSRF.generate_token()
    assert CSRF.verify_token(token, token)
    assert not CSRF.verify_token(token, "different")

    raw_token = APIAuth.generate_token("user-1", "device-1")
    stored_hash = APIAuth.generate_token("stored", "hash")
    stored_hash = __import__("hashlib").sha256(raw_token.encode()).hexdigest()
    assert APIAuth.verify_token(raw_token, stored_hash)
    assert not APIAuth.verify_token("wrong", stored_hash)


def test_password_helpers_and_filename_sanitization():
    hashed = hash_password("StrongPass123!")
    assert hashed != "StrongPass123!"
    assert verify_password("StrongPass123!", hashed)
    assert not verify_password("wrong", hashed)
    assert secure_filename("../../unsafe<>name.txt") == "unsafename.txt"


def test_security_headers_are_added(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers


def test_csrf_token_is_created_for_session(client):
    client.get("/login")
    with client.session_transaction() as session_state:
        assert session_state.get("csrf_token")


def test_require_auth_and_csrf_blocks_missing_token(client):
    client.get("/auth-session")
    response = client.post("/protected")
    assert response.status_code == 403


def test_require_auth_and_csrf_accepts_valid_token(client):
    client.get("/auth-session")
    client.get("/login")
    with client.session_transaction() as session_state:
        csrf_token = session_state["csrf_token"]
    response = client.post("/protected", data={"csrf_token": csrf_token})
    assert response.status_code == 200


def test_require_https_blocks_plain_http(client):
    response = client.get("/secure")
    assert response.status_code == 403

    proxied = client.get("/secure", headers={"X-Forwarded-Proto": "https"})
    assert proxied.status_code == 200


def test_route_rate_limit_triggers_429(client):
    for _ in range(5):
        response = client.get("/limited")
        assert response.status_code == 200

    blocked = client.get("/limited")
    assert blocked.status_code == 429


def test_login_rate_limit_triggers_429(client):
    for _ in range(10):
        response = client.post("/login")
        assert response.status_code == 200

    blocked = client.post("/login")
    assert blocked.status_code == 429


def test_password_strength_feedback():
    assert SecurityAudit.check_password_strength("StrongPass123!")[0] is True
    assert SecurityAudit.check_password_strength("weak")[0] is False


def test_security_headers_helper_object():
    app = Flask(__name__)
    response = app.make_response(("ok", 200))
    updated = SecurityHeaders.apply_headers(response)
    assert updated.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in updated.headers


def test_enrollment_key_rotation(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    default_config = config_dir / "config_default.json"
    default_config.write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_manager, "CONFIG_PATH", str(config_dir / "config.json"))
    monkeypatch.setattr(config_manager, "DEFAULT_CONFIG_PATH", str(default_config))
    monkeypatch.setattr(config_manager, "_config_cache", None)

    first_key = user_auth.get_enrollment_key()
    assert user_auth.verify_enrollment_key(first_key)

    rotated_key = user_auth.rotate_enrollment_key("test")
    assert rotated_key != first_key
    assert user_auth.verify_enrollment_key(rotated_key)
    assert not user_auth.verify_enrollment_key(first_key)
