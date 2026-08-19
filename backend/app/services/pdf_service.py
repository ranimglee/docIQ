from pathlib import Path
import fitz
import numpy as np


class PDFService:
    def pages(self, path: Path) -> list[np.ndarray]:
        document = fitz.open(path)
        try:
            images = []
            for page in document:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)
                images.append(image[:, :, ::-1])
            return images
        finally:
            document.close()
