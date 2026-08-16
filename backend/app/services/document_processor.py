from pathlib import Path

from app.services.processors.text_processor import TextProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.markdown_processor import MarkdownProcessor
from app.services.processors.ppt_processor import PPTProcessor
from app.services.processors.pdf_processor import PDFProcessor
from app.services.text_cleaner import TextCleaner
from app.services.chunk_services import ChunkService
from app.services.processors.image_processor import ImageProcessor


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
        ".md": MarkdownProcessor,
        ".png": ImageProcessor,
        ".jpg": ImageProcessor,
        ".jpeg": ImageProcessor,
        ".bmp": ImageProcessor,
        ".tiff": ImageProcessor,
        ".tif": ImageProcessor,
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

            if not result.get("status"):
                return result

            chunks = []
            clean_text_parts = []

            # If pages are returned (PDF/PPTX), chunk page-by-page
            if "pages" in result and result["pages"]:
                chunk_index = 0
                for page in result["pages"]:
                    page_text = page.get("text", "")
                    page_num = page.get("page_number", 1)

                    clean_page_text = TextCleaner.clean_text(page_text)
                    if not clean_page_text:
                        continue

                    clean_text_parts.append(clean_page_text)

                    # Chunk text on this page
                    page_chunks = ChunkService.chunk_text(clean_page_text)
                    for pc in page_chunks:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "chunk_text": pc["chunk_text"],
                            "word_count": pc["word_count"],
                            "page_number": page_num
                        })
                        chunk_index += 1

                clean_text = "\n".join(clean_text_parts)
            else:
                # Fallback for text, word doc, markdown, images
                clean_text = TextCleaner.clean_text(result["content"])
                base_chunks = ChunkService.chunk_text(clean_text)
                for pc in base_chunks:
                    chunks.append({
                        "chunk_index": pc["chunk_index"],
                        "chunk_text": pc["chunk_text"],
                        "word_count": pc["word_count"],
                        "page_number": 1
                    })

            return {
                "status": True,
                "message": "Document processed successfully",
                "data": {
                    **result,
                    "clean_text": clean_text,
                    "chunks": chunks
                }
            }

        except Exception as e:
            return {
                "status": False,
                "message": str(e)
            }