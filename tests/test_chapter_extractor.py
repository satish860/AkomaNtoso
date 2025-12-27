"""Tests for chapter extraction using structured outputs."""
import pytest
from src.parser.chapter_extractor import extract_chapters, Chapter, get_chapter_text


@pytest.fixture
def cleaned_text():
    """Load pre-cleaned DPDP Act text."""
    from pathlib import Path
    cleaned_path = Path(__file__).parent.parent / "output" / "dpdp_act_cleaned.txt"
    return cleaned_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def extracted_chapters():
    """Extract chapters once for all tests (expensive LLM call)."""
    from pathlib import Path
    cleaned_path = Path(__file__).parent.parent / "output" / "dpdp_act_cleaned.txt"
    text = cleaned_path.read_text(encoding="utf-8")
    return extract_chapters(text)


class TestChapterModel:
    """Tests for Chapter Pydantic model."""

    def test_chapter_has_number(self):
        """Chapter should have a number field."""
        ch = Chapter(number="I", title="PRELIMINARY", start_line=25, end_line=135)
        assert ch.number == "I"

    def test_chapter_has_title(self):
        """Chapter should have a title field."""
        ch = Chapter(number="I", title="PRELIMINARY", start_line=25, end_line=135)
        assert ch.title == "PRELIMINARY"

    def test_chapter_has_line_numbers(self):
        """Chapter should have start_line and end_line."""
        ch = Chapter(number="I", title="PRELIMINARY", start_line=25, end_line=135)
        assert ch.start_line == 25
        assert ch.end_line == 135


class TestExtractChapters:
    """Tests for extract_chapters function - uses single extraction."""

    def test_extract_chapters_returns_list(self, extracted_chapters):
        """Should return a list of Chapter objects."""
        assert isinstance(extracted_chapters, list)
        assert len(extracted_chapters) > 0

    def test_extract_chapters_finds_all_chapters(self, extracted_chapters):
        """DPDP Act has 9 chapters."""
        assert len(extracted_chapters) == 9

    def test_first_chapter_is_preliminary(self, extracted_chapters):
        """First chapter should be PRELIMINARY."""
        assert extracted_chapters[0].number == "I"
        assert "PRELIMINARY" in extracted_chapters[0].title.upper()

    def test_chapters_have_roman_numerals(self, extracted_chapters):
        """Chapter numbers should be roman numerals."""
        expected_numbers = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
        actual_numbers = [ch.number for ch in extracted_chapters]
        assert actual_numbers == expected_numbers

    def test_chapter_two_is_obligations(self, extracted_chapters):
        """Chapter II should be about obligations."""
        ch2 = extracted_chapters[1]
        assert ch2.number == "II"
        assert "OBLIGATION" in ch2.title.upper()

    def test_chapters_have_valid_line_numbers(self, extracted_chapters):
        """Each chapter should have valid start_line and end_line."""
        for ch in extracted_chapters:
            assert ch.start_line >= 1
            assert ch.end_line > ch.start_line

    def test_chapters_dont_overlap(self, extracted_chapters):
        """Chapter line ranges should not overlap."""
        for i in range(len(extracted_chapters) - 1):
            assert extracted_chapters[i].end_line < extracted_chapters[i + 1].start_line


class TestGetChapterText:
    """Tests for get_chapter_text function."""

    def test_get_chapter_text_returns_string(self, cleaned_text, extracted_chapters):
        """Should return chapter text as string."""
        ch1 = extracted_chapters[0]
        text = get_chapter_text(cleaned_text, ch1)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_chapter_one_contains_chapter_marker(self, cleaned_text, extracted_chapters):
        """Chapter I text should contain CHAPTER I."""
        ch1 = extracted_chapters[0]
        text = get_chapter_text(cleaned_text, ch1)
        assert "CHAPTER I" in text

    def test_chapter_one_does_not_contain_chapter_two(self, cleaned_text, extracted_chapters):
        """Chapter I text should not contain Chapter II."""
        ch1 = extracted_chapters[0]
        text = get_chapter_text(cleaned_text, ch1)
        assert "CHAPTER II" not in text
