from pathlib import Path
from pptx import Presentation


class PPTProcessor:
    @staticmethod
    def extract_text(file_path: str) -> dict:
        try:
            presentation = Presentation(file_path)
            extracted_lines = []
            pages_data = []

            for slide_num, slide in enumerate(presentation.slides, start=1):
                slide_lines = []

                def append_slide_text(text: str):
                    if not text:
                        return
                    cleaned = text.strip()
                    if cleaned:
                        slide_lines.append(cleaned)
                        extracted_lines.append(cleaned)

                for shape in slide.shapes:
                    if shape.has_table:
                        for row in shape.table.rows:
                            for cell in row.cells:
                                append_slide_text(cell.text)

                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            append_slide_text(paragraph.text)

                if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
                    append_slide_text(slide.notes_slide.notes_text_frame.text)

                pages_data.append({
                    "page_number": slide_num,
                    "text": "\n".join(slide_lines)
                })

            extracted_text = "\n".join(extracted_lines)

            return {
                "status": True,
                "file_type": "pptx",
                "file_name": Path(file_path).name,
                "content": extracted_text,
                "pages": pages_data
            }

        except Exception as error:
            return {
                "status": False,
                "file_type": "pptx",
                "file_name": Path(file_path).name,
                "content": "",
                "pages": [],
                "error": str(error),
            }
