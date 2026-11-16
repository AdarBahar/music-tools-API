import os
from collections import namedtuple
from pathlib import Path

import pytest

from app.core.config import settings
from app.services import stem_service
from app.services.stem_service import _safe_base_name

WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 64


class FakeDemucs:
    """Replaces subprocess.Popen. Writes four WAV stems like Demucs does."""
    fail = False
    pid = os.getpid()
    returncode = 0
    done = False

    def __init__(self, cmd, **kwargs):
        self.cmd = cmd

    def poll(self):
        return 0 if self.done else None

    def communicate(self, timeout=None):
        self.done = True
        if FakeDemucs.fail:
            self.returncode = 1
            return "", "Traceback /var/www/apitools/secret/path"
        out = Path(self.cmd[self.cmd.index("-o") + 1]) / "htdemucs" / "track"
        out.mkdir(parents=True)
        for name in ("vocals", "drums", "bass", "other"):
            (out / f"{name}.wav").write_bytes(WAV)
        return "", ""

    def kill(self):
        pass


@pytest.fixture(autouse=True)
def fake_demucs(monkeypatch):
    FakeDemucs.fail = False
    monkeypatch.setattr(stem_service.subprocess, "Popen", FakeDemucs)


def _post(client, auth, name, data=WAV, **form):
    return client.post("/api/v1/separate-stems", headers=auth,
                       files={"file": (name, data, "audio/wav")},
                       data={"output_format": "wav", **form})


@pytest.mark.parametrize("name,expected", [
    ("Wait... what.wav", "Wait___ what - vocals.wav"),
    ("AC$DC - Back.wav", "AC_DC - Back - vocals.wav"),
    ("R&B || Soul.wav", "R_B __ Soul - vocals.wav"),
    ("../../escape.wav", "escape - vocals.wav"),
    ("שלום עולם.wav", "שלום עולם - vocals.wav"),
])
def test_hostile_names_are_sanitized_and_stay_inside_job_dir(client, auth, out_dir, name, expected):
    before = {p for p in out_dir.rglob("*") if p.is_file()}
    r = _post(client, auth, name, stems="vocals")
    assert r.status_code == 200, r.text
    new = [p for p in out_dir.rglob("*") if p.is_file() and p not in before]
    assert [p.name for p in new] == [expected]
    assert new[0].parent.parent == out_dir
    assert not list(out_dir.parent.glob("escape*"))


def test_safe_base_name_edge_cases():
    assert _safe_base_name(None) == ""
    assert _safe_base_name("...wav") == ""  # empty base: the service falls back to the stem name
    assert "/" not in _safe_base_name("a/b/c.wav")


def test_failed_separation_gives_500_without_server_paths(client, auth):
    FakeDemucs.fail = True
    r = _post(client, auth, "a.wav")
    assert r.status_code == 500
    assert "apitools" not in r.text and "Traceback" not in r.text


def test_full_disk_gives_507(client, auth, monkeypatch):
    usage = namedtuple("U", "total used free")
    monkeypatch.setattr(stem_service.shutil, "disk_usage", lambda p: usage(10, 10, 0))
    assert _post(client, auth, "a.wav").status_code == 507


def test_busy_server_gives_503_with_retry_after(client, auth, monkeypatch):
    monkeypatch.setattr(settings, "MAX_CONCURRENT_OPERATIONS", 0)
    r = _post(client, auth, "a.wav")
    assert r.status_code == 503
    assert r.headers["retry-after"] == "30"


@pytest.mark.parametrize("data,name,status", [
    (b"MZ" + b"x" * 60, "a.wav", 400),
    (b"xxID3" + b"x" * 60, "a.mp3", 400),
    (b"RIFF" + b"x" * 60, "a.wav", 400),
    (b"ID3" + b"x" * 60, "a.mp3", 200),
    (b"\xff\xf1" + b"x" * 60, "a.aac", 200),
])
def test_upload_signature_check(client, auth, data, name, status):
    r = client.post("/api/v1/separate-stems", headers=auth,
                    files={"file": (name, data, "audio/mpeg")}, data={"output_format": "wav"})
    assert r.status_code == status


def test_long_hebrew_or_cjk_names_fit_the_255_byte_limit(client, auth, out_dir):
    long_name = "歌" * 120 + ".wav"
    r = _post(client, auth, long_name, stems="vocals")
    assert r.status_code == 200, r.text
    names = [p.name for p in out_dir.rglob("*") if p.is_file() and p.name.endswith("歌 - vocals.wav")]
    assert names
    assert all(len(n.encode("utf-8")) <= 255 for n in names)
    assert len(_safe_base_name("ש" * 300).encode("utf-8")) <= 200
