# Indian Acts to Akoma Ntoso Converter - Implementation Plan

## Project Overview

Build a semi-automated Python CLI tool to convert Indian Parliamentary Acts (PDF format) to Akoma Ntoso (LegalDocML) XML format, using Claude API for intelligent parsing.

**Key Principles:**
- **Test-Driven Development (TDD)** - Write tests first, then implement
- **Small Incremental Changes** - Build and verify step by step
- **LLM-Assisted Parsing** - Use Claude API for structure recognition
- **Iterative Refinement** - Start simple, evolve as we learn

**Scope:**
- Input: PDF files of Indian Acts (from Gazette of India)
- Output: Akoma Ntoso XML
- Workflow: Automated draft generation + human review/correction
- Architecture: Extensible for other jurisdictions later

---

## Project Structure

```
AkomaNtoso/
    |-- data/                      # Input PDFs (already exists)
    |-- output/                    # Generated XML files
    |-- src/
    |   |-- __init__.py
    |   |-- cli.py                 # Command-line interface
    |   |-- extractor/
    |   |   |-- __init__.py
    |   |   |-- pdf_extractor.py   # PDF to text extraction
    |   |   |-- text_cleaner.py    # Clean and normalize text
    |   |-- parser/
    |   |   |-- __init__.py
    |   |   |-- llm_parser.py      # Claude API for structure parsing
    |   |   |-- structure_parser.py    # Orchestrates parsing
    |   |-- generator/
    |   |   |-- __init__.py
    |   |   |-- akn_generator.py       # Generate Akoma Ntoso XML
    |   |-- models/
    |   |   |-- __init__.py
    |   |   |-- document.py            # Document model classes
    |   |-- prompts/
    |   |   |-- clean_text.txt         # Prompt for text cleaning (LLM-based)
    |   |   |-- extract_metadata.txt   # Prompt for metadata extraction
    |   |   |-- parse_structure.txt    # Prompt for structure parsing
    |   |   |-- extract_section.txt    # Prompt for section parsing
    |-- tests/
    |   |-- __init__.py
    |   |-- conftest.py                # Pytest fixtures
    |   |-- test_pdf_extractor.py
    |   |-- test_text_cleaner.py
    |   |-- test_llm_parser.py
    |   |-- test_akn_generator.py
    |   |-- test_e2e.py                # End-to-end tests
    |   |-- fixtures/
    |       |-- sample_text.txt        # Sample extracted text
    |       |-- expected_structure.json
    |       |-- expected_output.xml
    |-- requirements.txt
    |-- setup.py
    |-- .env.example                   # API key template
```

---

## Development Methodology: TDD

For each component, we follow this cycle:

```
1. Write failing test (RED)
       |
       v
2. Write minimal code to pass (GREEN)
       |
       v
3. Refactor if needed (REFACTOR)
       |
       v
4. Run test to verify --> Next feature
```

**Test file naming:** `test_<module>.py`
**Test function naming:** `test_<function>_<scenario>`

Example:
```python
# tests/test_pdf_extractor.py
def test_extract_text_returns_string():
    """PDF extractor should return text as string"""
    ...

def test_extract_text_preserves_section_numbers():
    """Section numbers like '1.' should be preserved"""
    ...

def test_extract_text_handles_multicolumn():
    """Multi-column layout should be merged correctly"""
    ...
```

---

## Implementation Phases (TDD Style)

### Phase 1: Project Setup & PDF Extraction

**Step 1.1: Project skeleton**
- Create folder structure
- Create `requirements.txt`
- Create `.env.example` for API keys
- Verify pytest runs

**Step 1.2: PDF Extractor (TDD)**

