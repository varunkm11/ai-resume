from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from docx import Document


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from PDF, DOCX or TXT without storing the raw file."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        doc = Document(BytesIO(content))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(parts)

    if suffix == ".txt":
        return content.decode("utf-8", errors="ignore")

    raise ValueError("Unsupported file type. Upload PDF, DOCX or TXT.")
