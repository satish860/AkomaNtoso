"""Tests for metadata extraction using structured outputs."""
import pytest
from datetime import date
from src.parser.metadata_extractor import extract_metadata, ActMetadata


@pytest.fixture(scope="module")
def cleaned_text():
    """Load pre-cleaned DPDP Act text."""
    from pathlib import Path
    cleaned_path = Path(__file__).parent.parent / "output" / "dpdp_act_cleaned.txt"
    return cleaned_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def metadata(cleaned_text):
    """Extract metadata once for all tests (expensive LLM call)."""
    return extract_metadata(cleaned_text)


class TestActMetadataModel:
    """Tests for ActMetadata Pydantic model."""

    def test_metadata_has_title(self):
        """ActMetadata should have a title field."""
        meta = ActMetadata(
            title="THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023",
            act_number=22,
            year=2023
        )
        assert meta.title == "THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023"

    def test_metadata_has_act_number(self):
        """ActMetadata should have an act_number field."""
        meta = ActMetadata(
            title="Test Act",
            act_number=22,
            year=2023
        )
        assert meta.act_number == 22

    def test_metadata_has_year(self):
        """ActMetadata should have a year field."""
        meta = ActMetadata(
            title="Test Act",
            act_number=22,
            year=2023
        )
        assert meta.year == 2023

    def test_metadata_has_optional_short_title(self):
        """ActMetadata should have optional short_title."""
        meta = ActMetadata(
            title="Test Act",
            act_number=22,
            year=2023,
            short_title="DPDP Act"
        )
        assert meta.short_title == "DPDP Act"

    def test_metadata_short_title_defaults_none(self):
        """short_title should default to None."""
        meta = ActMetadata(
            title="Test Act",
            act_number=22,
            year=2023
        )
        assert meta.short_title is None

    def test_metadata_has_optional_date_enacted(self):
        """ActMetadata should have optional date_enacted."""
        meta = ActMetadata(
            title="Test Act",
            act_number=22,
            year=2023,
            date_enacted="2023-08-11"
        )
        assert meta.date_enacted == "2023-08-11"


class TestExtractMetadata:
    """Tests for extract_metadata function - uses single extraction."""

    def test_extract_metadata_returns_model(self, metadata):
        """Should return an ActMetadata object."""
        assert isinstance(metadata, ActMetadata)

    def test_extracts_title(self, metadata):
        """Should extract the full act title."""
        assert "DIGITAL PERSONAL DATA PROTECTION" in metadata.title.upper()

    def test_extracts_act_number(self, metadata):
        """Should extract act number 22."""
        assert metadata.act_number == 22

    def test_extracts_year(self, metadata):
        """Should extract year 2023."""
        assert metadata.year == 2023

    def test_extracts_date_enacted(self, metadata):
        """Should extract date enacted (August 11, 2023)."""
        assert metadata.date_enacted is not None
        assert "2023" in metadata.date_enacted
        # Could be "2023-08-11" or "11th August, 2023" - just check year present

    def test_extracts_short_title(self, metadata):
        """Should extract short title reference."""
        # From section 1: "This Act may be called the Digital Personal Data Protection Act, 2023"
        assert metadata.short_title is not None
        assert "Digital Personal Data Protection" in metadata.short_title
