"""Tests for Akoma Ntoso XML generator."""
import pytest
from lxml import etree
from src.generator.akn_generator import generate_akn, AKN_NAMESPACE
from src.parser.document_extractor import Document, ExtractedChapter, ExtractedSection, ExtractedSubSection
from src.parser.metadata_extractor import ActMetadata


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return ActMetadata(
        title="THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023",
        act_number=22,
        year=2023,
        short_title="Digital Personal Data Protection Act, 2023",
        date_enacted="2023-08-11"
    )


@pytest.fixture
def sample_document(sample_metadata):
    """Sample document for testing."""
    return Document(
        metadata=sample_metadata,
        hierarchy=["chapters", "sections", "subsections"],
        chapters=[
            ExtractedChapter(
                number="I",
                title="PRELIMINARY",
                start_line=25,
                end_line=135,
                sections=[
                    ExtractedSection(
                        number=1,
                        heading="Short title and commencement",
                        subsections=[
                            ExtractedSubSection(number=1, content="This Act may be called the Digital Personal Data Protection Act, 2023."),
                            ExtractedSubSection(number=2, content="It shall come into force on such date as the Central Government may appoint.")
                        ]
                    ),
                    ExtractedSection(
                        number=2,
                        heading="Definitions",
                        subsections=[]
                    )
                ]
            ),
            ExtractedChapter(
                number="II",
                title="OBLIGATIONS OF DATA FIDUCIARY",
                start_line=136,
                end_line=406,
                sections=[
                    ExtractedSection(
                        number=4,
                        heading="Grounds for processing personal data",
                        subsections=[]
                    )
                ]
            )
        ]
    )


class TestAknStructure:
    """Tests for basic AKN XML structure."""

    def test_generate_akn_returns_string(self, sample_document):
        """Should return XML as string."""
        xml = generate_akn(sample_document)
        assert isinstance(xml, str)
        assert xml.startswith("<?xml")

    def test_has_akoma_ntoso_root(self, sample_document):
        """Should have akomaNtoso as root element."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        assert root.tag == f"{{{AKN_NAMESPACE}}}akomaNtoso"

    def test_has_act_element(self, sample_document):
        """Should have act element inside root."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        act = root.find(f"{{{AKN_NAMESPACE}}}act")
        assert act is not None

    def test_has_meta_element(self, sample_document):
        """Should have meta element with identification."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        meta = root.find(f".//{{{AKN_NAMESPACE}}}meta")
        assert meta is not None

    def test_has_body_element(self, sample_document):
        """Should have body element."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        body = root.find(f".//{{{AKN_NAMESPACE}}}body")
        assert body is not None


class TestAknMetadata:
    """Tests for FRBR metadata generation."""

    def test_has_frbr_work(self, sample_document):
        """Should have FRBRWork element."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        frbr_work = root.find(f".//{{{AKN_NAMESPACE}}}FRBRWork")
        assert frbr_work is not None

    def test_frbr_has_country(self, sample_document):
        """FRBRWork should have country=in."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        country = root.find(f".//{{{AKN_NAMESPACE}}}FRBRcountry")
        assert country is not None
        assert country.get("value") == "in"

    def test_frbr_has_act_number(self, sample_document):
        """FRBRWork should have act number."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        number = root.find(f".//{{{AKN_NAMESPACE}}}FRBRnumber")
        assert number is not None
        assert number.get("value") == "22"


class TestAknBody:
    """Tests for body content generation."""

    def test_has_chapters(self, sample_document):
        """Body should contain chapter elements."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        chapters = root.findall(f".//{{{AKN_NAMESPACE}}}chapter")
        assert len(chapters) == 2

    def test_chapter_has_eid(self, sample_document):
        """Chapters should have eId attribute."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        chapter = root.find(f".//{{{AKN_NAMESPACE}}}chapter")
        assert chapter.get("eId") == "chp_I"

    def test_chapter_has_num_and_heading(self, sample_document):
        """Chapters should have num and heading elements."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        chapter = root.find(f".//{{{AKN_NAMESPACE}}}chapter")
        num = chapter.find(f"{{{AKN_NAMESPACE}}}num")
        heading = chapter.find(f"{{{AKN_NAMESPACE}}}heading")
        assert num is not None
        assert heading is not None
        assert "I" in num.text
        assert "PRELIMINARY" in heading.text

    def test_has_sections(self, sample_document):
        """Chapters should contain section elements."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        sections = root.findall(f".//{{{AKN_NAMESPACE}}}section")
        assert len(sections) == 3  # 2 in chapter I, 1 in chapter II

    def test_section_has_eid(self, sample_document):
        """Sections should have eId attribute."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        section = root.find(f".//{{{AKN_NAMESPACE}}}section")
        assert section.get("eId") == "sec_1"

    def test_has_subsections(self, sample_document):
        """Sections should contain subsection elements."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        subsections = root.findall(f".//{{{AKN_NAMESPACE}}}subsection")
        assert len(subsections) == 2  # Section 1 has 2 subsections

    def test_subsection_has_eid(self, sample_document):
        """Subsections should have eId attribute."""
        xml = generate_akn(sample_document)
        root = etree.fromstring(xml.encode())
        subsection = root.find(f".//{{{AKN_NAMESPACE}}}subsection")
        assert subsection.get("eId") == "sec_1__subsec_1"
