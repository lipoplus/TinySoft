def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_signup(client):
    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_signup_duplicate_email(client):
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "password1"},
    )
    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "password2"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client):
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    assert response.status_code == 200
    assert "session_token" in response.cookies


def test_login_invalid_credentials(client):
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_logout(client):
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    assert "session_token" in login_response.cookies

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200


def test_password_reset_request(client):
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )
    response = client.post(
        "/auth/password-reset-request",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    assert "reset link will be sent" in response.json()["message"]


def test_password_reset_request_nonexistent_email(client):
    response = client.post(
        "/auth/password-reset-request",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    assert "reset link will be sent" in response.json()["message"]


def test_list_sessions(client, db):
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )

    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "secure-password"},
    )

    response = client.get("/auth/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) >= 1


def test_cleanup_expired_sessions(client, db):
    from datetime import datetime, timedelta, timezone

    from platform_db.models import Session as SessionModel
    from platform_db.models import User

    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure-password"},
    )

    users = db.query(User).all()
    if users:
        user = users[0]
        expired_session = SessionModel(
            user_id=user.id,
            token_hash="fake-expired-token",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add(expired_session)
        db.commit()

    response = client.delete("/auth/sessions")
    assert response.status_code == 200
    assert response.json()["deleted_sessions"] >= 0
