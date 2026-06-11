import re

class ChunkService:

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ):

        words = text.split()
        chunks = []
        step = chunk_size - overlap

        for index, start in enumerate(
            range(0, len(words), step)
        ):

            chunk_words = words[start:start + chunk_size]

            if not chunk_words:
                continue

            chunks.append({
                "chunk_index": index,
                "chunk_text": " ".join(chunk_words),
                "word_count": len(chunk_words)
            })

        return chunks

    @staticmethod
    def heading_aware_chunk(
        text: str
    ):

        lines = text.splitlines()
        chunks = []
        current_heading = "General"

        current_content = []
        chunk_index = 0

        for line in lines:

            cleaned = line.strip()

            if not cleaned:
                continue

            # Very simple heading detection
            if re.match(r"^(Chapter|Unit|Module)\s+\d+", cleaned, re.I):

                if current_content:

                    chunk_text = "\n".join(current_content)

                    chunks.append({
                        "chunk_index": chunk_index,
                        "heading": current_heading,
                        "chunk_text": chunk_text,
                        "word_count": len(chunk_text.split())
                    })

                    chunk_index += 1

                current_heading = cleaned
                current_content = []

            else:
                current_content.append(cleaned)

        if current_content:

            chunk_text = "\n".join(current_content)

            chunks.append({
                "chunk_index": chunk_index,
                "heading": current_heading,
                "chunk_text": chunk_text,
                "word_count": len(chunk_text.split())
            })

        return chunks