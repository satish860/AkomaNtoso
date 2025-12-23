"""Tests for PDF text extraction module."""
import pytest
from src.extractor.pdf_extractor import extract_text


class TestExtractText:
    """Tests for extract_text function."""

    def test_extract_text_from_valid_pdf(self, sample_pdf_path):
        """Should extract text from DPDP Act PDF."""
        text = extract_text(sample_pdf_path)
        assert "DIGITAL PERSONAL DATA PROTECTION ACT" in text
        assert len(text) > 1000

    def test_extract_text_preserves_structure(self, sample_pdf_path):
        """Section numbers and chapter headings should be intact."""
        text = extract_text(sample_pdf_path)
        assert "CHAPTER I" in text or "CHAPTER" in text
        assert "1." in text  # Section 1

    def test_extract_text_invalid_file_raises(self):
        """Should raise error for non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_text("nonexistent.pdf")

    def test_extract_text_returns_string(self, sample_pdf_path):
        """PDF extractor should return text as string."""
        text = extract_text(sample_pdf_path)
        assert isinstance(text, str)

    def test_extract_text_not_empty(self, sample_pdf_path):
        """Extracted text should not be empty."""
        text = extract_text(sample_pdf_path)
        assert text.strip() != ""
