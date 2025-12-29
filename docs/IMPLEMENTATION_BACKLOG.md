# Implementation Backlog: Universal AKN Generator

## Overview

This backlog implements the architecture defined in `ARCHITECTURE.md` for a universal legal document to Akoma Ntoso converter with human-in-the-loop validation.

**Key Workflow:**
```
PDF -> Extract (LLM) -> Review JSON -> Human Validation -> AKN XML
```

---

## Phase 0: Line-Numbered Text Extraction with Page Tracking

### T-050: Create line-numbered text extractor
**File:** `src/extractor/line_numbered_extractor.py`

**Design:** Uses existing `extract_text(include_page_markers=True)` which inserts `[PAGE:N]` markers. Parse markers to track current page, skip markers in output.

**Tasks:**
- [ ] Create `LineInfo` model in `src/models/line_info.py`:
  ```python
  class LineInfo(BaseModel):
      line_num: int   # 1-indexed, sequential
      page: int       # From [PAGE:N] markers
      text: str       # Line content
  ```
- [ ] Implement `extract_with_line_info(pdf_path) -> tuple[List[LineInfo], str]`
  - Call `extract_text(pdf_path, include_page_markers=True)`
  - Parse `[PAGE:N]` markers to track current page
  - Skip marker lines and empty lines
  - Return LineInfo list + formatted numbered text
- [ ] Implement `format_numbered_text(line_infos) -> str`
  - Right-align line numbers: `"  1| CHAPTER I"`
  - Width based on max line number
- [ ] Implement `get_lines_slice(line_infos, start, end) -> str`
  - Returns numbered text for line range (for LLM level extraction)
- [ ] Implement `get_content(line_infos, start, end) -> str`
  - Returns raw text without line numbers (for leaf node content)
- [ ] Implement `get_page_for_line(line_infos, line_num) -> int`

**Exit Criteria:**
- `[PAGE:N]` markers parsed correctly, not in output
- Line numbers sequential (1, 2, 3...) after skipping markers/empty lines
- Each LineInfo has correct page from most recent marker
- Helper functions work for slicing and content extraction

---

### T-051: Write tests for line-numbered extraction
**File:** `tests/test_line_numbered_extractor.py`

**Test Cases:**
- [ ] Parses `[PAGE:N]` markers correctly
- [ ] Markers not included in LineInfo output
- [ ] Line numbers are 1-indexed and sequential
- [ ] Page numbers track from markers (lines after `[PAGE:3]` have page=3)
- [ ] `format_numbered_text()` right-aligns numbers
- [ ] `get_lines_slice()` returns correct numbered subset
- [ ] `get_content()` returns raw text without numbers
- [ ] `get_page_for_line()` returns correct page
- [ ] Edge cases: empty pages, first page has no marker (default page=1)

---

## Phase 1: Core Models and Mapper

### T-100: Create citation model
**File:** `src/models/citation.py`

**Tasks:**
- [ ] Create `SourceCitation` model with fields:
  - `page: int` - PDF page number (1-indexed)
  - `start_char: Optional[int]` - Character offset start
  - `end_char: Optional[int]` - Character offset end
  - `start_line: Optional[int]` - Line number start
  - `end_line: Optional[int]` - Line number end
  - `snippet: Optional[str]` - Short excerpt (50 chars)
- [ ] Add helper method `from_position(char_pos, page_map, text) -> SourceCitation`
- [ ] Export from `src/models/__init__.py`

**Exit Criteria:**
- SourceCitation model complete
- Can create citation from character position

---

### T-101: Create hierarchy models module
**File:** `src/models/hierarchy.py`

**Tasks:**
- [ ] Create `HierarchyNode` with fields:
  - `id: str` - UUID for annotation reference
  - `level: int` - Hierarchy depth (1 = top)
  - `type: str` - Element type (chapter, section, etc.)
  - `number: str` - Numbering (I, 1, (a), etc.)
  - `title: Optional[str]` - Heading text
  - `content: Optional[str]` - Leaf node content
  - `citation: SourceCitation` - Source location
  - `confidence: float` - LLM confidence (0.0-1.0)
  - `status: str` - Validation status (pending/approved/rejected/modified)
  - `reviewer_notes: Optional[str]` - Human comments
  - `children: List[HierarchyNode]` - Nested nodes
  - `parent_id: Optional[str]` - Parent reference
