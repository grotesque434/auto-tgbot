import asyncio
import os


async def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Merge video and audio tracks into a single file."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    await _run(cmd)
    return output_path


async def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> str:
    """Burn SRT subtitles into video."""
    # Subtitle style: white text, black outline, bottom center
    subtitle_filter = (
        f"subtitles={srt_path}:force_style="
        "'FontName=Arial,FontSize=18,PrimaryColour=&HFFFFFF&,"
        "OutlineColour=&H000000&,Outline=2,Alignment=2,MarginV=30'"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        output_path,
    ]
    await _run(cmd)
    return output_path


async def images_to_video(image_paths: list[str], audio_path: str, output_path: str, fps: int = 1) -> str:
    """Create a slideshow video from images with audio."""
    # Write image list file for ffmpeg
    list_file = output_path + "_list.txt"
    with open(list_file, "w") as f:
        for img in image_paths:
            f.write(f"file '{os.path.abspath(img)}'\n")
            f.write(f"duration {1 / fps}\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    await _run(cmd)
    os.remove(list_file)
    return output_path


async def _run(cmd: list[str]):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {stderr.decode()}")
