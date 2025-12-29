"""Tests for line-numbered text extraction module."""
import pytest
from src.models import LineInfo
from src.extractor.line_numbered_extractor import (
    extract_with_line_info,
    format_numbered_text,
    get_lines_slice,
    get_content,
    get_page_for_line,
    get_page_range,
)


class TestFormatNumberedText:
    """Tests for format_numbered_text function."""

    def test_empty_list(self):
        """Should return empty string for empty list."""
        result = format_numbered_text([])
        assert result == ""

    def test_single_line(self):
        """Should format single line correctly."""
        lines = [LineInfo(line_num=1, page=1, text="Hello")]
        result = format_numbered_text(lines)
        assert result == "1| Hello"

    def test_multiple_lines(self):
        """Should format multiple lines with aligned numbers."""
        lines = [
            LineInfo(line_num=1, page=1, text="Line one"),
            LineInfo(line_num=2, page=1, text="Line two"),
        ]
        result = format_numbered_text(lines)
        assert result == "1| Line one\n2| Line two"

    def test_number_alignment(self):
        """Should right-align line numbers based on max width."""
        lines = [
            LineInfo(line_num=1, page=1, text="First"),
            LineInfo(line_num=10, page=1, text="Tenth"),
            LineInfo(line_num=100, page=2, text="Hundredth"),
        ]
        result = format_numbered_text(lines)
        expected = "  1| First\n 10| Tenth\n100| Hundredth"
        assert result == expected


class TestGetLinesSlice:
    """Tests for get_lines_slice function."""

    def test_full_range(self):
        """Should return all lines when range covers all."""
        lines = [
            LineInfo(line_num=1, page=1, text="A"),
            LineInfo(line_num=2, page=1, text="B"),
            LineInfo(line_num=3, page=1, text="C"),
        ]
        result = get_lines_slice(lines, 1, 3)
        assert "1| A" in result
        assert "2| B" in result
        assert "3| C" in result

    def test_partial_range(self):
        """Should return only lines in range."""
        lines = [
            LineInfo(line_num=1, page=1, text="A"),
            LineInfo(line_num=2, page=1, text="B"),
            LineInfo(line_num=3, page=1, text="C"),
            LineInfo(line_num=4, page=2, text="D"),
        ]
        result = get_lines_slice(lines, 2, 3)
        assert "1| A" not in result
        assert "2| B" in result
        assert "3| C" in result
        assert "4| D" not in result

    def test_empty_range(self):
        """Should return empty string for non-matching range."""
        lines = [LineInfo(line_num=1, page=1, text="A")]
        result = get_lines_slice(lines, 10, 20)
        assert result == ""


class TestGetContent:
    """Tests for get_content function."""

    def test_extracts_raw_text(self):
        """Should return text without line numbers."""
        lines = [
            LineInfo(line_num=1, page=1, text="Hello"),
            LineInfo(line_num=2, page=1, text="World"),
        ]
        result = get_content(lines, 1, 2)
        assert result == "Hello\nWorld"
        assert "|" not in result  # No line number format

    def test_partial_range(self):
        """Should return only content in range."""
        lines = [
            LineInfo(line_num=1, page=1, text="A"),
            LineInfo(line_num=2, page=1, text="B"),
            LineInfo(line_num=3, page=1, text="C"),
        ]
        result = get_content(lines, 2, 2)
        assert result == "B"


class TestGetPageForLine:
    """Tests for get_page_for_line function."""

    def test_finds_correct_page(self):
        """Should return correct page for line."""
        lines = [
            LineInfo(line_num=1, page=1, text="A"),
            LineInfo(line_num=2, page=1, text="B"),
            LineInfo(line_num=3, page=2, text="C"),
        ]
        assert get_page_for_line(lines, 1) == 1
        assert get_page_for_line(lines, 2) == 1
        assert get_page_for_line(lines, 3) == 2

    def test_missing_line_returns_default(self):
        """Should return 1 for non-existent line."""
        lines = [LineInfo(line_num=1, page=5, text="A")]
        assert get_page_for_line(lines, 99) == 1


class TestGetPageRange:
    """Tests for get_page_range function."""

    def test_same_page(self):
        """Should return same page for start and end."""
        lines = [
            LineInfo(line_num=1, page=3, text="A"),
            LineInfo(line_num=2, page=3, text="B"),
        ]
        start, end = get_page_range(lines, 1, 2)
        assert start == 3
        assert end == 3

    def test_different_pages(self):
        """Should return different pages when range spans pages."""
        lines = [
            LineInfo(line_num=1, page=1, text="A"),
            LineInfo(line_num=2, page=2, text="B"),
            LineInfo(line_num=3, page=3, text="C"),
        ]
        start, end = get_page_range(lines, 1, 3)
        assert start == 1
        assert end == 3


class TestExtractWithLineInfo:
    """Tests for extract_with_line_info function using real PDF."""

    def test_extracts_from_pdf(self, sample_pdf_path):
        """Should extract lines with page info from DPDP Act PDF."""
        line_infos, numbered_text = extract_with_line_info(sample_pdf_path)

        # Should have many lines
        assert len(line_infos) > 100

        # Line numbers should be sequential starting from 1
        assert line_infos[0].line_num == 1
        for i, li in enumerate(line_infos):
            assert li.line_num == i + 1

        # Should have page numbers (at least some > 1)
        pages = set(li.page for li in line_infos)
        assert len(pages) > 1  # Multiple pages
        assert 1 in pages  # Has page 1

    def test_numbered_text_format(self, sample_pdf_path):
        """Should produce correctly formatted numbered text."""
        line_infos, numbered_text = extract_with_line_info(sample_pdf_path)

        # Should have line number format
        assert "| " in numbered_text

        # First line should start with 1
        first_line = numbered_text.split('\n')[0]
        assert first_line.strip().startswith("1|") or "1| " in first_line

    def test_no_page_markers_in_output(self, sample_pdf_path):
        """Page markers should not appear in output."""
        line_infos, numbered_text = extract_with_line_info(sample_pdf_path)

        # No [PAGE:N] markers
        assert "[PAGE:" not in numbered_text
        for li in line_infos:
            assert "[PAGE:" not in li.text

    def test_content_preserved(self, sample_pdf_path):
        """Important content should be in extracted text."""
        line_infos, numbered_text = extract_with_line_info(sample_pdf_path)

        # Key content should be present
        full_text = '\n'.join(li.text for li in line_infos)
        assert "CHAPTER" in full_text
        assert "DIGITAL" in full_text or "DATA" in full_text
