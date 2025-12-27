"""Tests for structure analyzer - discovers what elements exist in a document."""
import pytest
from src.parser.structure_analyzer import analyze_structure, get_hierarchy


@pytest.fixture(scope="module")
def cleaned_text():
    """Load pre-cleaned DPDP Act text."""
    from pathlib import Path
    cleaned_path = Path(__file__).parent.parent / "output" / "dpdp_act_cleaned.txt"
    return cleaned_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def structure_result(cleaned_text):
    """Analyze structure once for all tests (expensive LLM call)."""
    return analyze_structure(cleaned_text)


class TestAnalyzeStructure:
    """Tests for analyze_structure function - uses single LLM call."""

    def test_analyze_structure_returns_dict(self, structure_result):
        """Should return a dictionary."""
        assert isinstance(structure_result, dict)

    def test_analyze_structure_has_elements_found_key(self, structure_result):
        """Should have elements_found key with boolean values."""
        assert "elements_found" in structure_result
        assert isinstance(structure_result["elements_found"], dict)

    def test_detects_chapters(self, structure_result):
        """DPDP Act has chapters - should detect them."""
        assert structure_result["elements_found"]["chapters"] is True

    def test_detects_sections(self, structure_result):
        """DPDP Act has sections - should detect them."""
        assert structure_result["elements_found"]["sections"] is True

    def test_detects_subsections(self, structure_result):
        """DPDP Act has subsections - should detect them."""
        assert structure_result["elements_found"]["subsections"] is True

    def test_detects_clauses(self, structure_result):
        """DPDP Act has clauses (a), (b) - should detect them."""
        assert structure_result["elements_found"]["clauses"] is True

    def test_detects_schedule(self, structure_result):
        """DPDP Act has a schedule - should detect it."""
        assert structure_result["elements_found"]["schedules"] is True

    def test_detects_explanations(self, structure_result):
        """DPDP Act has Explanation elements - should detect them."""
        assert structure_result["elements_found"]["explanations"] is True

    def test_no_provisos(self, structure_result):
        """DPDP Act has no 'Provided that' provisos."""
        assert structure_result["elements_found"]["provisos"] is False

    def test_has_counts(self, structure_result):
        """Should include counts for detected elements (approximate)."""
        assert "counts" in structure_result
        # LLM estimates from sample - check counts are reasonable, not exact
        assert structure_result["counts"]["chapters"] > 0
        assert structure_result["counts"]["sections"] > 0


class TestGetHierarchy:
    """Tests for get_hierarchy function."""

    def test_get_hierarchy_returns_list(self, structure_result):
        """Should return a list of hierarchy levels."""
        hierarchy = get_hierarchy(structure_result)
        assert isinstance(hierarchy, list)

    def test_hierarchy_has_chapters_for_dpdp(self, structure_result):
        """DPDP Act has chapters in hierarchy."""
        hierarchy = get_hierarchy(structure_result)
        assert "chapters" in hierarchy

    def test_hierarchy_has_sections_for_dpdp(self, structure_result):
        """DPDP Act has sections in hierarchy."""
        hierarchy = get_hierarchy(structure_result)
        assert "sections" in hierarchy

    def test_hierarchy_order_chapters_before_sections(self, structure_result):
        """Chapters should come before sections in hierarchy."""
        hierarchy = get_hierarchy(structure_result)
        chapters_idx = hierarchy.index("chapters")
        sections_idx = hierarchy.index("sections")
        assert chapters_idx < sections_idx

    def test_hierarchy_order_sections_before_subsections(self, structure_result):
        """Sections should come before subsections in hierarchy."""
        hierarchy = get_hierarchy(structure_result)
        sections_idx = hierarchy.index("sections")
        subsections_idx = hierarchy.index("subsections")
        assert sections_idx < subsections_idx

    def test_hierarchy_excludes_missing_elements(self):
        """Should not include elements that are not found."""
        mock_result = {
            "elements_found": {
                "chapters": False,
                "sections": True,
                "subsections": True,
                "clauses": False
            }
        }
        hierarchy = get_hierarchy(mock_result)
        assert "chapters" not in hierarchy
        assert "clauses" not in hierarchy
        assert "sections" in hierarchy
