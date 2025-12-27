"""Tests for section extraction using structured outputs."""
import pytest
from src.parser.section_extractor import extract_sections, Section
from src.parser.chapter_extractor import extract_chapters, get_chapter_text


@pytest.fixture(scope="module")
def cleaned_text():
    """Load pre-cleaned DPDP Act text."""
    from pathlib import Path
    cleaned_path = Path(__file__).parent.parent / "output" / "dpdp_act_cleaned.txt"
    return cleaned_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def chapters(cleaned_text):
    """Extract chapters once."""
    return extract_chapters(cleaned_text)


@pytest.fixture(scope="module")
def chapter_one_text(cleaned_text, chapters):
    """Get text for Chapter I only."""
    return get_chapter_text(cleaned_text, chapters[0])


@pytest.fixture(scope="module")
def chapter_one_sections(chapter_one_text):
    """Extract sections from Chapter I once."""
    return extract_sections(chapter_one_text, chapter_num="I")


class TestSectionModel:
    """Tests for Section Pydantic model."""

    def test_section_has_number(self):
        """Section should have a number field."""
        sec = Section(number=1, heading="Short title and commencement")
        assert sec.number == 1

    def test_section_has_heading(self):
        """Section should have a heading field."""
        sec = Section(number=1, heading="Short title and commencement")
        assert sec.heading == "Short title and commencement"


class TestGetChapterText:
    """Tests for get_chapter_text function."""

    def test_get_chapter_text_returns_string(self, cleaned_text, chapters):
        """Should return chapter text as string."""
        text = get_chapter_text(cleaned_text, chapters[0])
        assert isinstance(text, str)
        assert len(text) > 0

    def test_chapter_one_contains_chapter_marker(self, chapter_one_text):
        """Chapter I text should contain CHAPTER I."""
        assert "CHAPTER I" in chapter_one_text

    def test_chapter_one_does_not_contain_chapter_two(self, chapter_one_text):
        """Chapter I text should not contain Chapter II content."""
        assert "CHAPTER II" not in chapter_one_text


class TestExtractSections:
    """Tests for extract_sections function - uses single extraction."""

    def test_extract_sections_returns_list(self, chapter_one_sections):
        """Should return a list of Section objects."""
        assert isinstance(chapter_one_sections, list)
        assert len(chapter_one_sections) > 0

    def test_chapter_one_has_three_sections(self, chapter_one_sections):
        """Chapter I (PRELIMINARY) has sections 1, 2, 3."""
        assert len(chapter_one_sections) == 3

    def test_section_one_is_short_title(self, chapter_one_sections):
        """Section 1 should be about short title and commencement."""
        sec1 = chapter_one_sections[0]
        assert sec1.number == 1
        assert "title" in sec1.heading.lower() or "commencement" in sec1.heading.lower()

    def test_section_two_is_definitions(self, chapter_one_sections):
        """Section 2 should be Definitions."""
        sec2 = chapter_one_sections[1]
        assert sec2.number == 2
        assert "definition" in sec2.heading.lower()

    def test_section_three_is_application(self, chapter_one_sections):
        """Section 3 should be Application of Act."""
        sec3 = chapter_one_sections[2]
        assert sec3.number == 3
        assert "application" in sec3.heading.lower()