- [ ] Create `DocumentStructure` model (existing fields)
- [ ] Add UUID generation helper
- [ ] Export from `src/models/__init__.py`

**Exit Criteria:**
- Models importable from `src.models`
- All fields with proper types
- UUID auto-generation works

---

### T-102: Create review document model
**File:** `src/models/review.py`

**Tasks:**
- [ ] Create `ReviewStatus` enum: `pending_review`, `in_review`, `approved`, `rejected`
- [ ] Create `NodeStatus` enum: `pending`, `approved`, `rejected`, `modified`
- [ ] Create `ReviewDocument` model with fields:
  - `id: str` - Document UUID
  - `source_pdf: str` - Original PDF path
  - `extracted_at: datetime` - Extraction timestamp
  - `structure: DocumentStructure` - Document metadata
  - `nodes: List[HierarchyNode]` - Extracted hierarchy
  - `status: ReviewStatus` - Overall review status
  - `reviewer: Optional[str]` - Reviewer name
  - `reviewed_at: Optional[datetime]`
  - `statistics: ReviewStatistics` - Extraction stats
- [ ] Create `ReviewStatistics` model:
  - `total_nodes: int`
  - `nodes_by_level: Dict[int, int]`
  - `avg_confidence: float`
  - `approved_count: int`
  - `rejected_count: int`
- [ ] Export from `src/models/__init__.py`

**Exit Criteria:**
- All review models complete
- Statistics calculation works
- JSON serialization works

---

### T-103: Create AKN element mapper
**File:** `src/generator/akn_mapper.py`

**Tasks:**
- [ ] Define `NATIVE_ELEMENTS` set (all AKN hierarchical elements)
- [ ] Define `MAPPINGS` dict (jurisdiction terms -> AKN elements)
- [ ] Define `COUNTRY_CODES` dict (jurisdiction name -> ISO code)
- [ ] Implement `AKNElementMapper` class with `map(node_type: str) -> tuple[str, bool]`
- [ ] Implement `get_country_code(jurisdiction: str) -> str`
- [ ] Implement `get_document_element(doc_type: str) -> str`

**Exit Criteria:**
- All known jurisdiction terms mapped
- Returns `(element_name, is_native)` tuple
- Unknown terms return `(original, False)` for hcontainer fallback

---

### T-104: Write tests for models and mapper
**File:** `tests/test_models.py`, `tests/test_akn_mapper.py`

**Test Cases:**
- [ ] SourceCitation creation from position
- [ ] HierarchyNode UUID auto-generation
- [ ] ReviewDocument statistics calculation
- [ ] Native elements return `(name, True)`
- [ ] Mapped elements return `(mapped_name, True)`
- [ ] Unknown elements return `(name, False)`
- [ ] Country code mapping works

---

## Phase 2: Top-Down Recursive Extraction

### T-200: Create level-by-level extractor
**File:** `src/parser/level_extractor.py`

**Purpose:** Implement top-down recursive extraction where each level is extracted separately from its parent's line range.

**Tasks:**
- [ ] Create `Segment` model: `type: str, number: str, title: Optional[str], start_line: int, end_line: int`
- [ ] Create `LevelExtraction` model: `segments: List[Segment]`
- [ ] Create extraction prompt template (LEVEL_EXTRACTION_PROMPT):
  - Takes element_type, start_line, end_line, text_slice
  - Returns list of segments with line ranges
- [ ] Implement `extract_level(numbered_text, element_type, start_line, end_line) -> List[Segment]`
  - Single LLM call for one level
  - Uses structured outputs for guaranteed schema
- [ ] Implement `extract_hierarchy_recursive(numbered_text, line_infos, hierarchy_types, start_line, end_line, level=0) -> List[HierarchyNode]`
  - Recursive function that extracts level by level
  - For each segment at current level, recurse into next level
  - Build HierarchyNode with SourceCitation from line_infos
  - Leaf nodes get content extracted from line range
- [ ] Add confidence scoring from LLM output
- [ ] Handle edge cases: empty segments, overlapping ranges, missing levels

