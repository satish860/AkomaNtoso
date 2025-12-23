"""PDF text extraction module."""
from pathlib import Path
from typing import Union
import pdfplumber


def extract_text(pdf_path: Union[str, Path]) -> str:
    """Extract text from PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as string

    Raises:
        FileNotFoundError: If the PDF file does not exist
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text_parts = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts)
