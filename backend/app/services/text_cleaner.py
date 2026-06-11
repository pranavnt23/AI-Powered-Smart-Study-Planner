import re


class TextCleaner:
    """
    Service for cleaning extracted document text.
    """

    @staticmethod
    def clean_text(text: str) -> str:

        if not text:
            return ""

        # Replace tabs with spaces
        text = text.replace("\t", " ")

        # Normalize line endings
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Remove multiple spaces
        text = re.sub(r"[ ]+", " ", text)

        # Remove spaces before/after newlines
        text = re.sub(r" *\n *", "\n", text)

        # Reduce multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text