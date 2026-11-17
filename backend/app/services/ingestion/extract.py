import io
import re
from dataclasses import dataclass

import docx
import pymupdf


@dataclass
class ExtractedSection:
    heading: str
    text: str
    page_number: int


@dataclass
class ExtractedDocument:
    filename: str
    file_type: str
    total_pages: int
    sections: list[ExtractedSection]


SECTION_HEADING_PATTERN = re.compile(
    r"^(?:Section\s+\d+(?:\.\d+)*[:\-\s]+[^\n]+|[A-Z0-9\s]{4,40}:)",
    re.MULTILINE
)


def extract_pdf(file_bytes: bytes, filename: str) -> ExtractedDocument:
    """Extract pages and section hierarchies from a PDF document."""
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    sections: list[ExtractedSection] = []
    total_pages = len(doc)
    current_heading = "General"

    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_num = page_idx + 1
        text = page.get_text("text").strip()
        if not text:
            continue

        # Split page text into candidate blocks or paragraphs
        lines = text.split("\n")
        current_block: list[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Skip header/footer artifacts
            if "RETAILFLOW CORP" in line_str or re.match(r"^Page \d+ of \d+", line_str):
                continue
            if line_str.startswith("Doc ID:"):
                continue

            match = SECTION_HEADING_PATTERN.match(line_str)
            if match or (line_str.startswith("Section ") and ":" in line_str):
                if current_block:
                    sections.append(
                        ExtractedSection(
                            heading=current_heading,
                            text=" ".join(current_block),
                            page_number=page_num,
                        )
                    )
                    current_block = []
                current_heading = line_str
            else:
                current_block.append(line_str)

        if current_block:
            sections.append(
                ExtractedSection(
                    heading=current_heading,
                    text=" ".join(current_block),
                    page_number=page_num,
                )
            )

    doc.close()
    return ExtractedDocument(
        filename=filename,
        file_type="pdf",
        total_pages=total_pages,
        sections=sections,
    )


def extract_docx(file_bytes: bytes, filename: str) -> ExtractedDocument:
    """Extract paragraphs, headings, and page boundaries from a DOCX file."""
    doc = docx.Document(io.BytesIO(file_bytes))
    sections: list[ExtractedSection] = []
    current_heading = "General"
    current_block: list[str] = []
    page_number = 1
    total_pages = 1

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect manual page delimiter indicator
        page_match = re.search(r"--- Page (\d+) of (\d+) ---", text)
        if page_match:
            if current_block:
                sections.append(
                    ExtractedSection(
                        heading=current_heading,
                        text=" ".join(current_block),
                        page_number=page_number,
                    )
                )
                current_block = []
            page_number = int(page_match.group(1))
            total_pages = max(total_pages, int(page_match.group(2)))
            continue

        if para.style and para.style.name.startswith("Heading"):
            if current_block:
                sections.append(
                    ExtractedSection(
                        heading=current_heading,
                        text=" ".join(current_block),
                        page_number=page_number,
                    )
                )
                current_block = []
            current_heading = text
        elif text.startswith("Section ") and ":" in text:
            if current_block:
                sections.append(
                    ExtractedSection(
                        heading=current_heading,
                        text=" ".join(current_block),
                        page_number=page_number,
                    )
                )
                current_block = []
            current_heading = text
        else:
            current_block.append(text)

    if current_block:
        sections.append(
            ExtractedSection(
                heading=current_heading,
                text=" ".join(current_block),
                page_number=page_number,
            )
        )

    return ExtractedDocument(
        filename=filename,
        file_type="docx",
        total_pages=total_pages,
        sections=sections,
    )


def extract_document(file_bytes: bytes, filename: str) -> ExtractedDocument:
    """Route document extraction based on file extension."""
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        return extract_pdf(file_bytes, filename)
    elif lower_name.endswith(".docx"):
        return extract_docx(file_bytes, filename)
    raise ValueError(f"Unsupported file format for {filename}. Only PDF and DOCX are supported.")
