from pathlib import Path
import cv2
import numpy as np
import pytesseract
from PIL import Image


class ImageProcessor:
    """
    Processor for handling image files (PNG, JPG, JPEG, BMP, TIFF)
    and preparing them for text extraction / OCR.
    """

    @staticmethod
    def preprocess_image(file_path: str) -> np.ndarray:
        """
        Applies grayscaling, resizing, noise removal, and Otsu's binarization
        to prepare the image for optimal OCR extraction.
        """
        # Read image using OpenCV
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"OpenCV could not open image file: {file_path}")

        # 1. Grayscale conversion: reduces dimension complexity (3 channels -> 1)
        # Tesseract runs best on high-contrast single-channel luminance data.
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Resizing/Scaling: upscales low-resolution/small images.
        # Characters need to be around 30-40 pixels tall for accurate recognition.
        height, width = gray.shape[:2]
        if width < 2000 or height < 2000:
            scale_factor = 2.0
            processed = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        else:
            processed = gray

        # 3. Noise removal: smooths high-frequency noise and scanner pixelation artifacts.
        # Gaussian blur with a 3x3 kernel is gentle and prevents erasing fine lines.
        blurred = cv2.GaussianBlur(processed, (3, 3), 0)

        # 4. Binarization (Otsu's Thresholding): Segregates foreground text (black) from background (white).
        # Otsu's method automatically calculates the optimal threshold value based on image histogram.
        _, binarized = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binarized

    @staticmethod
    def extract_text(file_path: str) -> dict:
        try:
            path = Path(file_path)

            # Validate file existence
            if not path.exists():
                return {
                    "status": False,
                    "file_type": "image",
                    "file_name": path.name,
                    "content": "",
                    "error": f"File not found: {file_path}",
                }

            # Validate extension compatibility
            supported_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
            ext = path.suffix.lower()
            if ext not in supported_extensions:
                return {
                    "status": False,
                    "file_type": "image",
                    "file_name": path.name,
                    "content": "",
                    "error": f"Unsupported image extension: {ext}",
                }

            # Verify image integrity using Pillow (PIL)
            with Image.open(path) as img:
                img.verify()

            with Image.open(path) as img:
                img.load()

            # Preprocess the image using OpenCV
            preprocessed_mat = ImageProcessor.preprocess_image(str(path))

            # Run pytesseract OCR to extract text
            extracted_text = pytesseract.image_to_string(preprocessed_mat, config="--psm 3")

            return {
                "status": True,
                "file_type": "image",
                "file_name": path.name,
                "content": extracted_text.strip(),
            }

        except Exception as error:
            return {
                "status": False,
                "file_type": "image",
                "file_name": Path(file_path).name,
                "content": "",
                "error": str(error),
            }

