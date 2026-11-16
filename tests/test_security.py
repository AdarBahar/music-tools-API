import pytest

from app.core.config import Settings, settings


def test_static_mount_is_gone(client, out_dir):
    (out_dir / "My Song.mp3").write_bytes(b"x")
    assert client.get("/static/My%20Song.mp3").status_code == 404


def test_api_needs_a_key(client, auth):
    assert client.get("/api/v1/formats").status_code == 401
    assert client.get("/api/v1/formats", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/api/v1/formats", headers=auth).status_code == 200


def test_metrics_need_a_key(client, auth):
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers=auth).status_code == 200


def test_health_hides_details_without_key(client, auth):
    public = client.get("/health").json()
    for check in public["checks"].values():
        assert set(check) == {"status"}
    private = client.get("/health", headers=auth).json()
    assert "secret" not in str(private)  # Redis password is hidden
    assert "***@redis.invalid" in private["checks"]["redis"]["url"]


def test_metric_labels_use_route_templates(client, auth):
    import uuid
    for _ in range(10):
        client.get(f"/api/v1/download/{uuid.uuid4()}", headers=auth)
    text = client.get("/metrics", headers=auth).text
    assert 'endpoint="/download/{file_id}"' in text
    import re
    uuid_pattern = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
    series = [l for l in text.splitlines() if l.startswith("api_requests_total{")]
    assert series
    assert not [l for l in series if uuid_pattern.search(l)]


def test_rate_limit_applies(client, auth):
    codes = [client.get("/api/v1/models", headers=auth).status_code for _ in range(70)]
    assert codes.count(200) == 60
    assert codes.count(429) == 10


def test_size_and_redis_settings_follow_environment(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "10")
    monkeypatch.setenv("REDIS_URL", "redis://other:6379/5")
    monkeypatch.delenv("RATE_LIMIT_STORAGE_URI")
    s = Settings()
    assert s.MAX_FILE_SIZE_BYTES == 10 * 1024 * 1024
    assert s.CELERY_BROKER_URL == s.CELERY_RESULT_BACKEND == s.RATE_LIMIT_STORAGE_URI == "redis://other:6379/5"


def test_explicit_limiter_uri_wins():
    assert settings.RATE_LIMIT_STORAGE_URI == "memory://"