**Exit Criteria:**
- Each level extracted with separate LLM call
- Parent's line range constrains child extraction
- SourceCitation populated with page, line numbers
- Confidence scores between 0.0-1.0

---

### T-201: Add parallel extraction support
**File:** `src/parser/level_extractor.py`

**Tasks:**
- [ ] Add `parallel: bool = False` parameter to extraction
- [ ] Implement parallel extraction of sibling segments using ThreadPoolExecutor
- [ ] Add `max_workers` parameter (default 3 to avoid rate limits)
- [ ] Ensure results are sorted back to original order

**Exit Criteria:**
- Sibling segments at same level can be extracted in parallel
- Respects rate limits with configurable max_workers
- Results maintain document order

---

### T-202: Create review exporter
**File:** `src/review/review_exporter.py`

**Tasks:**
- [ ] Implement `create_review_document(structure, nodes, pdf_path) -> ReviewDocument`
- [ ] Implement `export_review_json(review_doc, output_path)`
- [ ] Calculate statistics (total nodes, by level, avg confidence)
- [ ] Generate document UUID
- [ ] Set initial status to `pending_review`

**Exit Criteria:**
- Creates valid ReviewDocument from extraction
- Exports to JSON file
- Statistics accurately calculated

---

### T-203: Create HTML preview generator
**File:** `src/review/html_preview.py`

**Tasks:**
- [ ] Implement `generate_preview_html(review_doc) -> str`
- [ ] Create collapsible tree view of hierarchy
- [ ] Show confidence with color coding (red < 0.7, yellow < 0.9, green >= 0.9)
- [ ] Show page numbers for each node
- [ ] Show snippet preview on hover
- [ ] Include node status indicators
- [ ] Add CSS styling (no external dependencies)

**Exit Criteria:**
- Generates standalone HTML file
- Tree view expands/collapses
- Confidence visually indicated
- Works in any browser

---

### T-204: Create review importer
**File:** `src/review/review_importer.py`

**Tasks:**
- [ ] Implement `load_review_json(json_path) -> ReviewDocument`
- [ ] Implement `get_approved_nodes(review_doc) -> List[HierarchyNode]`
- [ ] Implement `filter_by_status(review_doc, status) -> List[HierarchyNode]`
- [ ] Validate JSON structure on load
- [ ] Handle missing optional fields gracefully

**Exit Criteria:**
- Loads validated Review JSON
- Filters nodes by status
- Validation errors reported clearly

---

### T-205: Write tests for extraction and review
**File:** `tests/test_level_extractor.py`, `tests/test_review.py`

**Test Cases:**
- [ ] Level extraction returns segments with correct line ranges
- [ ] Recursive extraction builds full tree
- [ ] Parallel extraction maintains order
- [ ] Review document creation
- [ ] JSON export/import round-trip
- [ ] Statistics calculation
- [ ] HTML preview generation
- [ ] Node filtering by status

---

## Phase 3: Dynamic AKN Generator

### T-300: Create dynamic AKN generator
**File:** `src/generator/dynamic_akn_generator.py`

**Tasks:**
- [ ] Import models from `src.models`
- [ ] Import mapper from `src.generator.akn_mapper`
- [ ] Implement `_generate_frbr_work()` using DocumentStructure
- [ ] Implement `_generate_frbr_expression()` using DocumentStructure
- [ ] Implement `_generate_frbr_manifestation()` using DocumentStructure
- [ ] Implement `_generate_meta()` combining FRBR elements
- [ ] Implement `_generate_hierarchy_node()` recursive function
  - Use mapper to get element name
  - Use native element or hcontainer based on mapper result
  - Generate eId attributes
  - Handle num, heading, content
  - Recursively process children
- [ ] Implement `_generate_body()` iterating over root nodes
- [ ] Implement `generate_akn_dynamic(structure, nodes) -> str` main function
- [ ] Implement `generate_akn_from_review(review_doc, approved_only=True) -> str`
- [ ] Implement `save_akn(xml_str, path)` utility

**Exit Criteria:**
- Generates valid XML string
- Uses native elements where possible
- Falls back to hcontainer for unknown types
- eIds are unique and well-formed
- Can generate from ReviewDocument (approved nodes only)

---

