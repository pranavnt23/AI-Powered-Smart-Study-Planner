from pathlib import Path


class TextProcessor:

    @staticmethod
    def extract_text(file_path: str) -> dict:

        try:
            path = Path(file_path)

            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            return {
                "status": True,
                "file_type": "text",
                "file_name": path.name,
                "content": content
            }

        except Exception as e:
            return {
                "status": False,
                "message": str(e)
            }