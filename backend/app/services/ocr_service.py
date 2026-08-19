import logging
from typing import Any
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OCRService:
    """PaddleOCR adapter that returns stable application-owned OCR blocks."""
    def __init__(self) -> None:
        self._engine: Any = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            from paddleocr import PaddleOCR
            self._engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        return self._engine

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if min(gray.shape) < 900:
            gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        return cv2.fastNlMeansDenoising(gray, None, 8, 7, 21)

    def recognize(self, image: np.ndarray, page: int) -> dict[str, Any]:
        result = self._get_engine().ocr(self.preprocess(image), cls=True)
        height, width = image.shape[:2]
        blocks: list[dict[str, Any]] = []
        for line in (result[0] or []):
            points, recognition = line
            text, confidence = recognition
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            blocks.append({"text": text, "confidence": float(confidence), "bbox": [min(xs)/width, min(ys)/height, max(xs)/width, max(ys)/height]})
        return {"page": page, "blocks": blocks, "text": "\n".join(x["text"] for x in blocks), "confidence": sum(x["confidence"] for x in blocks) / max(len(blocks), 1)}