Tests to write FIRST:
```python
# tests/test_pdf_extractor.py

def test_extract_text_from_valid_pdf():
    """Should extract text from DPDP Act PDF"""
    text = extract_text("data/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf")
    assert "DIGITAL PERSONAL DATA PROTECTION ACT" in text
    assert len(text) > 1000

def test_extract_text_preserves_structure():
    """Section numbers and chapter headings should be intact"""
    text = extract_text("data/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf")
    assert "CHAPTER I" in text
    assert "1." in text  # Section 1

def test_extract_text_invalid_file_raises():
    """Should raise error for non-existent file"""
    with pytest.raises(FileNotFoundError):
        extract_text("nonexistent.pdf")
```

Then implement:
```python
# src/extractor/pdf_extractor.py

def extract_text(pdf_path: str) -> str:
    """Extract text from PDF file"""
    ...
```

**Step 1.3: Text Cleaner (LLM-Based)**

**Why LLM-based instead of regex?**
- Different jurisdictions (India, UK, USA) have different noise patterns
- Different document types (Acts, Bills, Ordinances) have different headers
- LLM can adapt to any format without manual regex maintenance
- Future-proof for F-001 to F-006 in ICEBOX

**Architecture:**
```
Raw Text --> Sample (first 2000 chars) --> Claude API
                                              |
                                              v
                                    "Identify noise patterns,
                                     return cleaned text"
                                              |
                                              v
                                        Clean Text
```

**Implementation:**
```python
# src/extractor/text_cleaner.py

def clean_text(raw_text: str, jurisdiction: str = "in") -> str:
    """Use LLM to clean extracted text.

    Args:
        raw_text: Raw text from PDF extraction
        jurisdiction: Country code (in, uk, us) for context

    Returns:
        Cleaned text with noise removed
    """
    prompt = f"""
    You are cleaning legal document text extracted from a PDF.
    Jurisdiction: {jurisdiction}

    Remove the following types of noise:
    - Page headers/footers (e.g., "THE GAZETTE OF INDIA EXTRAORDINARY")
    - Page numbers (standalone or embedded)
    - Registration/metadata lines
    - Non-English text (Hindi, etc.) that is not part of the Act
    - Repeated publication information

    Keep:
    - The Act title, number, date
    - All chapters, sections, subsections
    - Definitions, illustrations, provisos, explanations
    - Schedules and annexures

    Return ONLY the cleaned text, no explanations.

    Text to clean:
    {raw_text}
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=len(raw_text) + 1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
```

**Tests (TDD):**
```python
# tests/test_text_cleaner.py

def test_clean_text_removes_gazette_headers():
    """Should remove 'THE GAZETTE OF INDIA EXTRAORDINARY' headers"""
    raw = "THE GAZETTE OF INDIA EXTRAORDINARY\nCHAPTER I\nPRELIMINARY"
    cleaned = clean_text(raw)
    assert "GAZETTE" not in cleaned
    assert "CHAPTER I" in cleaned

def test_clean_text_preserves_act_content():
    """Should preserve the actual Act content"""
    cleaned = clean_text(sample_raw_text)
    assert "DIGITAL PERSONAL DATA PROTECTION ACT" in cleaned
    assert "CHAPTER I" in cleaned

def test_clean_text_removes_hindi():
    """Should remove Hindi/Devanagari headers"""
    raw = "vlk/kkj.k\nEXTRAORDINARY\nCHAPTER I"
    cleaned = clean_text(raw)
    assert "vlk/kkj.k" not in cleaned

def test_clean_text_removes_page_numbers():
    """Should remove standalone and embedded page numbers"""
    raw = "Section 1.\n2\nSection 2."
    cleaned = clean_text(raw)
    # Page number "2" should be removed but section numbers preserved
```

---

### Phase 2: Document Models

**Step 2.1: Define data classes (TDD)**

Tests first:
```python
# tests/test_models.py

def test_section_creation():
    """Section should store number and content"""
    section = Section(number=1, heading="Short title", content="...")
    assert section.number == 1

def test_chapter_contains_sections():
    """Chapter should contain list of sections"""
    chapter = Chapter(number="I", title="PRELIMINARY", sections=[])
    assert chapter.sections == []

def test_act_document_has_metadata():
    """ActDocument should have title, number, year"""
    act = ActDocument(
        title="THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023",
        act_number=22,
        year=2023
    )
    assert act.year == 2023
```

