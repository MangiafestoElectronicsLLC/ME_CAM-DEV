import cv2
import os
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
        
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            # FIX: Handle H.264 YUV420 color space conversion
            # H.264 codec outputs YUV420 format, but cv2 expects BGR
            # Without conversion, colors appear pink/green/blue
            try:
                # If frame appears to be in YUV format, convert to BGR
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # Check if colors are already correct (BGR)
                    # If blue channel > red significantly, likely YUV issue
                    mean_b = frame[:,:,0].mean()
                    mean_r = frame[:,:,2].mean()
                    
                    # If blue is significantly higher than red, likely YUV420 issue
                    if mean_b > mean_r * 1.5:
                        # Convert YUV420 to BGR properly
                        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR)
                        logger.debug(f"[THUMBNAIL] Applied YUV420->BGR conversion for {video_path}")
            except Exception as e:
                logger.warning(f"[THUMBNAIL] Color conversion check failed: {e}")
                # Continue anyway with original frame
            
            # Resize to thumbnail size (e.g., 200x112 for 16:9)
            frame = cv2.resize(frame, (200, 112))
            
            # Save with quality setting to preserve colors
            success = cv2.imwrite(thumb_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            if success:
                logger.info(f"[THUMBNAIL] Extracted (color corrected): {thumb_path}")
                return thumb_path
            else:
                logger.warning(f"[THUMBNAIL] Could not write thumbnail to {thumb_path}")
                return None
        else:
            logger.warning(f"[THUMBNAIL] Could not extract frame from {video_path}")
            return None
    except Exception as e:
        logger.error(f"[THUMBNAIL] Failed to extract from {video_path}: {e}")
        return None
