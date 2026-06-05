from pathlib import Path

class MarkdownProcessor:
    @staticmethod
    def extract_text(file_path: str) -> dict:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                extracted_text = file.read()

            return {
                "status": True,
                "file_type": "markdown",
                "file_name": Path(file_path).name,
                "content": extracted_text,
            }

        except Exception as error:
            return {
                "status": False,
                "file_type": "markdown",
                "file_name": Path(file_path).name,
                "content": "",
                "error": str(error),
            }