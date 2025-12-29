# Project: Universal Legal Document to Akoma Ntoso Converter

## Overview

Convert legal documents (PDF) to Akoma Ntoso (LegalDocML) XML format using Claude API for intelligent parsing. Supports dynamic hierarchy extraction across jurisdictions.

## Architecture

```
PDF Document
    |
    v
[Line-Numbered Extractor] --> LineInfo[] with page tracking
    |
    v
[Level-by-Level Extractor] --> JSON hierarchy (parallel LLM calls)
    |
    v
[AKN Generator] --> Akoma Ntoso 3.0 XML (schema-validated)
```

## Key Files

```
data/                           # Input PDFs
output/                         # Generated JSON and XML
schemas/                        # AKN 3.0 XSD schemas
scripts/                        # Extraction scripts

src/
  extractor/
    line_numbered_extractor.py  # PDF to line-numbered text with page tracking
  parser/
    level_extractor.py          # BFS hierarchy extraction with LLM
    llm_client.py               # Claude API client
  generator/
    akn_generator.py            # JSON hierarchy to AKN XML
  models/
    line_info.py                # LineInfo model (line_num, page, text)
    segment.py                  # Segment model for LLM output

tests/                          # pytest tests
```

## Commands

```bash
# Run tests
pytest

# Extract hierarchy from PDF to JSON
python scripts/extract_full_document.py

# Generate AKN XML from JSON
python -c "
from src.generator.akn_generator import generate_akn_from_json_file
generate_akn_from_json_file(
    'output/dpdp_act_hierarchy.json',
    'output/dpdp_act.xml',
    {'title': 'Digital Personal Data Protection Act, 2023', 'year': 2023, 'act_number': 22, 'date_enacted': '2023-08-11'}
)
"

# Validate against AKN 3.0 schema
python -c "
from lxml import etree
import os
os.chdir('schemas')
schema = etree.XMLSchema(etree.parse('akomantoso30.xsd'))
os.chdir('..')
doc = etree.parse('output/dpdp_act.xml')
print('Valid' if schema.validate(doc) else schema.error_log)
"
```

## Environment

Requires `ANTHROPIC_API_KEY` environment variable.

```bash
set ANTHROPIC_API_KEY=your-key-here
```

## Pipeline Steps

### 1. Line-Numbered Extraction

```python
from src.extractor.line_numbered_extractor import extract_with_line_info
line_infos, numbered_text = extract_with_line_info("data/act.pdf")
# Returns LineInfo objects with line_num, page, text
```

### 2. Level-by-Level Hierarchy Extraction

```python
from src.parser.level_extractor import extract_level_by_level
nodes = extract_level_by_level(line_infos, parallel=True, max_workers=5)
# Returns HierarchyNode tree with dynamic types (chapter, section, subsection, etc.)
```

### 3. AKN XML Generation

```python
from src.generator.akn_generator import generate_akn_from_hierarchy
xml = generate_akn_from_hierarchy(hierarchy_data, metadata)
# Returns schema-valid AKN 3.0 XML string
```

## Key Design Decisions

1. **Line Numbers** - All text includes line numbers for accurate LLM citations
2. **Page Tracking** - `[PAGE:N]` markers track PDF page numbers
3. **Dynamic Hierarchy** - LLM discovers element types (not hardcoded)
4. **Breadth-First** - Level-by-level extraction enables parallelization
5. **Skip Same-Range** - Prevents infinite recursion when LLM returns parent as child

## Project Documents

- **PRD.md** - Product Requirements Document
- **BACKLOG.md** - Kanban backlog
