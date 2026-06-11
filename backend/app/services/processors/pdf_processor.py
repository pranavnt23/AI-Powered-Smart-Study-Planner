from pathlib import Path
from PyPDF2 import PdfReader


class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> dict:
        try:
            reader = PdfReader(file_path)
            extracted_lines = []

            def append_text(text: str):
                if not text:
                    return
                cleaned = text.strip()
                if cleaned:
                    extracted_lines.append(cleaned)

            for page in reader.pages:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    append_text(line)

            extracted_text = "\n".join(extracted_lines)

            return {
                "status": True,
                "file_type": "pdf",
                "file_name": Path(file_path).name,
                "content": extracted_text,
            }

        except Exception as error:
            return {
                "status": False,
                "file_type": "pdf",
                "file_name": Path(file_path).name,
                "content": "",
                "error": str(error),
            }
