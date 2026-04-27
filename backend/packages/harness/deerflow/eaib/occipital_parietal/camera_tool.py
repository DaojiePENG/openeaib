"""Camera capture tool for the Occipital-Parietal perception system.

顶叶&枕叶 (Parietal & Occipital Lobes): vision tools.
"""

from __future__ import annotations

import base64
import json
import logging
import tempfile
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("capture_frame")
def capture_frame_tool(
    device_index: int = 0,
    save_path: str = "",
    return_base64: bool = False,
) -> str:
    """Capture a single image frame from a connected camera.

    Requires OpenCV (cv2) to be installed. Falls back gracefully if unavailable.

    Args:
        device_index: Camera device index (0 = first camera, 1 = second, …).
                      Can also be a device path like '/dev/video0'.
        save_path: If provided, saves the image to this path (JPEG).
        return_base64: If True, includes base64-encoded JPEG in the response.

    Returns:
        JSON with image path and optional base64 data.
    """
    try:
        import cv2  # type: ignore[import]
    except ImportError:
        return json.dumps({
            "error": "OpenCV not installed. Run: pip install opencv-python-headless",
            "hint": "After installing, retry the capture.",
        })

    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        return json.dumps({"error": f"Cannot open camera device {device_index}."})

    try:
        ret, frame = cap.read()
        if not ret or frame is None:
            return json.dumps({"error": "Failed to capture frame."})

        # Determine save path
        if save_path:
            out_path = Path(save_path)
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            out_path = Path(tmp.name)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), frame)

        result: dict = {
            "status": "captured",
            "path": str(out_path),
            "width": frame.shape[1],
            "height": frame.shape[0],
            "device_index": device_index,
        }

        if return_base64:
            with open(out_path, "rb") as f:
                result["base64_jpeg"] = base64.b64encode(f.read()).decode("utf-8")

        return json.dumps(result)
    finally:
        cap.release()
