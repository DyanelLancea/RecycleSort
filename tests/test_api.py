from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.auth import rate_limit
from app.db.models import Base, get_db
from app.main import app
from app.ml.service import InferenceResult
from app.upload import routes as upload_routes


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    def fake_infer(_image_bytes: bytes, _filename: str = "") -> InferenceResult:
        return InferenceResult(
            predicted_class="metal",
            confidence=0.98,
            is_recyclable=True,
            recyclable_status="yes",
            bin_message="Rinse it out and place it in the blue recycling bin.",
            fun_fact="Recycling aluminium saves energy.",
            model_loaded=True,
        )

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    monkeypatch.setattr(upload_routes, "infer", fake_infer)
    rate_limit._attempts.clear()

    with TestClient(app) as test_client:
        yield test_client

    engine.dispose()


def make_jpeg() -> bytes:
    image = Image.new("RGB", (16, 16), color="silver")
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def create_user_and_token(client: TestClient) -> str:
    payload = {"email": "student@example.com", "password": "RecycleSort2026!"}
    registration = client.post("/api/auth/register", json=payload)
    assert registration.status_code == 201

    login = client.post("/api/auth/login", json=payload)
    assert login.status_code == 200
    return login.json()["access_token"]


def test_register_login_upload_awards_points(client: TestClient) -> None:
    token = create_user_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    upload_response = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("can.jpg", make_jpeg(), "image/jpeg")},
    )

    assert upload_response.status_code == 200
    assert upload_response.json()["predicted_class"] == "metal"
    assert upload_response.json()["points_awarded"] == 5
    assert upload_response.json()["total_points"] == 5
    assert client.get("/api/profile", headers=headers).json()["points"] == 5
    assert client.get("/api/logs/me", headers=headers).json()[0]["predicted_class"] == "metal"


def test_my_logs_returns_full_history(client: TestClient) -> None:
    token = create_user_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(55):
        response = client.post(
            "/api/upload",
            headers=headers,
            files={"file": ("can.jpg", make_jpeg(), "image/jpeg")},
        )
        assert response.status_code == 200

    assert len(client.get("/api/logs/me", headers=headers).json()) == 55


def test_upload_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/upload",
        files={"file": ("can.jpg", make_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 401


def test_upload_rejects_text_renamed_to_jpeg(client: TestClient) -> None:
    token = create_user_and_token(client)

    response = client.post(
        "/api/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fake.jpg", b"not an image", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Corrupted or unreadable image"


def test_upload_rejects_file_over_five_mib(client: TestClient) -> None:
    token = create_user_and_token(client)

    response = client.post(
        "/api/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("large.jpg", b"x" * (6 * 1024 * 1024), "image/jpeg")},
    )

    assert response.status_code == 400
    assert "File exceeds" in response.json()["detail"]


def test_sixth_wrong_login_is_rate_limited(client: TestClient) -> None:
    responses = [
        client.post(
            "/api/auth/login",
            json={"email": "unknown@example.com", "password": "WrongPassword2026!"},
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses] == [
        401, 401, 401, 401, 401, 429
    ]


def test_admin_logs_without_key_returns_403(client: TestClient) -> None:
    response = client.get("/api/admin/logs")

    assert response.status_code == 403


def test_health_returns_503_when_database_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class UnavailableDatabase:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, OSError("database unavailable"))

    def override_unavailable_db():
        yield UnavailableDatabase()

    monkeypatch.setitem(app.dependency_overrides, get_db, override_unavailable_db)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "unreachable"}


def test_health_returns_ok_when_database_is_available(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "connected"}
