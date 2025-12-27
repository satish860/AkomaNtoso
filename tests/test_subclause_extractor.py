"""Tests for subclause extraction using structured outputs."""
import pytest
from src.parser.subclause_extractor import extract_subclauses, SubClause
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
    """Get text for Chapter I (PRELIMINARY) - contains Section 2 Definitions."""
    return get_chapter_text(cleaned_text, chapters[0])


@pytest.fixture(scope="module")
def clause_j_subclauses(chapter_one_text):
    """Extract subclauses from Section 2, clause (j) - Data Principal definition."""
    # Section 2, clause (j) has subclauses (i) and (ii)
    return extract_subclauses(chapter_one_text, section_num=2, clause_letter="j")


class TestSubClauseModel:
    """Tests for SubClause Pydantic model."""

    def test_subclause_has_numeral(self):
        """SubClause should have a numeral field."""
        sub = SubClause(numeral="i", content="a child, includes the parents")
        assert sub.numeral == "i"

    def test_subclause_has_content(self):
        """SubClause should have a content field."""
        sub = SubClause(numeral="i", content="a child, includes the parents")
        assert sub.content == "a child, includes the parents"


class TestExtractSubclauses:
    """Tests for extract_subclauses function."""

    def test_extract_subclauses_returns_list(self, clause_j_subclauses):
        """Should return a list of SubClause objects."""
        assert isinstance(clause_j_subclauses, list)
        assert len(clause_j_subclauses) > 0

    def test_clause_j_has_two_subclauses(self, clause_j_subclauses):
        """Clause (j) has subclauses (i) and (ii)."""
        assert len(clause_j_subclauses) == 2

    def test_subclause_i_about_child(self, clause_j_subclauses):
        """Subclause (i) should be about child."""
        sub_i = clause_j_subclauses[0]
        assert sub_i.numeral == "i"
        assert "child" in sub_i.content.lower()

    def test_subclause_ii_about_disability(self, clause_j_subclauses):
        """Subclause (ii) should be about person with disability."""
        sub_ii = clause_j_subclauses[1]
        assert sub_ii.numeral == "ii"
        assert "disability" in sub_ii.content.lower()

    def test_subclauses_have_sequential_numerals(self, clause_j_subclauses):
        """Subclause numerals should be sequential."""
        numerals = [s.numeral for s in clause_j_subclauses]
        assert numerals == ["i", "ii"]
