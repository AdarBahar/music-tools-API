# Known Issues

This file lists the open problems. The review of 2026-11-16 closed the security, bug and basic performance items. See `CHANGELOG.md` for the fixes.

## Open

### Performance
- **Model reload for each request**: each stem job starts a new Demucs process, so torch and the model weights load again. A resident worker would remove this cost.
- **Two-step MP3 output**: Demucs writes WAV, then ffmpeg converts each stem. The Demucs `--mp3` option can do this in one step. A real Demucs run must verify the output layout first.
- **GPU detection**: there is no automatic GPU detection for Demucs.

### Operations
- **No job queue**: separation and download requests stay open until the work ends. A job queue (HTTP 202 and a status route) is the better design. Redis is used only for rate limit storage. Celery was removed.
- **Memory estimate**: the estimate is file size x 4. It is below the real Demucs need, and the check uses the API process memory, not the Demucs process.
- **Nginx `/downloads/` alias**: `nginx.conf` can serve the output directory without an API key. Check that `/var/www/downloads` does not point to the output directory.
- **Real Demucs test**: the automated tests use a fake Demucs. Run one real separation on the server after each deployment change.

## Upstream dependencies

- **yt-dlp**: YouTube changes can break downloads. Update yt-dlp often.
- **Demucs models**: the first use of a model needs an internet connection to download it.
- **FFmpeg**: format conversion needs a system FFmpeg.

## Known behavior

- **Redis**: if Redis is not available, rate limits use memory storage for each process.
- **Old files**: the periodic cleanup removes files older than `FILE_RETENTION_HOURS`. Files live up to `FILE_RETENTION_HOURS` + `CLEANUP_INTERVAL_HOURS`.
