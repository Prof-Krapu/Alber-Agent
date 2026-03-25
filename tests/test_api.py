"""
Tests d'intégration pour l'API Albert IA Agentic.
"""

import pytest
from unittest.mock import patch
import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    """Créer un client de test FastAPI."""
    # Override env pour les tests AVANT l'import
    os.environ["DEBUG"] = "true"
    os.environ["BOT_ACCESS_TOKEN"] = "test-token-12345"
    os.environ["ALBERT_API_KEY"] = "test-key"
    os.environ["RATE_LIMIT_REQUESTS"] = "1000"  # Désactiver rate limit en tests

    # Reset rate limiter singleton pour tenir compte des nouvelles valeurs
    import rate_limiter
    rate_limiter._rate_limiter = None

    from fastapi.testclient import TestClient
    from albert_api import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token-12345"}


class TestStatusEndpoint:
    def test_status_returns_200(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "online"

    def test_status_no_auth_required(self, client):
        """Le endpoint status est public."""
        response = client.get("/api/status")
        assert response.status_code == 200


class TestAuthEndpoints:
    def test_models_requires_auth(self, client):
        response = client.get("/api/models")
        assert response.status_code == 401

    def test_models_with_auth(self, client, auth_headers):
        response = client.get("/api/models", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["models"]) > 0

    def test_tools_requires_auth(self, client):
        response = client.get("/api/tools")
        assert response.status_code == 401

    def test_tools_with_auth(self, client, auth_headers):
        response = client.get("/api/tools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["tools"], list)

    def test_invalid_token_rejected(self, client):
        headers = {"Authorization": "Bearer wrong-token"}
        response = client.get("/api/models", headers=headers)
        assert response.status_code == 401


class TestChatEndpoint:
    def test_chat_requires_auth(self, client):
        response = client.post(
            "/api/chat",
            json={"message": "test", "model": "mistralai/Ministral-3-8B-Instruct-2512"},
        )
        assert response.status_code == 401

    def test_chat_invalid_model_rejected(self, client, auth_headers):
        response = client.post(
            "/api/chat",
            json={"message": "test", "model": "invalid/model"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "inconnu" in data["error"].lower()

    def test_chat_empty_message_rejected(self, client, auth_headers):
        response = client.post(
            "/api/chat",
            json={"message": "", "model": "mistralai/Ministral-3-8B-Instruct-2512"},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error


class TestUIEndpoint:
    def test_root_serves_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
