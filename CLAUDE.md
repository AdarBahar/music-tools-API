# Music Tools API

A FastAPI service. It converts YouTube videos to audio files and separates audio files into stems with Demucs.

## Commands

```bash
pip install -r requirements-core.txt pytest httpx   # the same install as CI
python main.py                                      # run the API on http://localhost:8000
python -m pytest -q                                 # all tests (they use a fake Demucs)
docker compose up                                   # API :8001, Redis :6380, Nginx :80 and :443
```

- Add `requirements-audio.txt` for a real Demucs run. It installs torch and Demucs.
- CI runs `python -m pytest -q` on Python 3.12 for each push and pull request.

## Layout

- `main.py`: the app, the middleware, `/health` and `/metrics`.
- `app/api/routes/`: `youtube.py`, `stems.py`, `downloads.py`.
- `app/services/`: `youtube_service.py` (yt-dlp) and `stem_service.py` (Demucs in a subprocess).
- `app/core/`: `config.py`, `auth.py`, `rate_limit.py`, `upload_validation.py`, `memory_management.py`, `filenames.py`, `metrics.py`, `cleanup.py`.
- `app/models/`: the Pydantic request and response models.
- `tests/`: the pytest suite. `tests/conftest.py` sets the environment before the app imports.
- `docs/`: old reports. `.codeagent/current/known_issues.md` lists the open problems.

## Rules for the code

- **Blocking work:** never block the event loop. Use `run_in_threadpool` or `asyncio.to_thread` for downloads, ffmpeg and Demucs.
- **Rate limits:** use the shared limiter in `app/core/rate_limit.py`. Put the route decorator on top and `@limit(...)` below it.
- **Client address:** `get_client_ip` trusts `X-Forwarded-For` only from `TRUSTED_PROXIES`. Do not widen this list to a large range.
- **File names:** the file system limit is 255 bytes, not characters. Use `truncate_utf8` in `app/core/filenames.py`. YouTube files are `<file_id> - <title>.<ext>`.
- **Paths from users:** sanitize every name that comes from a user. A path must stay inside its job directory.
- **Errors:** do not send Demucs output or server paths to the client. Log them. The route maps errors to 500, 503 (with `Retry-After`) and 507.
- **Secrets:** compare keys with `hmac.compare_digest`. `/metrics` needs an API key. `/health` shows details only with a valid key.
- **Settings:** add each new setting to `app/core/config.py` and to `.env.example`. Never write a secret value in a file.
- **Pydantic:** use the V2 style (`field_validator`, `model_validator`, `SettingsConfigDict`).

## Tests

- Add a test for each bug fix. Tests must not need Demucs, a GPU or the network.
- A real Demucs run is a manual test. Do it on the server after a change to the Demucs call or to Docker.

## Git and docs

- Make a branch and a pull request for each change. Do not commit to `main`.
- Update `CHANGELOG.md` for each change that a user can see.
- Write docs and commit messages in ASD-STE100 Simplified Technical English.
