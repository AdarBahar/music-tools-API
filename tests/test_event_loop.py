"""Heavy work must not stop the event loop (a 3 second job gave a 3 second stall)."""

import asyncio
import time

import httpx

import main
from app.services import youtube_service


def test_slow_download_does_not_block_loop(monkeypatch, auth):
    def slow(self, **kwargs):
        time.sleep(1.5)
        return {"success": False, "error": "x"}

    monkeypatch.setattr(youtube_service.YouTubeService, "download_audio", slow)

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as ac:
            gaps = []

            async def ticker():
                last = time.time()
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    now = time.time()
                    gaps.append(now - last)
                    last = now

            tick = asyncio.create_task(ticker())
            await asyncio.sleep(0.05)
            await ac.post("/api/v1/youtube-to-mp3",
                          json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, headers=auth)
            await tick
            return max(gaps)

    assert asyncio.run(run()) < 0.5