Then implement:
```python
# src/models/document.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class Section:
    number: int
    heading: str
    content: str
    subsections: List['SubSection'] = None

@dataclass
class Chapter:
    number: str
    title: str
    sections: List[Section]

@dataclass
class ActDocument:
    title: str
    act_number: int
    year: int
    date_enacted: Optional[date] = None
    preamble: Optional[str] = None
    chapters: List[Chapter] = None
    schedules: List['Schedule'] = None
```

---

### Phase 3: LLM Parser (Claude API)

**Step 3.1: Claude API Integration**

Tests first:
```python
# tests/test_llm_parser.py

def test_extract_metadata_from_text():
    """LLM should extract act title, number, year from text"""
    sample_text = """
    THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023
    (NO. 22 OF 2023)
    [11th August, 2023.]
    """
    metadata = extract_metadata(sample_text)
    assert metadata['title'] == "THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023"
    assert metadata['act_number'] == 22
    assert metadata['year'] == 2023

def test_parse_structure_identifies_chapters():
    """LLM should identify chapter boundaries"""
    sample_text = "... CHAPTER I PRELIMINARY ... CHAPTER II ..."
    structure = parse_structure(sample_text)
    assert len(structure['chapters']) >= 2

def test_parse_section_extracts_content():
    """LLM should parse a single section correctly"""
    section_text = """
    1. (1) This Act may be called the Digital Personal Data Protection Act, 2023.
    (2) It shall come into force on such date...
    """
    section = parse_section(section_text)
    assert section['number'] == 1
    assert len(section['subsections']) == 2
```

Then implement:
```python
# src/parser/llm_parser.py

import anthropic
import json

client = anthropic.Anthropic()

def extract_metadata(text: str) -> dict:
    """Use Claude to extract metadata from act text"""
    prompt = f"""
    Extract the following metadata from this Indian Act text:
    - title: The full title of the Act
    - act_number: The act number (integer)
    - year: The year (integer)
    - date_enacted: The date in YYYY-MM-DD format

    Text:
    {text[:2000]}

    Return as JSON only, no explanation.
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)

def parse_structure(text: str) -> dict:
    """Use Claude to identify document structure"""
    ...

def parse_section(section_text: str) -> dict:
    """Use Claude to parse a single section into subsections"""
    ...
```

**Step 3.2: Prompts as separate files**

Store prompts in `src/prompts/` for easy iteration:
```
# src/prompts/extract_metadata.txt

You are a legal document parser. Extract metadata from the following Indian Parliamentary Act.

Return JSON with these fields:
- title: Full title of the Act
- act_number: Integer
- year: Integer
- date_enacted: YYYY-MM-DD format
- short_title: Common name if mentioned

Text to parse:
{text}

Return ONLY valid JSON, no explanation.
```

---

### Phase 4: Akoma Ntoso Generator

**Step 4.1: XML Generation (TDD)**

Tests first:
```python
# tests/test_akn_generator.py

def test_generate_act_root_element():
    """Should generate valid akomaNtoso root element"""
    act = ActDocument(title="Test Act", act_number=1, year=2023)
    xml = generate_akn(act)
    assert '<akomaNtoso' in xml
    assert 'xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"' in xml

def test_generate_frbr_metadata():
    """Should generate FRBR identification"""
    act = ActDocument(title="Test", act_number=22, year=2023)
    xml = generate_akn(act)
    assert '<FRBRcountry value="in"/>' in xml
    assert '<FRBRnumber value="22"/>' in xml

def test_generate_chapter_structure():
    """Chapters should have proper eId attributes"""
    chapter = Chapter(number="I", title="TEST", sections=[])
    act = ActDocument(title="Test", act_number=1, year=2023, chapters=[chapter])
    xml = generate_akn(act)
    assert 'eId="chp_I"' in xml

def test_generated_xml_is_valid():
    """Generated XML should be well-formed"""
    act = ActDocument(...)
    xml = generate_akn(act)
    # Should not raise
    etree.fromstring(xml.encode())
```

