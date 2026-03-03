import asyncio
import aiohttp
import aiofiles
from config import config

SORA_API_BASE = "https://api.openai.com/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }


async def generate_video(prompt: str, output_path: str) -> str:
    """
    Generate a video via OpenAI Sora API.
    Submits a generation job, polls for completion, downloads the result.
    Returns path to the saved .mp4 file.
    """
    async with aiohttp.ClientSession() as session:
        # Step 1: Submit generation job
        payload = {
            "model": config.SORA_MODEL,
            "prompt": prompt,
            "size": "1080x1920",   # vertical — YouTube Shorts / TikTok
            "duration": 5,         # seconds (Sora supports 5 or 10)
            "n": 1,
        }
        async with session.post(
            f"{SORA_API_BASE}/video/generations",
            json=payload,
            headers=_headers(),
        ) as resp:
            if resp.status not in (200, 201, 202):
                raise RuntimeError(f"Sora API error {resp.status}: {await resp.text()}")
            data = await resp.json()

        generation_id = data.get("id")
        if not generation_id:
            raise RuntimeError(f"Sora: no generation id in response: {data}")

        # Step 2: Poll for completion
        for _ in range(60):  # max ~10 minutes (60 × 10s)
            await asyncio.sleep(10)
            async with session.get(
                f"{SORA_API_BASE}/video/generations/{generation_id}",
                headers=_headers(),
            ) as poll_resp:
                poll_data = await poll_resp.json()

            status = poll_data.get("status")
            if status == "succeeded":
                video_url = poll_data["data"][0]["url"]
                break
            elif status in ("failed", "cancelled"):
                raise RuntimeError(f"Sora generation {status}: {poll_data}")
        else:
            raise RuntimeError("Sora: generation timeout (10 min)")

        # Step 3: Download video
        async with session.get(video_url) as dl_resp:
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(await dl_resp.read())

    return output_path


async def generate_image(prompt: str, output_path: str) -> str:
    """
    Generate an image via OpenAI Images API (dall-e-3).
    Used as fallback when user chooses 'image' instead of video.
    Returns path to the saved .png file.
    """
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": "1024x1792",   # closest to 9:16 vertical
            "quality": "hd",
            "n": 1,
        }
        async with session.post(
            f"{SORA_API_BASE}/images/generations",
            json=payload,
            headers=_headers(),
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"DALL-E API error {resp.status}: {await resp.text()}")
            data = await resp.json()

        image_url = data["data"][0]["url"]

        async with session.get(image_url) as dl_resp:
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(await dl_resp.read())

    return output_path
