import aiohttp
import aiofiles
from config import config


async def generate_voiceover(text: str, output_path: str) -> str:
    """
    Generate voiceover audio from text using ElevenLabs TTS API.
    Returns path to the saved .mp3 file.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise RuntimeError(f"ElevenLabs API error: {resp.status} {await resp.text()}")
            audio_data = await resp.read()

    async with aiofiles.open(output_path, "wb") as f:
        await f.write(audio_data)

    return output_path
