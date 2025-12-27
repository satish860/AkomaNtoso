"""Tests for subsection extraction using structured outputs."""
import pytest
from src.parser.subsection_extractor import extract_subsections, SubSection
from src.parser.chapter_extractor import extract_chapters, get_chapter_text
from src.parser.section_extractor import extract_sections


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
def chapter_two_text(cleaned_text, chapters):
    """Get text for Chapter II (OBLIGATIONS OF DATA FIDUCIARY)."""
    return get_chapter_text(cleaned_text, chapters[1])


@pytest.fixture(scope="module")
def chapter_two_sections(chapter_two_text):
    """Extract sections from Chapter II."""
    return extract_sections(chapter_two_text, chapter_num="II")


@pytest.fixture(scope="module")
def section_four_subsections(chapter_two_text, chapter_two_sections):
    """Extract subsections from Section 4 (Grounds for processing)."""
    # Section 4 is the first section in Chapter II
    sec4 = chapter_two_sections[0]
    return extract_subsections(chapter_two_text, section_num=sec4.number)


class TestSubSectionModel:
    """Tests for SubSection Pydantic model."""

    def test_subsection_has_number(self):
        """SubSection should have a number field."""
        sub = SubSection(number=1, content="This is subsection content.")
        assert sub.number == 1

    def test_subsection_has_content(self):
        """SubSection should have a content field."""
        sub = SubSection(number=1, content="This is subsection content.")
        assert sub.content == "This is subsection content."


class TestExtractSubsections:
    """Tests for extract_subsections function."""

    def test_extract_subsections_returns_list(self, section_four_subsections):
        """Should return a list of SubSection objects."""
        assert isinstance(section_four_subsections, list)
        assert len(section_four_subsections) > 0

    def test_section_four_has_two_subsections(self, section_four_subsections):
        """Section 4 has subsections (1) and (2)."""
        assert len(section_four_subsections) == 2

    def test_subsection_one_about_consent(self, section_four_subsections):
        """Subsection (1) should be about processing personal data."""
        sub1 = section_four_subsections[0]
        assert sub1.number == 1
        assert "personal data" in sub1.content.lower() or "consent" in sub1.content.lower()

    def test_subsection_two_about_lawful_purpose(self, section_four_subsections):
        """Subsection (2) should define lawful purpose."""
        sub2 = section_four_subsections[1]
        assert sub2.number == 2
        assert "lawful purpose" in sub2.content.lower()

    def test_subsections_have_sequential_numbers(self, section_four_subsections):
        """Subsection numbers should be sequential."""
        numbers = [sub.number for sub in section_four_subsections]
        assert numbers == [1, 2]
