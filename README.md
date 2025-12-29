# Legal Document to Akoma Ntoso Converter

Convert legal documents (PDF) to [Akoma Ntoso](http://www.akomantoso.org/) (LegalDocML) XML format using Claude API for intelligent parsing.

## Features

- **PDF Extraction** - Extract text with line numbers and page tracking
- **Dynamic Hierarchy** - LLM discovers document structure (chapters, sections, subsections, etc.)
- **Parallel Processing** - Level-by-level extraction with concurrent LLM calls
- **Schema Validation** - Output validates against official AKN 3.0 XSD schema
- **Multi-jurisdiction** - Works with Indian Acts, Irish Statutory Instruments, and more

## Installation

```bash
# Clone the repository
git clone https://github.com/satish860/AkomaNtoso.git
cd AkomaNtoso

# Install dependencies
pip install -r requirements.txt

# Set API key
set ANTHROPIC_API_KEY=your-key-here  # Windows
export ANTHROPIC_API_KEY=your-key-here  # Linux/Mac
```

## Quick Start

### 1. Extract Hierarchy from PDF

```bash
python scripts/extract_full_document.py
```

This extracts the document structure and saves to `output/dpdp_act_hierarchy.json`.

### 2. Generate Akoma Ntoso XML

```python
from src.generator.akn_generator import generate_akn_from_json_file

generate_akn_from_json_file(
    'output/dpdp_act_hierarchy.json',
    'output/dpdp_act.xml',
    {
        'title': 'Digital Personal Data Protection Act, 2023',
        'year': 2023,
        'act_number': 22,
        'date_enacted': '2023-08-11'
    }
)
```

### 3. Validate Against Schema

```python
from lxml import etree
import os

os.chdir('schemas')
schema = etree.XMLSchema(etree.parse('akomantoso30.xsd'))
os.chdir('..')
doc = etree.parse('output/dpdp_act.xml')
print('Valid!' if schema.validate(doc) else schema.error_log)
```

## Architecture

```
PDF Document
    |
    v
[Line-Numbered Extractor]  -->  LineInfo[] with page tracking
    |
    v
[Level-by-Level Extractor] -->  JSON hierarchy (parallel LLM calls)
    |
    v
[AKN Generator]            -->  Akoma Ntoso 3.0 XML
```

## Project Structure

```
data/                           # Input PDFs
output/                         # Generated JSON and XML
schemas/                        # AKN 3.0 XSD schemas

src/
  extractor/
    line_numbered_extractor.py  # PDF to line-numbered text
  parser/
    level_extractor.py          # BFS hierarchy extraction
    llm_client.py               # Claude API client
  generator/
    akn_generator.py            # JSON to AKN XML
  models/
    line_info.py                # LineInfo model
    segment.py                  # Segment model

scripts/
  extract_full_document.py      # Full extraction pipeline

tests/                          # pytest tests
```

## Example Output

Input: DPDP Act 2023 (PDF)

Output: Schema-valid Akoma Ntoso XML

```xml
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="DigitalPersonalDataProtectionAct2023">
    <meta>
      <identification source="#source">
        <FRBRWork>
          <FRBRthis value="/in/act/2023/22/main"/>
          <FRBRuri value="/in/act/2023/22"/>
          <FRBRdate date="2023-08-11" name="enacted"/>
          <FRBRauthor href="#parliament"/>
          <FRBRcountry value="in"/>
          <FRBRnumber value="22"/>
          <FRBRname value="Digital Personal Data Protection Act, 2023"/>
        </FRBRWork>
        ...
      </identification>
    </meta>
    <body>
      <chapter eId="chp_i">
        <num>CHAPTER I</num>
        <heading>PRELIMINARY</heading>
        <section eId="chp_i__sec_1">
          <num>1.</num>
          <heading>Short title and commencement.</heading>
          <subsection eId="chp_i__sec_1__subsec_1">
            <num>(1)</num>
            <content>
              <p>This Act may be called the Digital Personal Data Protection Act, 2023.</p>
            </content>
          </subsection>
        </section>
      </chapter>
    </body>
  </act>
</akomaNtoso>
```

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key (required) |
| `ANTHROPIC_MODEL` | Model to use (default: claude-sonnet-4-20250514) |

## Running Tests

```bash
pytest
```

## License

MIT
