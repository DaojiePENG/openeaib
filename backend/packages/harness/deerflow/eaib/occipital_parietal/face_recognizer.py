"""Face recognition module for the Occipital-Parietal perception system.

顶叶&枕叶 (Parietal & Occipital Lobes): opt-in face recognition for user identity.

Backends (in preference order):
1. face_recognition (dlib-based) — best accuracy
2. opencv haar cascades — fallback, no pip extras needed

Face database stored at: <eaib_dir>/face_db/ as PNG files named <user_id>.png
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_face_db_path() -> Path:
    try:
        from deerflow.config.eaib_config import get_eaib_config

        return Path(get_eaib_config().resolve_face_db_path())
    except Exception:
        return Path.home() / ".local" / "share" / "eaib" / "face_db"


class FaceRecognizer:
    """Identifies users from camera frames.

    Features:
    - Enroll new faces from a captured frame
    - Recognise a face in a frame and return user_id
    - List enrolled users
    - Delete a user's face record
    """

    def __init__(self) -> None:
        self._db_path = _get_face_db_path()
        self._db_path.mkdir(parents=True, exist_ok=True)
        self._backend: str = self._detect_backend()

    def _detect_backend(self) -> str:
        try:
            import face_recognition as _  # type: ignore[import]  # noqa: F401

            return "face_recognition"
        except ImportError:
            pass
        try:
            import cv2 as _  # type: ignore[import]  # noqa: F401

            return "opencv"
        except ImportError:
            pass
        return "none"

    def is_available(self) -> bool:
        return self._backend != "none"

    def enroll(self, user_id: str, image_path: str) -> dict[str, Any]:
        """Enroll a user into the face database.

        Args:
            user_id: Unique identifier for the user (e.g. 'alice' or UUID).
            image_path: Path to an image file containing a clear front-facing photo.

        Returns:
            dict with success status and message.
        """
        src = Path(image_path)
        if not src.exists():
            return {"success": False, "message": f"Image file not found: {image_path}"}

        if self._backend == "face_recognition":
            return self._enroll_fr(user_id, src)
        elif self._backend == "opencv":
            return self._enroll_opencv(user_id, src)
        else:
            return {"success": False, "message": "No face recognition backend available."}

    def _enroll_fr(self, user_id: str, src: Path) -> dict[str, Any]:
        import face_recognition as fr  # type: ignore[import]
        import numpy as np

        img = fr.load_image_file(str(src))
        encodings = fr.face_encodings(img)
        if not encodings:
            return {"success": False, "message": "No face detected in image."}

        out = self._db_path / f"{user_id}.npy"
        np.save(str(out), encodings[0])
        return {"success": True, "user_id": user_id, "backend": "face_recognition"}

    def _enroll_opencv(self, user_id: str, src: Path) -> dict[str, Any]:
        dest = self._db_path / f"{user_id}.png"
        shutil.copy(src, dest)
        return {"success": True, "user_id": user_id, "backend": "opencv", "note": "Haar cascade recognition is approximate."}

    def identify(self, image_path: str, tolerance: float = 0.6) -> dict[str, Any]:
        """Identify a face in the given image.

        Args:
            image_path: Path to the image to analyse.
            tolerance: Lower = stricter matching (face_recognition backend only).

        Returns:
            dict with user_id (or 'unknown'), confidence, and backend.
        """
        src = Path(image_path)
        if not src.exists():
            return {"user_id": "unknown", "error": f"Image not found: {image_path}"}

        if self._backend == "face_recognition":
            return self._identify_fr(src, tolerance)
        elif self._backend == "opencv":
            return {"user_id": "unknown", "note": "OpenCV backend cannot identify; enroll with face_recognition backend for identification."}
        else:
            return {"user_id": "unknown", "error": "No face recognition backend available."}

    def _identify_fr(self, src: Path, tolerance: float) -> dict[str, Any]:
        import face_recognition as fr  # type: ignore[import]
        import numpy as np

        img = fr.load_image_file(str(src))
        encodings = fr.face_encodings(img)
        if not encodings:
            return {"user_id": "unknown", "reason": "No face detected"}

        best_match: str | None = None
        best_dist = 1.0
        for npy_file in self._db_path.glob("*.npy"):
            known_enc = np.load(str(npy_file))
            dist = fr.face_distance([known_enc], encodings[0])[0]
            if dist < best_dist:
                best_dist = float(dist)
                best_match = npy_file.stem

        if best_match and best_dist < tolerance:
            return {"user_id": best_match, "distance": best_dist, "backend": "face_recognition"}
        return {"user_id": "unknown", "best_candidate": best_match, "distance": best_dist}

    def list_enrolled(self) -> list[str]:
        npy = [f.stem for f in self._db_path.glob("*.npy")]
        png = [f.stem for f in self._db_path.glob("*.png")]
        return sorted(set(npy + png))

    def delete_user(self, user_id: str) -> bool:
        deleted = False
        for ext in ("npy", "png"):
            p = self._db_path / f"{user_id}.{ext}"
            if p.exists():
                p.unlink()
                deleted = True
        return deleted

    def status(self) -> dict[str, Any]:
        return {
            "backend": self._backend,
            "available": self.is_available(),
            "enrolled_users": self.list_enrolled(),
            "db_path": str(self._db_path),
        }


_instance: FaceRecognizer | None = None


def get_face_recognizer() -> FaceRecognizer:
    global _instance
    if _instance is None:
        _instance = FaceRecognizer()
    return _instance
