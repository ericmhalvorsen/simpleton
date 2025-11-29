"""Text chunking strategies for RAG pipeline"""

import re


class TextChunker:
    """Split text into chunks for embedding and retrieval"""

    @staticmethod
    def chunk_by_tokens(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
        """
        Split text into chunks by approximate token count
        Uses simple whitespace splitting as token approximation

        Args:
            text: Text to split
            chunk_size: Target size per chunk (in tokens)
            chunk_overlap: Number of tokens to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split into words (approximate tokens)
        words = text.split()

        if not words:
            return []

        chunks = []
        start_idx = 0

        while start_idx < len(words):
            # Get chunk of words
            end_idx = start_idx + chunk_size
            chunk_words = words[start_idx:end_idx]
            chunk = " ".join(chunk_words)

            chunks.append(chunk)

            # Move start position with overlap
            start_idx = end_idx - chunk_overlap

            # Prevent infinite loop if overlap >= chunk_size
            if start_idx <= chunks.__len__() * (chunk_size - chunk_overlap):
                start_idx = end_idx

            # Break if we've processed all words
            if end_idx >= len(words):
                break

        return chunks

    @staticmethod
    def chunk_by_sentences(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
        """
        Split text into chunks by sentences, respecting chunk size

        Args:
            text: Text to split
            chunk_size: Target size per chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split into sentences (simple regex-based)
        sentences = re.split(r"(?<=[.!?])\s+", text)

        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If adding this sentence would exceed chunk_size
            if current_size + sentence_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                # Calculate how many sentences to keep for overlap
                overlap_chunk = []
                overlap_size = 0

                for prev_sentence in reversed(current_chunk):
                    if overlap_size + len(prev_sentence) <= chunk_overlap:
                        overlap_chunk.insert(0, prev_sentence)
                        overlap_size += len(prev_sentence) + 1  # +1 for space
                    else:
                        break

                current_chunk = overlap_chunk
                current_size = overlap_size

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size + 1  # +1 for space

        # Add final chunk if it exists
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    @staticmethod
    def chunk_by_paragraphs(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
        """
        Split text into chunks by paragraphs, respecting chunk size

        Args:
            text: Text to split
            chunk_size: Target size per chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)

            # If single paragraph exceeds chunk_size, split it by sentences
            if paragraph_size > chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph by sentences
                sentence_chunks = TextChunker.chunk_by_sentences(paragraph, chunk_size, chunk_overlap)
                chunks.extend(sentence_chunks)
                continue

            # If adding this paragraph would exceed chunk_size
            if current_size + paragraph_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append("\n\n".join(current_chunk))

                # Start new chunk with overlap
                overlap_chunk = []
                overlap_size = 0

                for prev_paragraph in reversed(current_chunk):
                    if overlap_size + len(prev_paragraph) <= chunk_overlap:
                        overlap_chunk.insert(0, prev_paragraph)
                        overlap_size += len(prev_paragraph) + 2  # +2 for \n\n
                    else:
                        break

                current_chunk = overlap_chunk
                current_size = overlap_size

            # Add paragraph to current chunk
            current_chunk.append(paragraph)
            current_size += paragraph_size + 2  # +2 for \n\n

        # Add final chunk if it exists
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    @staticmethod
    def chunk_recursive(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
        """
        Recursively split text trying different separators
        This is the recommended default method

        Priority order: paragraphs -> sentences -> words -> characters

        Args:
            text: Text to split
            chunk_size: Target size per chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # If text is smaller than chunk_size, return as is
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        # Try splitting by paragraphs first (best preservation of context)
        if "\n\n" in text:
            return TextChunker.chunk_by_paragraphs(text, chunk_size, chunk_overlap)

        # Try splitting by sentences
        if ". " in text or "! " in text or "? " in text:
            return TextChunker.chunk_by_sentences(text, chunk_size, chunk_overlap)

        # Fall back to word-based chunking
        return TextChunker.chunk_by_tokens(text, chunk_size // 4, chunk_overlap // 4)

    @staticmethod
    def chunk_with_metadata(
        text: str, chunk_size: int = 1000, chunk_overlap: int = 200, strategy: str = "recursive"
    ) -> list[dict]:
        """
        Chunk text and return chunks with metadata

        Args:
            text: Text to split
            chunk_size: Target size per chunk
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy ('recursive', 'paragraphs', 'sentences', 'tokens')

        Returns:
            List of dicts with 'content', 'index', 'char_start', 'char_end'
        """
        # Select chunking strategy
        if strategy == "paragraphs":
            chunks = TextChunker.chunk_by_paragraphs(text, chunk_size, chunk_overlap)
        elif strategy == "sentences":
            chunks = TextChunker.chunk_by_sentences(text, chunk_size, chunk_overlap)
        elif strategy == "tokens":
            chunks = TextChunker.chunk_by_tokens(text, chunk_size, chunk_overlap)
        else:  # recursive (default)
            chunks = TextChunker.chunk_recursive(text, chunk_size, chunk_overlap)

        # Add metadata to each chunk
        chunks_with_metadata = []
        char_offset = 0

        for idx, chunk in enumerate(chunks):
            # Find chunk position in original text (approximate)
            chunk_start = text.find(chunk[:50], char_offset) if len(chunk) >= 50 else text.find(chunk, char_offset)
            if chunk_start == -1:
                chunk_start = char_offset

            chunk_end = chunk_start + len(chunk)

            chunks_with_metadata.append(
                {
                    "content": chunk,
                    "index": idx,
                    "char_start": chunk_start,
                    "char_end": chunk_end,
                    "length": len(chunk),
                }
            )

            char_offset = chunk_end

        return chunks_with_metadata
