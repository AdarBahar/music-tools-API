import uuid

from app.api.routes.downloads import _display_name
from app.models.responses import VideoMetadata
from app.services.youtube_service import YouTubeService


def _store(out_dir, meta, fmt="mp3"):
    file_id = str(uuid.uuid4())
    name = YouTubeService()._generate_filename(meta, file_id, fmt)
    (out_dir / name).write_bytes(b"audio")
    return file_id, name


def test_download_finds_file_by_id_and_shows_clean_title(client, auth, out_dir):
    file_id, _ = _store(out_dir, VideoMetadata(title="My Song"))
    r = client.get(f"/api/v1/download/{file_id}", headers=auth)
    assert r.status_code == 200
    assert "My%20Song.mp3" in r.headers["content-disposition"]


def test_same_title_does_not_overwrite(client, auth, out_dir):
    a, _ = _store(out_dir, VideoMetadata(title="Same"))
    b, _ = _store(out_dir, VideoMetadata(title="Same"))
    assert client.get(f"/api/v1/download/{a}", headers=auth).status_code == 200
    assert client.get(f"/api/v1/download/{b}", headers=auth).status_code == 200


def test_download_without_title_uses_audio_name(client, auth, out_dir):
    file_id, _ = _store(out_dir, None)
    r = client.get(f"/api/v1/download/{file_id}", headers=auth)
    assert 'filename="audio.mp3"' in r.headers["content-disposition"]


def test_info_route_is_reachable(client, auth, out_dir):
    file_id, _ = _store(out_dir, VideoMetadata(title="Info Song"))
    r = client.get(f"/api/v1/download/{file_id}/info", headers=auth)
    assert r.status_code == 200
    assert r.json()["filename"] == "Info Song.mp3"


def test_stem_file_route_still_works(client, auth, out_dir):
    job = str(uuid.uuid4())
    (out_dir / job).mkdir()
    (out_dir / job / "s - vocals.mp3").write_bytes(b"x")
    assert client.get(f"/api/v1/download/{job}/s - vocals.mp3", headers=auth).status_code == 200


def test_bad_ids_and_names_are_rejected(client, auth):
    assert client.get("/api/v1/download/not-a-uuid", headers=auth).status_code == 400
    job = str(uuid.uuid4())
    assert client.get(f"/api/v1/download/{job}/..%2Fsecret", headers=auth).status_code in (400, 404)


def test_display_name_helper():
    fid = str(uuid.uuid4())
    assert _display_name(f"{fid} - A.mp3", fid) == "A.mp3"
    assert _display_name(f"{fid}.mp3", fid) == "audio.mp3"
    assert _display_name("other.mp3", fid) == "other.mp3"