### T-301: Write tests for dynamic AKN generator
**File:** `tests/test_dynamic_akn_generator.py`

**Test Cases:**
- [ ] Simple single-level hierarchy
- [ ] Multi-level nested hierarchy
- [ ] Mixed native and hcontainer elements
- [ ] FRBR metadata generation
- [ ] eId uniqueness
- [ ] Content escaping (special characters)
- [ ] Empty content handling
- [ ] Generation from ReviewDocument

---

## Phase 4: Integration

### T-400: Create unified pipeline
**File:** `src/pipeline.py`

**Tasks:**
- [ ] Implement `extract_to_review(pdf_path) -> ReviewDocument`
  - Extract text with page tracking
  - Analyze structure
  - Extract hierarchy with citations
  - Create ReviewDocument
- [ ] Implement `export_for_review(review_doc, output_dir)`
  - Save Review JSON
  - Generate HTML preview
- [ ] Implement `generate_from_review(review_json_path, output_path) -> str`
  - Load validated review
  - Filter approved nodes
  - Generate AKN XML
- [ ] Implement full `convert_pdf_to_akn(pdf_path, output_path, skip_review=False)`
- [ ] Add progress callback support

**Exit Criteria:**
- Three-stage pipeline works
- Review stage can be skipped for automation
- Progress reported at each stage

---

### T-401: Update CLI for review workflow
**File:** `src/cli.py`

**Tasks:**
- [ ] Add `extract` command: PDF -> Review JSON + HTML preview
- [ ] Add `generate` command: Review JSON -> AKN XML
- [ ] Add `convert` command: PDF -> AKN (full pipeline, optional review skip)
- [ ] Add `--skip-review` flag for automated conversion
- [ ] Add `--output-dir` for review artifacts
- [ ] Update help text with workflow examples

**CLI Commands:**
```bash
# Step 1: Extract and create review files
python -m src.cli extract data/act.pdf -o output/reviews/

# Step 2: (Human reviews and edits review JSON)

# Step 3: Generate AKN from approved review
python -m src.cli generate output/reviews/act_review.json -o output/akn/act.xml

# Or: Full pipeline with review skip
python -m src.cli convert data/act.pdf -o output/act.xml --skip-review
```

**Exit Criteria:**
- All three commands work
- Review workflow supported
- Skip option for automation

---

## Phase 5: Validation

### T-500: Add AKN schema validation
**File:** `src/validator/akn_validator.py`

**Tasks:**
- [ ] Download AKN 3.0 XSD schema to `schemas/`
- [ ] Implement `validate_akn(xml_str) -> ValidationResult`
- [ ] Create `ValidationResult` with `is_valid`, `errors`, `warnings`
- [ ] Return detailed error messages with line numbers

**Exit Criteria:**
- Validates against official AKN 3.0 schema
- Returns detailed error messages
- Warnings for non-critical issues

---

### T-501: Write validation tests
**File:** `tests/test_akn_validator.py`

**Test Cases:**
- [ ] Valid AKN passes
- [ ] Invalid XML fails with message
- [ ] Missing required elements detected
- [ ] Invalid eId format detected

---

## Phase 6: End-to-End Testing

### T-600: End-to-end test with India Act
**Tasks:**
- [ ] Extract DPDP Act 2023 to Review JSON
- [ ] Verify citations have correct page numbers
- [ ] Generate HTML preview and verify
- [ ] Generate AKN from review
- [ ] Validate AKN against schema

**Exit Criteria:**
- Review JSON has valid citations
- HTML preview shows hierarchy correctly
- AKN validates against schema
- Chapter/Section structure correct

---

### T-601: End-to-end test with India Rules
**Tasks:**
- [ ] Extract DPDP Rules 2025 to Review JSON
- [ ] Verify rule/subrule citations
- [ ] Generate AKN and validate
- [ ] Verify rule -> section mapping

**Exit Criteria:**
- Rules mapped to `<section>`
- Subrules mapped to `<subsection>`
- Page numbers correct

---

### T-602: End-to-end test with Irish SI (3-level)
**Tasks:**
- [ ] Extract S.I. 81/2025 to Review JSON
- [ ] Verify part/chapter/regulation structure
- [ ] Generate AKN and validate

