import pytest

from app.api.routes.youtube import validate_youtube_url
from app.services import youtube_service

GOOD = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=abc&feature=share",
    "https://www.youtube.com/watch?v=abc&ab_channel=X",
    "https://youtu.be/dQw4w9WgXcQ?si=abc",
    "https://www.youtube.com/shorts/abc123",
]
BAD = [
    "https://evil.example/?x=youtube.com",
    "https://youtube.com.evil.example/watch?v=1",
    "ftp://www.youtube.com/watch?v=1",
    "https://www.youtube.com/watch?v=1&redirect=http://x",
    "https://youtube.com@evil.example/watch?v=1",
    "javascript:alert(1)",
]


@pytest.mark.parametrize("url", GOOD)
def test_valid_links_pass(url):
    assert validate_youtube_url(url)


@pytest.mark.parametrize("url", BAD)
def test_hostile_links_fail(url):
    assert not validate_youtube_url(url)


def test_bad_url_gives_400(client, auth):
    r = client.post("/api/v1/youtube-to-mp3", json={"url": "https://www.youtube.com/watch?v=a&zz=1"}, headers=auth)
    assert r.status_code == 400


def test_fake_host_in_query_is_rejected_by_model(client, auth):
    r = client.post("/api/v1/youtube-to-mp3", json={"url": "https://evil.example/?x=youtube.com"}, headers=auth)
    assert r.status_code == 422


def test_failed_download_gives_502(client, auth, monkeypatch):
    monkeypatch.setattr(youtube_service.YouTubeService, "download_audio",
                        lambda self, **k: {"success": False, "error": "boom"})
    r = client.post("/api/v1/youtube-to-mp3", json={"url": "https://music.youtube.com/watch?v=abc"}, headers=auth)
    assert r.status_code == 502
    assert r.json()["success"] is False and r.json()["error"] == "boom"


def test_cookie_options(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "YOUTUBE_COOKIES_FILE", "")
    monkeypatch.setattr(settings, "YOUTUBE_COOKIES_FROM_BROWSER", "")
    assert youtube_service.build_cookie_opts() == {}
    monkeypatch.setattr(settings, "YOUTUBE_COOKIES_FROM_BROWSER", "firefox")
    assert youtube_service.build_cookie_opts() == {"cookiesfrombrowser": ("firefox", None)}
