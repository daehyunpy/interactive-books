from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    content: str
    start_page: int
    end_page: int
    distance: float