**Exit Criteria:**
- 3-level hierarchy correct
- Regulation mapped correctly

---

### T-603: End-to-end test with Irish SI (4-level)
**Tasks:**
- [ ] Extract S.I. 80/2025 to Review JSON
- [ ] Verify part/regulation/paragraph/subparagraph
- [ ] Generate AKN and validate

**Exit Criteria:**
- 4-level hierarchy correct
- Different structure from T-602 handled

---

### T-604: End-to-end test with Irish SI (5-level)
**Tasks:**
- [ ] Extract S.I. 607/2024 to Review JSON
- [ ] Verify all 5 levels have citations
- [ ] Generate AKN and validate

**Exit Criteria:**
- 5-level hierarchy correct
- Subregulation mapped to `<subsection>`

---

## Test Data Set

### Required Test PDFs

| # | Document | Jurisdiction | Type | Hierarchy | Status |
|---|----------|--------------|------|-----------|--------|
| 1 | DPDP Act 2023 | India | Act | chapter > section > subsection > clause > subclause | Available |
| 2 | DPDP Rules 2025 | India | Rules | rule > subrule > clause > subclause | Available |
| 3 | S.I. 81/2025 | Ireland | SI | part > chapter > regulation | Available |
| 4 | S.I. 80/2025 | Ireland | SI | part > regulation > paragraph > subparagraph | Available |
| 5 | S.I. 607/2024 | Ireland | SI | part > regulation > subregulation > paragraph > subparagraph | Available |
| 6 | UK Act (TBD) | UK | Act | part > chapter > section > subsection > paragraph | **Needed** |
| 7 | UK SI (TBD) | UK | SI | part > regulation > paragraph > subparagraph | **Needed** |
| 8 | EU Regulation (TBD) | EU | Regulation | title > chapter > article > paragraph > point | **Needed** |

### Download URLs

```bash
# India (Available)
data/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf  # DPDP Act 2023
data/meity_rules.pdf                         # DPDP Rules 2025

# Ireland (Available)
data/irish_si.pdf      # S.I. 81/2025
data/irish_si_80.pdf   # S.I. 80/2025
data/irish_si_607.pdf  # S.I. 607/2024

# UK (To be downloaded)
# Example: https://www.legislation.gov.uk/ukpga/2023/32/data.pdf

# EU (To be downloaded)
# Example: https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1114
```

### Test Data Checklist

- [x] India Act (DPDP 2023)
- [x] India Rules (DPDP Rules 2025)
- [x] Ireland SI 3-level (81/2025)
- [x] Ireland SI 4-level (80/2025)
- [x] Ireland SI 5-level (607/2024)
- [ ] UK Act - **Please provide URL**
- [ ] UK SI - **Please provide URL**
- [ ] EU Regulation - **Please provide URL**

---

## Test Matrix

### Unit Tests

| Test File | Test Case | Input | Expected Output |
|-----------|-----------|-------|-----------------|
| test_akn_mapper.py | test_native_element | "chapter" | ("chapter", True) |
| test_akn_mapper.py | test_native_element_case | "CHAPTER" | ("chapter", True) |
| test_akn_mapper.py | test_mapped_element | "regulation" | ("section", True) |
| test_akn_mapper.py | test_mapped_element | "subrule" | ("subsection", True) |
| test_akn_mapper.py | test_unknown_element | "xyz123" | ("xyz123", False) |
| test_akn_mapper.py | test_country_code | "India" | "in" |
| test_akn_mapper.py | test_country_code | "Ireland" | "ie" |
| test_akn_mapper.py | test_country_code | "Unknown" | "un" |
| test_dynamic_akn_generator.py | test_single_node | HierarchyNode(chapter) | `<chapter>...</chapter>` |
| test_dynamic_akn_generator.py | test_nested_nodes | chapter > section | `<chapter><section>...` |
| test_dynamic_akn_generator.py | test_hcontainer_fallback | "custom_type" | `<hcontainer name="custom_type">` |
| test_dynamic_akn_generator.py | test_eid_generation | chapter I, section 1 | eId="chp_i__sec_1" |
| test_dynamic_akn_generator.py | test_frbr_work | DocumentStructure | Valid FRBRWork element |
| test_dynamic_akn_generator.py | test_full_document | Structure + Nodes | Complete AKN XML |

