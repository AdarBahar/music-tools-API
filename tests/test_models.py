import pytest
from pydantic import ValidationError

from app.models.requests import StemSeparationRequest, YouTubeToMP3Request


def test_youtube_request_accepts_known_hosts():
    for url in ("https://www.youtube.com/watch?v=abc", "https://youtu.be/abc",
                "https://music.youtube.com/watch?v=abc"):
        assert YouTubeToMP3Request(url=url).audio_format


@pytest.mark.parametrize("url", ["https://evil.example/watch?v=abc",
                                 "https://youtube.com.evil.example/watch?v=abc"])
def test_youtube_request_rejects_other_hosts(url):
    with pytest.raises(ValidationError):
        YouTubeToMP3Request(url=url)


def test_youtube_request_rejects_unknown_audio_format():
    with pytest.raises(ValidationError):
        YouTubeToMP3Request(url="https://youtu.be/abc", audio_format="exe")


def test_stem_request_defaults_to_all_stems():
    assert StemSeparationRequest().stems is None


def test_stem_request_accepts_valid_stems():
    assert StemSeparationRequest(stems=["vocals", "drums"]).stems == ["vocals", "drums"]


@pytest.mark.parametrize("field,value", [("stems", ["guitar"]),
                                         ("model", "no_such_model"),
                                         ("output_format", "exe")])
def test_stem_request_rejects_bad_values(field, value):
    with pytest.raises(ValidationError):
        StemSeparationRequest(**{field: value})
