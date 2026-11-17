from app.services.ingestion.chunker import (
    chunk_document,
    compute_chunk_id,
    recursive_split_text,
)
from app.services.ingestion.extract import ExtractedDocument, ExtractedSection


def test_recursive_split_short_text() -> None:
    """Short text below chunk size should not be divided."""
    text = "Short clause under size limit."
    chunks = recursive_split_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_recursive_split_with_paragraphs() -> None:
    """Paragraph breaks should be prioritized for splitting."""
    para1 = "Paragraph one with detailed background details."
    para2 = "Paragraph two with fulfillment SLA instructions."
    text = f"{para1}\n\n{para2}"
    chunks = recursive_split_text(text, chunk_size=55, chunk_overlap=10)
    assert len(chunks) >= 2
    assert "Paragraph one" in chunks[0]
    assert "Paragraph two" in chunks[1]


def test_recursive_split_overlap() -> None:
    """Consecutive chunks should share overlapping context."""
    text = "First long section. Second long section. Third long section. Fourth long section."
    chunks = recursive_split_text(text, chunk_size=40, chunk_overlap=15)
    assert len(chunks) > 1
    # Check that adjacent chunks have partial overlap
    assert any(word in chunks[1] for word in chunks[0].split())


def test_chunk_document_metadata() -> None:
    """Section headings and page numbers must be preserved across chunks."""
    sections = [
        ExtractedSection(
            heading="Section 7.2: Late Delivery Penalties",
            text="Late delivery fee of 4% per week applies to delayed shipments.",
            page_number=2,
        ),
        ExtractedSection(
            heading="Section 8.0: Quality Control",
            text="Return rate must remain below 1.5% of total units shipped.",
            page_number=3,
        ),
    ]
    doc = ExtractedDocument(
        filename="Test_Contract.pdf",
        file_type="pdf",
        total_pages=3,
        sections=sections,
    )

    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 2
    assert chunks[0].document_name == "Test_Contract.pdf"
    assert chunks[0].section_title == "Section 7.2: Late Delivery Penalties"
    assert chunks[0].page_number == 2
    assert chunks[0].chunk_index == 0
    assert chunks[1].section_title == "Section 8.0: Quality Control"
    assert chunks[1].page_number == 3
    assert chunks[1].chunk_index == 1


def test_deterministic_chunk_id() -> None:
    """Same input arguments must produce identical chunk hashes."""
    id1 = compute_chunk_id("doc.pdf", 1, 0, "Consistent text content")
    id2 = compute_chunk_id("doc.pdf", 1, 0, "Consistent text content")
    id3 = compute_chunk_id("doc.pdf", 1, 1, "Different chunk index")
    assert id1 == id2
    assert id1 != id3
