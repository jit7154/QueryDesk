import hashlib
from dataclasses import dataclass

from app.services.ingestion.extract import ExtractedDocument


@dataclass
class TextChunk:
    chunk_id: str
    document_name: str
    section_title: str
    page_number: int
    chunk_index: int
    content: str


def compute_chunk_id(doc_name: str, page: int, idx: int, content: str) -> str:
    """Generate deterministic SHA-256 hash for chunk deduplication."""
    payload = f"{doc_name}:{page}:{idx}:{content[:50]}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def recursive_split_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
    separators: list[str] | None = None,
) -> list[str]:
    """Recursively split text using decreasing delimiter granularity with sliding overlap."""
    if separators is None:
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    # Find the largest matching separator
    chosen_sep = ""
    for sep in separators:
        if sep == "" or sep in text:
            chosen_sep = sep
            break

    if chosen_sep != "":
        splits = text.split(chosen_sep)
    else:
        splits = list(text)

    docs: list[str] = []
    current_doc: list[str] = []
    total_len = 0

    if chosen_sep in separators:
        next_separators = separators[separators.index(chosen_sep) + 1 :]
    else:
        next_separators = [""]

    for piece in splits:
        piece_len = len(piece) + (len(chosen_sep) if current_doc else 0)
        if total_len + piece_len <= chunk_size:
            current_doc.append(piece)
            total_len += piece_len
        else:
            if current_doc:
                merged = chosen_sep.join(current_doc).strip()
                if merged:
                    docs.append(merged)
                # Apply sliding overlap window
                overlap_accum: list[str] = []
                overlap_len = 0
                for prev in reversed(current_doc):
                    if overlap_len + len(prev) <= chunk_overlap:
                        overlap_accum.insert(0, prev)
                        overlap_len += len(prev)
                    else:
                        break
                current_doc = overlap_accum
                sep_cost = len(chosen_sep) * max(0, len(current_doc) - 1)
                total_len = sum(len(p) for p in current_doc) + sep_cost

            if len(piece) > chunk_size:
                # Recurse with finer delimiter
                sub_pieces = recursive_split_text(piece, chunk_size, chunk_overlap, next_separators)
                for sp in sub_pieces:
                    docs.append(sp)
            else:
                current_doc.append(piece)
                total_len += len(piece) + (len(chosen_sep) if len(current_doc) > 1 else 0)

    if current_doc:
        merged = chosen_sep.join(current_doc).strip()
        if merged:
            docs.append(merged)

    return docs


def chunk_document(
    doc: ExtractedDocument,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> list[TextChunk]:
    """Chunk extracted document sections while preserving section headings and page metadata."""
    chunks: list[TextChunk] = []
    chunk_counter = 0

    for sec in doc.sections:
        if not sec.text.strip():
            continue

        raw_splits = recursive_split_text(
            text=sec.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for split in raw_splits:
            clean_split = split.strip()
            if not clean_split:
                continue

            cid = compute_chunk_id(doc.filename, sec.page_number, chunk_counter, clean_split)
            chunks.append(
                TextChunk(
                    chunk_id=cid,
                    document_name=doc.filename,
                    section_title=sec.heading,
                    page_number=sec.page_number,
                    chunk_index=chunk_counter,
                    content=clean_split,
                )
            )
            chunk_counter += 1

    return chunks
