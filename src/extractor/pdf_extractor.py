"""PDF text extraction module using PyMuPDF (fitz)."""
from pathlib import Path
from typing import Union
import re
import fitz  # PyMuPDF


# Patterns for romanized Hindi (ASCII gibberish from font mapping)
ROMANIZED_HINDI_PATTERNS = [
    r'\bHkkx\b', r'\bizkf/kdkj\b', r'\blañ\b', r'\bubZ\b', r'\bfnYyh\b',
    r'\b[vkjl][kñ]+[a-z]*\b',  # Common romanized Hindi patterns
    r'\b\w*[ñ]+\w*\b',  # Words with ñ (common in romanized Hindi)
    r'\b\w*[¼½¾]+\w*\b',  # Words with fraction characters
]


def is_romanized_hindi(line: str) -> bool:
    """Check if a line is likely romanized Hindi gibberish."""
    # Skip short lines or lines that look like English
    if len(line.strip()) < 3:
        return False

    # Check for romanized Hindi patterns
    for pattern in ROMANIZED_HINDI_PATTERNS:
        if re.search(pattern, line):
            return True

    # High ratio of special punctuation or unusual character combos
    unusual_chars = len(re.findall(r'[ñ¼½¾\[\]@]', line))
    if unusual_chars > 2:
        return True

    return False


def clean_line(line: str) -> str:
    """Remove non-ASCII (Unicode Hindi) from a line."""
    # Remove Unicode Hindi characters (non-ASCII)
    return re.sub(r'[^\x00-\x7F]+', '', line).strip()


def extract_text(pdf_path: Union[str, Path], remove_hindi: bool = True) -> str:
    """Extract text from PDF file using PyMuPDF.

    Args:
        pdf_path: Path to the PDF file
        remove_hindi: If True, removes Hindi text (both Unicode and romanized)

    Returns:
        Extracted text as string

    Raises:
        FileNotFoundError: If the PDF file does not exist
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(path)
    text_parts = []

    for page in doc:
        page_text = page.get_text()
        if page_text:
            text_parts.append(page_text)

    doc.close()

    full_text = "\n".join(text_parts)

    if remove_hindi:
        # Process line by line
        lines = full_text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip romanized Hindi lines
            if is_romanized_hindi(line):
                continue

            # Remove Unicode Hindi from mixed lines
            cleaned = clean_line(line)

            # Keep non-empty lines
            if cleaned.strip():
                cleaned_lines.append(cleaned)

        full_text = '\n'.join(cleaned_lines)

    return full_text
