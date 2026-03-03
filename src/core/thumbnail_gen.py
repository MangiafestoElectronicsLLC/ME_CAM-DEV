import os
import shutil
import subprocess
from loguru import logger

def extract_thumbnail(video_path: str, thumb_dir: str, thumb_name: str = None) -> str:
    """Extract first frame from video and save as thumbnail.
    
    FIXED v2.2.3: Proper H.264 YUV420 to BGR color space conversion
    Eliminates pink/green/blue color corruption in motion event thumbnails
    
    Args:
        video_path: Path to video file
        thumb_dir: Directory to save thumbnail
        thumb_name: Optional custom name; defaults to video basename + .jpg
    
    Returns:
        Path to the thumbnail file.
    """
    try:
        os.makedirs(thumb_dir, exist_ok=True)

        if thumb_name is None:
            thumb_name = os.path.basename(video_path) + ".jpg"
        thumb_path = os.path.join(thumb_dir, thumb_name)

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            logger.warning("[THUMBNAIL] ffmpeg not installed; skipping thumbnail extraction")
            return None

        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", video_path,
            "-frames:v", "1",
            "-vf", "scale=200:112",
            "-q:v", "3",
            thumb_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and os.path.exists(thumb_path):
            logger.info(f"[THUMBNAIL] Extracted: {thumb_path}")
            return thumb_path

        stderr_tail = (result.stderr or "").strip().splitlines()[-1:] if result.stderr else []
        logger.warning(f"[THUMBNAIL] ffmpeg extraction failed: {' '.join(stderr_tail) if stderr_tail else 'unknown error'}")
        return None
    except Exception as e:
        logger.error(f"[THUMBNAIL] Failed to extract from {video_path}: {e}")
        return None
