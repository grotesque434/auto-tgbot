import asyncio
from faster_whisper import WhisperModel


_model = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        # "base" is a good balance of speed/quality.
        # device="cpu", compute_type="int8" — works on any machine without GPU.
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


async def transcribe_audio(audio_path: str) -> list[dict]:
    """
    Transcribe audio and return segments for subtitle generation.
    Returns list of {"start": float, "end": float, "text": str}
    """
    loop = asyncio.get_event_loop()
    segments, _ = await loop.run_in_executor(
        None,
        lambda: _get_model().transcribe(audio_path, word_timestamps=True),
    )
    return [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in segments
    ]


def segments_to_srt(segments: list[dict]) -> str:
    """Convert segments to SRT subtitle format."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_timecode(seg["start"])
        end = _format_timecode(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    return "\n".join(lines)


def _format_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