### Integration Tests

| Test File | Test Case | Input PDF | Validations |
|-----------|-----------|-----------|-------------|
| test_e2e.py | test_india_act | DPDP Act 2023 | Schema valid, chapters present |
| test_e2e.py | test_india_rules | DPDP Rules 2025 | Schema valid, rules -> sections |
| test_e2e.py | test_ireland_si_3level | S.I. 81/2025 | Schema valid, 3-level hierarchy |
| test_e2e.py | test_ireland_si_4level | S.I. 80/2025 | Schema valid, 4-level hierarchy |
| test_e2e.py | test_ireland_si_5level | S.I. 607/2024 | Schema valid, 5-level hierarchy |

---

## Acceptance Criteria (Definition of Done)

### For Each Task:
- [ ] Code implemented
- [ ] Unit tests written and passing
- [ ] No type errors (mypy)
- [ ] Code reviewed

### For Complete Implementation:
- [ ] All 5 test PDFs convert successfully
- [ ] Review JSON has valid citations with page numbers
- [ ] HTML preview renders correctly
- [ ] All AKN outputs validate against schema
- [ ] CLI supports extract/generate/convert workflow
- [ ] Documentation updated

---

## Phase Summary

| Phase | Focus | Tasks | Complexity |
|-------|-------|-------|------------|
| Phase 0 | Line-Numbered Text Extraction | T-050, T-051 | Low |
| Phase 1 | Models & Mapper | T-100 to T-104 | Low |
| Phase 2 | Top-Down Recursive Extraction + Review | T-200 to T-205 | High |
| Phase 3 | AKN Generator | T-300, T-301 | Medium |
| Phase 4 | Integration & CLI | T-400, T-401 | Medium |
| Phase 5 | Validation | T-500, T-501 | Low |
| Phase 6 | E2E Testing | T-600 to T-604 | Low |

**Total Tasks:** 19 implementation + 5 E2E tests

---

## Dependencies

```
Phase 0 (Page Tracking)
    |
    v
Phase 1 (Models & Mapper)
    |
    +------------------+
    |                  |
    v                  v
Phase 2 (Review)    Phase 3 (Generator)
    |                  |
    +--------+---------+
             |
             v
      Phase 4 (Integration)
             |
             v
      Phase 5 (Validation)
             |
             v
      Phase 6 (E2E Testing)
```

---

## Workflow Summary

```
                    EXTRACTION (Top-Down)                    REVIEW                     GENERATION
               +----------------------------+          +------------------+          +------------------+
               |                            |          |                  |          |                  |
PDF ---------> | 1. Line-Numbered Text      | -------> | Review JSON      | -------> | AKN Generator    | -----> AKN XML
               | 2. Analyze Structure       |          | + HTML Preview   |          | (Approved nodes) |
               | 3. Extract Level 1 (LLM)   |          +------------------+          +------------------+
               | 4. For each L1, extract L2 |                  ^
               | 5. For each L2, extract L3 |                  |
               | 6. ... until leaf level    |           Human Validation
               +----------------------------+           (Annotation UI)

LEVEL-BY-LEVEL EXTRACTION:
+-----------+     +-------------+     +-------------+     +-------------+
|  Full     | --> | Level 1     | --> | Level 2     | --> | Level 3     | --> ...
|  Document |     | Parts       |     | Regulations |     | SubRegs     |
|  (1 call) |     | (1 call)    |     | (N calls)   |     | (M calls)   |
+-----------+     +-------------+     +-------------+     +-------------+
                        |                   |                   |
                        v                   v                   v
                  lines 1-800         lines 10-200        lines 15-50
                                      lines 201-500       lines 52-80
                                      lines 501-800       ...
```

---

## Next Steps

1. **You provide:** UK and EU test PDFs (optional, can add later)
2. **Start with:** Phase 0 (T-050 - Page tracking)
3. **TDD approach:** Write tests first, then implement
4. **Milestone 1:** Review JSON generation working (Phase 0-2)
5. **Milestone 2:** Full pipeline working (Phase 3-4)
6. **Milestone 3:** All tests passing (Phase 5-6)
