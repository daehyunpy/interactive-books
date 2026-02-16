import re

from interactive_books.domain.chunk_data import ChunkData
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import TextChunker as TextChunkerPort

DEFAULT_MAX_TOKENS = 500
DEFAULT_OVERLAP_TOKENS = 100

SEPARATORS = ("\n\n", "\n", ". ", " ")


class TextChunker(TextChunkerPort):
    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    ) -> None:
        self._max_tokens = max_tokens
        self._overlap_tokens = overlap_tokens

    def chunk(self, pages: list[PageContent]) -> list[ChunkData]:
        non_empty = [p for p in pages if p.text.strip()]
        if not non_empty:
            return []

        word_page_pairs = self._build_word_page_pairs(non_empty)
        if not word_page_pairs:
            return []

        full_text = " ".join(w for w, _ in word_page_pairs)
        segments = self._recursive_split(full_text, SEPARATORS)

        return self._assemble_chunks(segments, word_page_pairs)

    def _build_word_page_pairs(self, pages: list[PageContent]) -> list[tuple[str, int]]:
        return [
            (word, page.page_number) for page in pages for word in page.text.split()
        ]

    def _recursive_split(self, text: str, separators: tuple[str, ...]) -> list[str]:
        if not separators:
            words = text.split()
            return self._group_words(words)

        sep = separators[0]
        remaining_seps = separators[1:]

        parts = text.split(sep)
        if sep != " ":
            parts = [p + sep if i < len(parts) - 1 else p for i, p in enumerate(parts)]

        result: list[str] = []
        for part in parts:
            stripped = part.strip()
            if not stripped:
                continue
            word_count = len(stripped.split())
            if word_count <= self._max_tokens:
                result.append(stripped)
            else:
                result.extend(self._recursive_split(stripped, remaining_seps))

        return result

    def _group_words(self, words: list[str]) -> list[str]:
        segments: list[str] = []
        for i in range(0, len(words), self._max_tokens):
            segment = " ".join(words[i : i + self._max_tokens])
            if segment.strip():
                segments.append(segment)
        return segments

    def _assemble_chunks(
        self,
        segments: list[str],
        word_page_pairs: list[tuple[str, int]],
    ) -> list[ChunkData]:
        merged = self._merge_segments(segments)

        chunks: list[ChunkData] = []
        word_offset = 0
        overlap_prefix = ""

        for i, segment in enumerate(merged):
            has_overlap = i > 0 and self._overlap_tokens > 0 and overlap_prefix
            if has_overlap:
                content = overlap_prefix + " " + segment
            else:
                content = segment

            chunk_words = segment.split()
            segment_start = self._find_word_offset(
                chunk_words[0], word_page_pairs, word_offset
            )
            segment_end = min(
                segment_start + len(chunk_words) - 1, len(word_page_pairs) - 1
            )

            start_page = word_page_pairs[segment_start][1]
            end_page = word_page_pairs[segment_end][1]

            if has_overlap:
                overlap_word_count = len(overlap_prefix.split())
                overlap_start = max(0, segment_start - overlap_word_count)
                start_page = min(start_page, word_page_pairs[overlap_start][1])

            chunks.append(
                ChunkData(
                    content=content.strip(),
                    start_page=start_page,
                    end_page=end_page,
                    chunk_index=i,
                )
            )

            if self._overlap_tokens > 0 and len(chunk_words) > self._overlap_tokens:
                overlap_prefix = " ".join(chunk_words[-self._overlap_tokens :])
            elif self._overlap_tokens > 0:
                overlap_prefix = segment
            else:
                overlap_prefix = ""

            word_offset = segment_end + 1

        return chunks

    def _merge_segments(self, segments: list[str]) -> list[str]:
        merged: list[str] = []
        current: list[str] = []
        current_count = 0

        for seg in segments:
            seg_count = len(seg.split())
            if current_count + seg_count <= self._max_tokens:
                current.append(seg)
                current_count += seg_count
            else:
                if current:
                    merged.append(" ".join(current))
                current = [seg]
                current_count = seg_count

        if current:
            merged.append(" ".join(current))

        return merged

    def _find_word_offset(
        self, target_word: str, pairs: list[tuple[str, int]], start_from: int
    ) -> int:
        target_clean = re.sub(r"[^\w]", "", target_word.lower())
        for i in range(start_from, len(pairs)):
            pair_clean = re.sub(r"[^\w]", "", pairs[i][0].lower())
            if pair_clean == target_clean or pairs[i][0] == target_word:
                return i
        return min(start_from, len(pairs) - 1)
