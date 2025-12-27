"""Tests for clause extraction using structured outputs."""
import pytest
from src.parser.clause_extractor import extract_clauses, Clause
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
def chapter_two_text(cleaned_text, chapters):
    """Get text for Chapter II (OBLIGATIONS OF DATA FIDUCIARY)."""
    return get_chapter_text(cleaned_text, chapters[1])


@pytest.fixture(scope="module")
def section_four_subsection_one_clauses(chapter_two_text):
    """Extract clauses from Section 4, Subsection (1)."""
    # Section 4(1) has clauses (a) and (b)
    return extract_clauses(chapter_two_text, section_num=4, subsection_num=1)


class TestClauseModel:
    """Tests for Clause Pydantic model."""

    def test_clause_has_letter(self):
        """Clause should have a letter field."""
        clause = Clause(letter="a", content="for which the Data Principal has given her consent")
        assert clause.letter == "a"

    def test_clause_has_content(self):
        """Clause should have a content field."""
        clause = Clause(letter="a", content="for which the Data Principal has given her consent")
        assert clause.content == "for which the Data Principal has given her consent"


class TestExtractClauses:
    """Tests for extract_clauses function."""

    def test_extract_clauses_returns_list(self, section_four_subsection_one_clauses):
        """Should return a list of Clause objects."""
        assert isinstance(section_four_subsection_one_clauses, list)
        assert len(section_four_subsection_one_clauses) > 0

    def test_section_four_subsection_one_has_two_clauses(self, section_four_subsection_one_clauses):
        """Section 4(1) has clauses (a) and (b)."""
        assert len(section_four_subsection_one_clauses) == 2

    def test_clause_a_about_consent(self, section_four_subsection_one_clauses):
        """Clause (a) should be about consent."""
        clause_a = section_four_subsection_one_clauses[0]
        assert clause_a.letter == "a"
        assert "consent" in clause_a.content.lower()

    def test_clause_b_about_legitimate_uses(self, section_four_subsection_one_clauses):
        """Clause (b) should be about legitimate uses."""
        clause_b = section_four_subsection_one_clauses[1]
        assert clause_b.letter == "b"
        assert "legitimate" in clause_b.content.lower()

    def test_clauses_have_sequential_letters(self, section_four_subsection_one_clauses):
        """Clause letters should be sequential."""
        letters = [c.letter for c in section_four_subsection_one_clauses]
        assert letters == ["a", "b"]
