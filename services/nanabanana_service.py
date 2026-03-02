import aiohttp
from config import config


async def generate_video(prompt: str, output_path: str) -> str | None:
    """
    Generate a video via NanaBanana API.
    Returns path to saved file or None on failure.
    """
    headers = {
        "Authorization": f"Bearer {config.NANABANANA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "duration": 10,
        "resolution": "1080x1920",  # vertical for Shorts/TikTok
        "fps": 30,
    }

    async with aiohttp.ClientSession() as session:
        # Step 1: Submit generation job
        async with session.post(
            f"{config.NANABANANA_BASE_URL}/v1/video/generate",
            json=payload,
            headers=headers,
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"NanaBanana API error: {resp.status} {await resp.text()}")
            data = await resp.json()
            job_id = data.get("job_id")

        if not job_id:
            raise RuntimeError("NanaBanana: no job_id in response")

        # Step 2: Poll for result
        import asyncio
        for _ in range(30):  # max 5 minutes (30 * 10s)
            await asyncio.sleep(10)
            async with session.get(
                f"{config.NANABANANA_BASE_URL}/v1/video/status/{job_id}",
                headers=headers,
            ) as poll_resp:
                poll_data = await poll_resp.json()
                status = poll_data.get("status")
                if status == "completed":
                    video_url = poll_data.get("url")
                    break
                elif status == "failed":
                    raise RuntimeError(f"NanaBanana generation failed: {poll_data}")
        else:
            raise RuntimeError("NanaBanana: generation timeout")

        # Step 3: Download video
        async with session.get(video_url) as dl_resp:
            with open(output_path, "wb") as f:
                f.write(await dl_resp.read())

    return output_path


async def generate_image(prompt: str, output_path: str) -> str:
    """Generate a single image via NanaBanana API."""
    headers = {
        "Authorization": f"Bearer {config.NANABANANA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "width": 1080,
        "height": 1920,
        "num_images": 1,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{config.NANABANANA_BASE_URL}/v1/image/generate",
            json=payload,
            headers=headers,
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"NanaBanana API error: {resp.status} {await resp.text()}")
            data = await resp.json()
            image_url = data["images"][0]["url"]

        async with session.get(image_url) as dl_resp:
            with open(output_path, "wb") as f:
                f.write(await dl_resp.read())

    return output_path
