"""Tests for unified document extraction."""
import pytest
from src.parser.document_extractor import extract_document, Document


@pytest.fixture(scope="module")
def cleaned_text():
    """Load pre-cleaned DPDP Act text."""
    from pathlib import Path
    cleaned_path = Path(__file__).parent.parent / "output" / "dpdp_act_cleaned.txt"
    return cleaned_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def document(cleaned_text):
    """Extract full document once (expensive - multiple LLM calls)."""
    return extract_document(cleaned_text)


class TestDocumentModel:
    """Tests for Document model structure."""

    def test_document_has_metadata(self, document):
        """Document should have metadata."""
        assert document.metadata is not None
        assert document.metadata.title is not None

    def test_document_has_chapters(self, document):
        """Document should have chapters list."""
        assert document.chapters is not None
        assert isinstance(document.chapters, list)

    def test_document_has_hierarchy(self, document):
        """Document should store detected hierarchy."""
        assert document.hierarchy is not None
        assert isinstance(document.hierarchy, list)


class TestExtractDocument:
    """Tests for extract_document function."""

    def test_extracts_metadata(self, document):
        """Should extract document metadata."""
        assert "DIGITAL PERSONAL DATA PROTECTION" in document.metadata.title.upper()
        assert document.metadata.act_number == 22
        assert document.metadata.year == 2023

    def test_extracts_all_chapters(self, document):
        """Should extract all 9 chapters."""
        assert len(document.chapters) == 9

    def test_chapter_has_sections(self, document):
        """Each chapter should have sections."""
        ch1 = document.chapters[0]
        assert ch1.sections is not None
        assert len(ch1.sections) > 0

    def test_chapter_one_has_three_sections(self, document):
        """Chapter I should have 3 sections."""
        ch1 = document.chapters[0]
        assert len(ch1.sections) == 3

    def test_section_has_heading(self, document):
        """Sections should have headings."""
        sec1 = document.chapters[0].sections[0]
        assert sec1.heading is not None

    def test_hierarchy_detected(self, document):
        """Should detect hierarchy: chapters > sections > subsections > clauses."""
        assert "chapters" in document.hierarchy
        assert "sections" in document.hierarchy


class TestNestedStructure:
    """Tests for nested extraction (sections with subsections)."""

    def test_section_can_have_subsections(self, document):
        """Section 4 (in Chapter II) should have subsections."""
        # Chapter II, Section 4 has subsections
        ch2 = document.chapters[1]
        sec4 = ch2.sections[0]  # First section in Chapter II is Section 4
        assert sec4.subsections is not None
        assert len(sec4.subsections) >= 2
