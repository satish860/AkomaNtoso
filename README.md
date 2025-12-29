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

### Convert PDF to AKN XML (One Command)

```bash
# Auto-detects metadata (title, country, year, etc.)
python scripts/pdf_to_akn.py data/your_document.pdf

# With manual metadata
python scripts/pdf_to_akn.py data/irish_si_607.pdf \
    --title "European Union (Markets in Crypto-Assets) Regulations 2024" \
    --country ie --doc-type regulation --year 2024 --number 607
```

This will:
1. Extract text from PDF
2. Auto-detect metadata (or use provided)
3. Extract document hierarchy (parallel LLM calls)
4. Generate AKN XML
5. Validate against AKN 3.0 schema

Output: `output/<filename>.xml` and `output/<filename>_hierarchy.json`

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
  pdf_to_akn.py                 # Complete pipeline: PDF -> JSON -> XML
  extract_full_document.py      # JSON extraction only

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
| `ANTHROPIC_ENDPOINT` | API endpoint URL (required) |
| `ANTHROPIC_DEPLOYMENT` | Model deployment name (default: claude-sonnet-4-5) |

## Rate Limits

The tool uses parallel LLM calls for faster extraction. If you hit rate limits:

```bash
# Reduce parallel workers (default: 3)
python scripts/pdf_to_akn.py data/document.pdf --workers 2

# Or use sequential mode (slower but no rate limits)
python scripts/pdf_to_akn.py data/document.pdf --sequential
```

The tool includes automatic retry with exponential backoff (10s, 20s, 40s...) for rate limit errors.

## Running Tests

```bash
pytest
```

## License

MIT
