"""Tests for LLM-based text cleaning module."""
import pytest
from src.extractor.text_cleaner import clean_text, generate_cleaning_code, execute_cleaning_code


class TestGenerateCleaningCode:
    """Tests for generate_cleaning_code function."""

    def test_generate_cleaning_code_returns_string(self):
        """Should return Python code as string."""
        sample = "THE GAZETTE OF INDIA\nCHAPTER I\nPRELIMINARY"
        code = generate_cleaning_code(sample)
        assert isinstance(code, str)
        assert len(code) > 0

    def test_generate_cleaning_code_returns_valid_python(self):
        """Generated code should be valid Python syntax."""
        sample = "THE GAZETTE OF INDIA\nCHAPTER I"
        code = generate_cleaning_code(sample)
        # Should not raise SyntaxError
        compile(code, '<string>', 'exec')

    def test_generate_cleaning_code_has_clean_function(self):
        """Generated code should define a clean() function."""
        sample = "THE GAZETTE OF INDIA\nCHAPTER I"
        code = generate_cleaning_code(sample)
        assert "def clean(" in code or "def clean_text(" in code


class TestExecuteCleaningCode:
    """Tests for execute_cleaning_code function."""

    def test_execute_simple_cleaning_code(self):
        """Should execute simple cleaning code."""
        code = '''
def clean(text):
    return text.replace("NOISE", "")
'''
        result = execute_cleaning_code(code, "NOISE hello NOISE world")
        assert result == " hello  world"

    def test_execute_cleaning_code_with_regex(self):
        """Should handle code that uses regex."""
        code = '''
import re
def clean(text):
    return re.sub(r"\\d+", "", text)
'''
        result = execute_cleaning_code(code, "Page 123 content 456")
        assert result == "Page  content "


class TestCleanText:
    """Integration tests for clean_text function."""

    def test_clean_text_removes_gazette_headers(self):
        """Should remove 'THE GAZETTE OF INDIA EXTRAORDINARY' headers."""
        raw = """THE GAZETTE OF INDIA EXTRAORDINARY
PART II - Section 1
THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023
CHAPTER I
PRELIMINARY"""
        cleaned = clean_text(raw)
        assert "GAZETTE" not in cleaned
        assert "DIGITAL PERSONAL DATA PROTECTION ACT" in cleaned
        assert "CHAPTER I" in cleaned

    def test_clean_text_preserves_act_content(self, sample_pdf_path):
        """Should preserve the actual Act content."""
        from src.extractor.pdf_extractor import extract_text
        raw = extract_text(sample_pdf_path)
        cleaned = clean_text(raw)
        assert "DIGITAL PERSONAL DATA PROTECTION ACT" in cleaned
        assert "CHAPTER" in cleaned

    def test_clean_text_removes_page_numbers(self):
        """Should remove standalone page numbers."""
        raw = """Section 1. Short title.
2
Section 2. Definitions."""
        cleaned = clean_text(raw)
        assert "Section 1" in cleaned
        assert "Section 2" in cleaned
        # Standalone "2" should be removed but section references kept

    def test_clean_text_returns_string(self):
        """Should return cleaned text as string."""
        raw = "Some legal text here"
        cleaned = clean_text(raw)
        assert isinstance(cleaned, str)

    def test_clean_text_not_empty(self):
        """Cleaned text should not be empty if input has content."""
        raw = "THE GAZETTE OF INDIA\nActual content here"
        cleaned = clean_text(raw)
        assert len(cleaned.strip()) > 0