Then implement:
```python
# src/generator/akn_generator.py

from lxml import etree
from src.models.document import ActDocument

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"

def generate_akn(act: ActDocument) -> str:
    """Generate Akoma Ntoso XML from ActDocument"""
    ...
```

---

### Phase 5: CLI & Integration

**Step 5.1: CLI (TDD)**

Tests first:
```python
# tests/test_cli.py
from click.testing import CliRunner

def test_convert_command_produces_output():
    """convert command should create XML file"""
    runner = CliRunner()
    result = runner.invoke(cli, ['convert', 'data/test.pdf', '-o', 'output/test.xml'])
    assert result.exit_code == 0
    assert os.path.exists('output/test.xml')
```

**Step 5.2: End-to-End Test**

```python
# tests/test_e2e.py

def test_full_pipeline_dpdp_act():
    """Full conversion of DPDP Act should produce valid AKN"""
    input_pdf = "data/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
    output_xml = "output/dpdp_act_2023.xml"

    # Run full pipeline
    result = convert(input_pdf, output_xml)

    # Verify output exists
    assert os.path.exists(output_xml)

    # Verify XML is well-formed
    tree = etree.parse(output_xml)

    # Verify key elements
    root = tree.getroot()
    assert root.tag.endswith('akomaNtoso')

    # Verify metadata
    assert '2023' in etree.tostring(tree).decode()
    assert '22' in etree.tostring(tree).decode()
```

---

## Dependencies

```
# requirements.txt
# PDF Processing
pdfplumber>=0.9.0

# XML Generation
lxml>=4.9.0

# LLM
anthropic>=0.18.0

# CLI
click>=8.0.0
rich>=13.0.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0

# Environment
python-dotenv>=1.0.0
```

---

## Execution Order (TDD Steps)

### Sprint 1: Foundation
1. [x] Download sample PDF (DPDP Act) - DONE
2. [ ] Create project structure (folders, __init__.py files)
3. [ ] Create requirements.txt and install dependencies
4. [ ] Write test_pdf_extractor.py (RED)
5. [ ] Implement pdf_extractor.py (GREEN)
6. [ ] Write test_text_cleaner.py (RED)
7. [ ] Implement text_cleaner.py (GREEN)

### Sprint 2: Models & LLM
8. [ ] Write test_models.py (RED)
9. [ ] Implement document.py models (GREEN)
10. [ ] Set up Claude API (.env)
11. [ ] Write test_llm_parser.py (RED)
12. [ ] Implement llm_parser.py (GREEN)
13. [ ] Create and refine prompts

### Sprint 3: Generation
14. [ ] Write test_akn_generator.py (RED)
15. [ ] Implement akn_generator.py (GREEN)
16. [ ] Write test_cli.py (RED)
17. [ ] Implement cli.py (GREEN)

### Sprint 4: Integration & Polish
18. [ ] Write test_e2e.py (RED)
19. [ ] Run full pipeline, fix issues (GREEN)
20. [ ] Manual review of DPDP Act output
21. [ ] Iterate based on findings

---

## Environment Setup

```bash
# Create .env file
ANTHROPIC_API_KEY=your_api_key_here
```

```python
# Load in code
from dotenv import load_dotenv
load_dotenv()
```

---

## Future Extensibility

The architecture supports:
- **New jurisdictions:** Different prompt templates for UK, USA
- **New document types:** Bills, Judgments with different models
- **Web UI:** Build on CLI foundation
- **Local LLM:** Swap Claude for Ollama if needed
- **Caching:** Cache LLM responses to reduce API costs during testing
