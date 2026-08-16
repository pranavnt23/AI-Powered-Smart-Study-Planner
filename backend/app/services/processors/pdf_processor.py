import os
import tempfile
from pathlib import Path
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from app.services.processors.image_processor import ImageProcessor


class PDFProcessor:
    """
    Processor for handling PDF files, extracting digital text page-by-page,
    and dynamically falling back to Tesseract OCR for scanned/image-only pages.
    """

    @staticmethod
    def extract_text(file_path: str) -> dict:
        try:
            reader = PdfReader(file_path)
            extracted_lines = []
            pages_data = []

            # Determine local poppler path for PDF to image conversion
            poppler_path = None
            potential_poppler_paths = [
                r"C:\Users\prana\.gemini\antigravity-ide\scratch\AI Invoice Processing\bin\poppler-24.08.0\Library\bin",
                r"C:\Users\prana\.gemini\antigravity\scratch\AI Invoice Processing\bin\poppler-24.08.0\Library\bin",
            ]
            for p in potential_poppler_paths:
                if Path(p).exists():
                    poppler_path = p
                    break

            # Loop page-by-page for hybrid extraction
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                page_text = text.strip()

                # If standard digital extraction is empty or very short, fall back to OCR
                if len(page_text) < 10:
                    # Convert only this page to an image
                    images = convert_from_path(
                        file_path,
                        first_page=page_num,
                        last_page=page_num,
                        poppler_path=poppler_path,
                    )
                    if images:
                        page_image = images[0]

                        # Save temporarily to run through the standard ImageProcessor
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                            temp_img_name = temp_img.name

                        try:
                            page_image.save(temp_img_name, "PNG")

                            # Extract text using ImageProcessor (which runs preprocessing + Tesseract OCR)
                            ocr_result = ImageProcessor.extract_text(temp_img_name)
                            if ocr_result["status"]:
                                page_text = ocr_result["content"]
                            else:
                                page_text = ""
                        finally:
                            # Clean up temporary page image file
                            if os.path.exists(temp_img_name):
                                os.unlink(temp_img_name)

                # Process extracted page lines
                page_lines = []
                for line in page_text.splitlines():
                    cleaned = line.strip()
                    if cleaned:
                        page_lines.append(cleaned)
                        extracted_lines.append(cleaned)

                pages_data.append({
                    "page_number": page_num,
                    "text": "\n".join(page_lines)
                })

            extracted_text = "\n".join(extracted_lines)

            return {
                "status": True,
                "file_type": "pdf",
                "file_name": Path(file_path).name,
                "content": extracted_text,
                "pages": pages_data
            }

        except Exception as error:
            return {
                "status": False,
                "file_type": "pdf",
                "file_name": Path(file_path).name,
                "content": "",
                "pages": [],
                "error": str(error),
            }
