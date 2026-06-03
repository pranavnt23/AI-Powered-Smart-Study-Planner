from pathlib import Path

from app.services.processors.text_processor import TextProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.ppt_processor import PPTProcessor
from app.services.processors.pdf_processor import PDFProcessor

# Future imports
# from app.services.processors.image_processor import ImageProcessor


class DocumentProcessor:

    """
    Central dispatcher for all document processors.
    """

    PROCESSOR_MAP = {
        ".txt": TextProcessor,
        ".docx": DOCXProcessor,
        ".pdf": PDFProcessor,
        ".ppt": PPTProcessor,
        ".pptx": PPTProcessor,

        # Future expandable
        # ".png": ImageProcessor,
        # ".jpg": ImageProcessor,
        # ".jpeg": ImageProcessor,
    }

    @classmethod
    def process_document(cls, file_path: str) -> dict:

        try:
            extension = Path(file_path).suffix.lower()

            # Validate supported extension
            if extension not in cls.PROCESSOR_MAP:
                return {
                    "status": False,
                    "message": f"Unsupported file type: {extension}"
                }

            # Get processor dynamically
            processor = cls.PROCESSOR_MAP[extension]

            # Process file
            result = processor.extract_text(file_path)

            return {
                "status": True,
                "message": "Document processed successfully",
                "data": result
            }

        except Exception as e:
            return {
                "status": False,
                "message": str(e)
            }