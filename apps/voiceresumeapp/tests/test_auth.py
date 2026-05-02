import pytest


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
