# Architecture: Universal Legal Document to Akoma Ntoso Converter

## 1. Problem Statement

Legal documents across jurisdictions use different hierarchical structures:

| Jurisdiction | Document Type | Hierarchy |
|--------------|---------------|-----------|
| India | Act | Chapter > Section > Subsection > Clause > Subclause |
| India | Rules | Rule > Subrule > Clause > Subclause |
| UK | Act | Part > Chapter > Section > Subsection > Paragraph |
| UK | Statutory Instrument | Part > Regulation > Paragraph > Subparagraph |
| Ireland | Statutory Instrument | Part > Chapter > Regulation OR Part > Regulation > Subregulation > Paragraph |
| EU | Directive/Regulation | Title > Chapter > Section > Article > Paragraph > Point |
| Australia | Act | Chapter > Part > Division > Subdivision > Section > Subsection > Paragraph |

**Challenge:** Build a single converter that handles ANY legal document from ANY jurisdiction without hardcoding structure.

---

## 2. Research Findings

### 2.1 Akoma Ntoso Native Elements

AKN provides ~310 element names. The hierarchical elements are:

**Higher Subdivisions (Containers):**
```
book > tome > part > title > chapter > division > section
```

**Basic Units (Provision Level):**
```
article, rule, paragraph, clause
```

**Lower Subdivisions (Nested):**
```
subsection > subparagraph > point > indent > alinea
```

**Key Finding:** AKN does NOT enforce element ordering. Any element can nest inside any other. This gives us flexibility.

### 2.2 The hcontainer Escape Hatch

For jurisdiction-specific terms not in AKN vocabulary:
```xml
<hcontainer name="subrule">
  <num>(1)</num>
  <content><p>...</p></content>
</hcontainer>
```

Use `hcontainer` ONLY when no native AKN element matches.

### 2.3 Mapping Strategy

| Extracted Type | AKN Native Element | Notes |
|----------------|-------------------|-------|
| part | `<part>` | Direct match |
| chapter | `<chapter>` | Direct match |
| title | `<title>` | Direct match |
| division | `<division>` | Direct match |
| section | `<section>` | Direct match |
| article | `<article>` | Direct match |
| rule | `<rule>` | Direct match (AKN has this!) |
| paragraph | `<paragraph>` | Direct match |
| clause | `<clause>` | Direct match |
| subsection | `<subsection>` | Direct match |
| subparagraph | `<subparagraph>` | Direct match |
| point | `<point>` | Direct match |
| indent | `<indent>` | Direct match |
| alinea | `<alinea>` | Direct match |
| regulation | `<section>` | Map to nearest equivalent |
| subrule | `<subsection>` | Map to nearest equivalent |
| subregulation | `<subsection>` | Map to nearest equivalent |
| subclause | `<point>` | Map to nearest equivalent |
| sub-subparagraph | `<indent>` | Map to nearest equivalent |
| *unknown* | `<hcontainer name="...">` | Fallback |

---

## 3. Architecture

### 3.1 High-Level Flow (with Human-in-the-Loop)

```
+-------+     +----------+     +------------+     +-------------+     +--------+     +-----------+
|       |     |          |     |            |     |             |     |        |     |           |
|  PDF  +---->+ Numbered +---->+ Structure  +---->+ Top-Down    +---->+ Review +---->+ AKN       |
|       |     | Text     |     | Analysis   |     | Extraction  |     | Stage  |     | Generator |
+-------+     +----------+     +------------+     +-------------+     +--------+     +-----------+
                  |                 |                   |                 |               |
                  v                 v                   v                 v               v
             Line Map +      hierarchy_types      Level-by-Level    Review JSON     AKN XML
             Page Map        ["part",             LLM Calls         + Preview
                              "regulation",
                              "subregulation"]
```

**Key Insight:** Extraction happens TOP-DOWN, one level at a time. Each level's extraction provides line ranges for the next level. This ensures accurate citations and manageable LLM context.

### 3.2 Core Extraction Technique: Line-Numbered Segmentation

Based on the [Instructor document segmentation pattern](https://python.useinstructor.com/examples/document_segmentation/):

1. **Prepend line numbers** to text - LLM can see and reference them
2. **LLM returns line ranges** in structured output - not content, just positions
3. **We extract content** using those line numbers - accurate citations guaranteed

```
Original:                     Numbered:
CHAPTER I                     1| CHAPTER I
PRELIMINARY                   2| PRELIMINARY
1. Short title...             3| 1. Short title...
(1) This Act...               4| (1) This Act...
```

### 3.3 Top-Down Recursive Extraction

**Why Top-Down?**
- Large documents don't fit in one LLM context
- Smaller focused tasks = higher accuracy
- Each level validates before going deeper
- Enables parallel extraction of siblings

**Extraction Flow:**

```
Step 1: Analyze Structure (1 LLM call)
        "What hierarchy levels exist?"
        -> ["part", "regulation", "subregulation", "paragraph"]

Step 2: Extract Level 1 (1 LLM call on full document)
        "Find all PARTS with their line ranges"
        -> Part I (lines 7-200), Part II (lines 201-400), Part III (lines 401-800)

Step 3: Extract Level 2 (N LLM calls, one per Part)
        For Part I (lines 7-200):
          "Find all REGULATIONS in lines 7-200"
          -> Reg 1 (10-50), Reg 2 (51-100), Reg 3 (101-200)
        For Part II (lines 201-400):
          "Find all REGULATIONS in lines 201-400"
          -> Reg 4 (205-300), ...

Step 4: Extract Level 3 (N LLM calls, one per Regulation)
        For Reg 1 (lines 10-50):
          "Find all SUBREGULATIONS in lines 10-50"
          -> (1) lines 12-20, (2) lines 21-35, (3) lines 36-50
        ...

Step 5: Continue until leaf level reached
```

**Parallel Extraction:**

```
Level 2 can run in parallel:
  +-> Extract Regs from Part I   --+
  +-> Extract Regs from Part II  --+--> Combine results
  +-> Extract Regs from Part III --+

Level 3 can run in parallel:
  +-> Extract SubRegs from Reg 1 --+
  +-> Extract SubRegs from Reg 2 --+--> Combine results
  +-> Extract SubRegs from Reg 3 --+
```

### 3.4 Data Models for Extraction

#### 3.4.1 Line Information (for citation tracking)

```python
class LineInfo(BaseModel):
    """Metadata for each line in the document."""
    line_num: int          # 1-indexed, sequential across document
    page: int              # PDF page number (from [PAGE:N] markers)
    text: str              # Actual line content
```

#### 3.4.2 Line-Numbered Extraction Flow

```python
def extract_with_line_info(pdf_path: str) -> tuple[List[LineInfo], str]:
    """
    Extract PDF with line numbers and page tracking.

    Uses existing extract_text(include_page_markers=True) which produces:
        [PAGE:1]
        CHAPTER I
        PRELIMINARY
        [PAGE:2]
        2. Definitions
        ...

    Parses [PAGE:N] markers to track current page, skips markers in output.

    Returns:
        line_infos: List of LineInfo (line_num, page, text)
        numbered_text: Formatted text for LLM ("  1| CHAPTER I\n  2| ...")
    """
    raw_text = extract_text(pdf_path, include_page_markers=True)

    line_infos = []
    line_num = 0
    current_page = 1

    for line in raw_text.split('\n'):
        # Track page from markers
        if line.startswith('[PAGE:'):
            current_page = int(line[6:-1])
            continue  # Skip marker line

        # Skip empty lines
        if not line.strip():
            continue

        line_num += 1
        line_infos.append(LineInfo(
            line_num=line_num,
            page=current_page,
            text=line
        ))

    numbered_text = format_numbered_text(line_infos)
    return line_infos, numbered_text
```

#### 3.4.3 Helper Functions

```python
def format_numbered_text(line_infos: List[LineInfo]) -> str:
    """Format lines with line numbers for LLM. E.g., '  1| CHAPTER I'"""
    max_width = len(str(line_infos[-1].line_num)) if line_infos else 1
    return '\n'.join(f"{li.line_num:>{max_width}}| {li.text}" for li in line_infos)

def get_lines_slice(line_infos: List[LineInfo], start: int, end: int) -> str:
    """Get numbered text for a line range (for level extraction)."""
    subset = [li for li in line_infos if start <= li.line_num <= end]
    return format_numbered_text(subset)

def get_content(line_infos: List[LineInfo], start: int, end: int) -> str:
    """Get raw content for a line range (for leaf nodes)."""
    subset = [li for li in line_infos if start <= li.line_num <= end]
    return '\n'.join(li.text for li in subset)

def get_page_for_line(line_infos: List[LineInfo], line_num: int) -> int:
    """Get PDF page number for a specific line."""
    for li in line_infos:
        if li.line_num == line_num:
            return li.page
    return 1
```

#### 3.4.4 Segment (LLM output for one level)

```python
class Segment(BaseModel):
    """A segment found at one level - returned by LLM."""
    type: str              # "part", "regulation", etc.
    number: str            # "I", "1", "(a)"
    title: Optional[str]   # Heading text if present
    start_line: int        # Line number where this starts
    end_line: int          # Line number where this ends


class LevelExtraction(BaseModel):
    """All segments found at one level - LLM structured output."""
    segments: List[Segment]
```

#### 3.4.5 Extraction Prompt Template

```python
LEVEL_EXTRACTION_PROMPT = """
Analyze this section of a legal document and find all {element_type} elements.

The text has line numbers prefixed (e.g., "  42| Section 5...").

For each {element_type} found, provide:
- type: "{element_type}"
- number: The identifier (e.g., "I", "1", "(a)")
- title: The heading text if present (null if none)
- start_line: Line number where this {element_type} STARTS
- end_line: Line number where this {element_type} ENDS (before next element or section end)

Rules:
- Use the LINE NUMBERS shown (left of the "|" character)
- Segments must not overlap
- Segments must cover lines {start_line} to {end_line}
- Return segments in order of appearance

TEXT (lines {start_line} to {end_line}):
{text_slice}
"""
```

#### 3.4.6 Recursive Extraction Function

```python
def extract_hierarchy(
    numbered_text: str,
    line_map: Dict[int, LineInfo],
    hierarchy_types: List[str],
    start_line: int,
    end_line: int,
    current_level: int = 0
) -> List[HierarchyNode]:
    """
    Recursively extract hierarchy, one level at a time.
    """
    if current_level >= len(hierarchy_types):
        return []  # Reached leaf level

    element_type = hierarchy_types[current_level]

    # LLM call for THIS level only
    text_slice = get_lines(numbered_text, start_line, end_line)
    extraction = llm_extract_level(text_slice, element_type, start_line, end_line)

    nodes = []
    for seg in extraction.segments:
        node = HierarchyNode(
            id=str(uuid4()),
            level=current_level + 1,
            type=seg.type,
            number=seg.number,
            title=seg.title,
            citation=build_citation(seg, line_map),
            children=[]
        )

        # RECURSE into this segment's range
        node.children = extract_hierarchy(
            numbered_text,
            line_map,
            hierarchy_types,
            start_line=seg.start_line,
            end_line=seg.end_line,
            current_level=current_level + 1
        )

        # If leaf node, extract content
        if not node.children:
            node.content = get_content(numbered_text, seg.start_line, seg.end_line)

        nodes.append(node)

    return nodes
```

---

### 3.5 Human-in-the-Loop Review Stage

#### 3.5.1 Purpose
- Validate LLM extraction accuracy before committing to AKN
- Enable annotation UI for corrections
- Provide audit trail with source citations
- Support iterative refinement

#### 3.5.2 Review Data Model

```python
class SourceCitation(BaseModel):
    """Links extracted content back to source PDF."""
    page: int                      # PDF page number (1-indexed)
    start_char: Optional[int]      # Character offset in extracted text
    end_char: Optional[int]        # Character offset end
    start_line: Optional[int]      # Line number in extracted text
    end_line: Optional[int]        # Line number end
    snippet: Optional[str]         # Short excerpt for context (50 chars)


class HierarchyNode(BaseModel):
    """A node in the document hierarchy with source tracking."""
    # Identity
    id: str                        # Unique ID (UUID) for annotation reference
    level: int                     # 1 = top, 2 = child, etc.
    type: str                      # "chapter", "section", "rule", etc.
    number: str                    # "I", "1", "(a)", etc.

    # Content
    title: Optional[str]           # Heading text
    content: Optional[str]         # Leaf node content

    # Source Citation (NEW)
    citation: SourceCitation       # Where this was found in PDF

    # Validation State (NEW)
    confidence: float              # LLM confidence score (0.0 - 1.0)
    status: str                    # "pending", "approved", "rejected", "modified"
    reviewer_notes: Optional[str]  # Human reviewer comments

    # Hierarchy
    children: List[HierarchyNode]
    parent_id: Optional[str]       # Reference to parent node ID


class ReviewDocument(BaseModel):
    """Complete document ready for human review."""
    # Metadata
    id: str                        # Document UUID
    source_pdf: str                # Original PDF path
    extracted_at: datetime         # Extraction timestamp

    # Structure
    structure: DocumentStructure   # Document type, jurisdiction, etc.
    nodes: List[HierarchyNode]     # Extracted hierarchy with citations

    # Review State
    status: str                    # "pending_review", "in_review", "approved", "rejected"
    reviewer: Optional[str]        # Who is reviewing
    reviewed_at: Optional[datetime]

    # Statistics
    total_nodes: int
    nodes_by_level: Dict[int, int]
    avg_confidence: float
```

#### 3.5.3 Review JSON Output

The extractor outputs a JSON file for review before AKN generation:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_pdf": "data/dpdp_act_2023.pdf",
  "extracted_at": "2025-12-27T10:30:00Z",
  "status": "pending_review",
  "structure": {
    "document_type": "act",
    "jurisdiction": "India",
    "hierarchy_types": ["chapter", "section", "subsection", "clause"],
    "title": "The Digital Personal Data Protection Act, 2023",
    "enactment_date": "2023-08-11",
    "number": "No. 22 of 2023"
  },
  "nodes": [
    {
      "id": "node-001",
      "level": 1,
      "type": "chapter",
      "number": "I",
      "title": "PRELIMINARY",
      "content": null,
      "citation": {
        "page": 2,
        "start_line": 45,
        "end_line": 120,
        "snippet": "CHAPTER I PRELIMINARY 1. Short title..."
      },
      "confidence": 0.95,
      "status": "pending",
      "reviewer_notes": null,
      "children": [
        {
          "id": "node-002",
          "level": 2,
          "type": "section",
          "number": "1",
          "title": "Short title and commencement",
          "content": null,
          "citation": {
            "page": 2,
            "start_line": 47,
            "end_line": 55,
            "snippet": "1. Short title and commencement.-(1)..."
          },
          "confidence": 0.98,
          "status": "pending",
          "children": [
            {
              "id": "node-003",
              "level": 3,
              "type": "subsection",
              "number": "(1)",
              "title": null,
              "content": "This Act may be called the Digital Personal Data Protection Act, 2023.",
              "citation": {
                "page": 2,
                "start_line": 48,
                "end_line": 49,
                "snippet": "(1) This Act may be called the Digital..."
              },
              "confidence": 0.99,
              "status": "pending",
              "children": []
            }
          ]
        }
      ]
    }
  ],
  "statistics": {
    "total_nodes": 245,
    "nodes_by_level": {
      "1": 8,
      "2": 45,
      "3": 120,
      "4": 72
    },
    "avg_confidence": 0.94
  }
}
```

#### 3.5.4 Annotation UI Requirements (Future)

The Review JSON enables a future annotation UI with:

| Feature | Description |
|---------|-------------|
| **Side-by-side view** | PDF viewer + extracted hierarchy |
| **Click-to-locate** | Click node -> highlight in PDF |
| **Confidence indicators** | Color-coded by LLM confidence |
| **Approve/Reject buttons** | Per-node validation |
| **Edit capability** | Modify type, number, title, content |
| **Add/Delete nodes** | Fix missing or extra extractions |
| **Bulk approve** | Approve all high-confidence nodes |
| **Export approved** | Generate AKN from approved nodes only |

#### 3.5.5 Review Workflow

```
1. EXTRACT
   PDF -> LLM Extraction -> Review JSON

2. REVIEW (Human-in-the-Loop)
   Review JSON -> Annotation UI -> Validated JSON

   Actions:
   - Approve node (status: "approved")
   - Reject node (status: "rejected", with notes)
   - Modify node (status: "modified", update fields)
   - Add missing node
   - Delete incorrect node

3. GENERATE
   Validated JSON (approved nodes only) -> AKN XML
```

#### 3.5.6 Page Number Extraction

To populate `citation.page`, we need to track page boundaries during PDF extraction:

```python
class PageAwareExtractor:
    """Extract text while tracking page numbers."""

    def extract_with_pages(self, pdf_path: str) -> tuple[str, Dict[int, tuple[int, int]]]:
        """
        Returns:
            text: Full extracted text
            page_map: {page_num: (start_char, end_char)} mapping
        """
        import fitz
        doc = fitz.open(pdf_path)

        full_text = ""
        page_map = {}

        for page_num, page in enumerate(doc, 1):
            start_char = len(full_text)
            page_text = page.get_text()
            full_text += page_text
            end_char = len(full_text)
            page_map[page_num] = (start_char, end_char)

        return full_text, page_map

    def find_page(self, char_position: int, page_map: Dict[int, tuple[int, int]]) -> int:
        """Find which page a character position belongs to."""
        for page_num, (start, end) in page_map.items():
            if start <= char_position < end:
                return page_num
        return 1  # Default to first page
```

#### 3.5.7 Confidence Scoring

LLM provides confidence based on extraction clarity:

```python
class ConfidenceFactors:
    """Factors affecting extraction confidence."""

    CLEAR_NUMBERING = 0.2      # "CHAPTER I" vs ambiguous
    CLEAR_HEADING = 0.2        # Has distinct heading
    STANDARD_STRUCTURE = 0.2   # Follows expected hierarchy
    CONTENT_COMPLETE = 0.2     # Full content extracted
    NO_OCR_ERRORS = 0.2        # Clean text, no artifacts

    # Total: 1.0 max confidence
```

### 3.6 AKN Generation Components

#### 3.6.1 PDF Extractor (Existing)
- Input: PDF file path
- Output: Raw text
- Technology: PyMuPDF (fitz)

#### 3.6.2 Dynamic Structure Analyzer
- Input: Raw text (first 2000 chars)
- Output: `DocumentStructure`
- Technology: Claude API with structured outputs

```python
class DocumentStructure(BaseModel):
    document_type: str      # "act", "rules", "regulation", etc.
    jurisdiction: str       # "India", "Ireland", "UK", etc.
    hierarchy_types: List[str]  # ["chapter", "section", "subsection", ...]
    title: str
    enactment_date: Optional[str]
    number: Optional[str]
```

#### 3.6.3 Dynamic Hierarchy Extractor
- Input: Full text + DocumentStructure
- Output: List[HierarchyNode]
- Technology: Claude API with structured outputs

```python
class HierarchyNode(BaseModel):
    level: int              # 1 = top, 2 = child, etc.
    type: str               # "chapter", "section", "rule", etc.
    number: str             # "I", "1", "(a)", etc.
    title: Optional[str]    # Heading text
    content: Optional[str]  # Leaf node content
    children: List[HierarchyNode]
```

#### 3.6.4 AKN Element Mapper
- Input: HierarchyNode.type (string)
- Output: AKN element name + whether native or hcontainer
- Technology: Rule-based mapping

```python
class AKNElementMapper:
    """Maps extracted types to AKN elements."""

    # Native AKN elements (use directly)
    NATIVE_ELEMENTS = {
        'part', 'chapter', 'title', 'division', 'section',
        'article', 'rule', 'paragraph', 'clause',
        'subsection', 'subparagraph', 'point', 'indent', 'alinea'
    }

    # Jurisdiction-specific -> AKN native mappings
    MAPPINGS = {
        'regulation': 'section',
        'subrule': 'subsection',
        'subregulation': 'subsection',
        'subclause': 'point',
        'sub-subparagraph': 'indent',
    }

    def map(self, node_type: str) -> tuple[str, bool]:
        """
        Returns (element_name, is_native).
        If is_native=False, use hcontainer with name attribute.
        """
        normalized = node_type.lower().strip()

        # Direct native match
        if normalized in self.NATIVE_ELEMENTS:
            return normalized, True

        # Mapped to native
        if normalized in self.MAPPINGS:
            return self.MAPPINGS[normalized], True

        # Fallback to hcontainer
        return node_type, False
```

#### 3.6.5 AKN XML Generator
- Input: DocumentStructure + List[HierarchyNode]
- Output: Valid AKN 3.0 XML string
- Technology: lxml

```python
def generate_node_xml(node: HierarchyNode, mapper: AKNElementMapper) -> Element:
    element_name, is_native = mapper.map(node.type)

    if is_native:
        elem = Element(element_name)
    else:
        elem = Element('hcontainer', name=element_name)

    # Add num, heading, content
    if node.number:
        SubElement(elem, 'num').text = node.number
    if node.title:
        SubElement(elem, 'heading').text = node.title
    if node.content:
        content = SubElement(elem, 'content')
        SubElement(content, 'p').text = node.content

    # Recursively add children
    for child in node.children:
        elem.append(generate_node_xml(child, mapper))

    return elem
```

### 3.7 Data Flow Example

**Input:** Irish S.I. 607/2024 (Crypto-Assets)

**Step 1: Structure Analysis**
```json
{
  "document_type": "statutory instrument",
  "jurisdiction": "Ireland",
  "hierarchy_types": ["part", "regulation", "subregulation", "paragraph", "subparagraph"],
  "title": "European Union (Markets in Crypto-Assets) Regulations 2024",
  "number": "S.I. No. 607 of 2024"
}
```

**Step 2: Hierarchy Extraction**
```
HierarchyNode(level=1, type="part", number="I", title="PRELIMINARY AND GENERAL")
  HierarchyNode(level=2, type="regulation", number="1", title="Citation and commencement")
    HierarchyNode(level=3, type="subregulation", number="(1)", content="These Regulations...")
    HierarchyNode(level=3, type="subregulation", number="(2)", content="These Regulations shall...")
```

**Step 3: AKN Mapping**
```
part -> <part> (native)
regulation -> <section> (mapped)
subregulation -> <subsection> (mapped)
paragraph -> <paragraph> (native)
subparagraph -> <subparagraph> (native)
```

**Step 4: XML Output**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="EuropeanUnionMarketsinCryptoAssetsRegulations2024">
    <meta>
      <identification source="#source">
        <FRBRWork>
          <FRBRthis value="/ie/act/2024/SI607/main"/>
          <FRBRuri value="/ie/act/2024/SI607"/>
          <FRBRcountry value="ie"/>
          <FRBRdate date="2024-11-08" name="enacted"/>
          <FRBRnumber value="S.I. No. 607 of 2024"/>
          <FRBRname value="European Union (Markets in Crypto-Assets) Regulations 2024"/>
        </FRBRWork>
        ...
      </identification>
    </meta>
    <body>
      <part eId="part_i">
        <num>I</num>
        <heading>PRELIMINARY AND GENERAL</heading>
        <section eId="part_i__sec_1">
          <num>1</num>
          <heading>Citation and commencement</heading>
          <subsection eId="part_i__sec_1__subsec_1">
            <num>(1)</num>
            <content>
              <p>These Regulations may be cited as the European Union (Markets in Crypto-Assets) Regulations 2024.</p>
            </content>
          </subsection>
          <subsection eId="part_i__sec_1__subsec_2">
            <num>(2)</num>
            <content>
              <p>These Regulations shall come into operation on 8 November 2024.</p>
            </content>
          </subsection>
        </section>
      </part>
    </body>
  </act>
</akomaNtoso>
```

---

## 4. Module Structure

```
src/
  extractor/
    pdf_extractor.py          # PDF to text with page tracking
    text_cleaner.py           # LLM-based cleaning (existing)

  parser/
    dynamic_extractor.py      # Structure analysis + hierarchy extraction
    llm_client.py             # Claude API client (existing)

  models/
    hierarchy.py              # HierarchyNode, DocumentStructure
    citation.py               # SourceCitation model
    review.py                 # ReviewDocument, validation states

  review/
    review_exporter.py        # Export extraction to Review JSON
    review_importer.py        # Import validated Review JSON
    html_preview.py           # Generate HTML preview for review

  generator/
    akn_mapper.py             # Type to AKN element mapping
    dynamic_akn_generator.py  # Universal AKN XML generator

  validator/
    akn_validator.py          # AKN schema validation

  pipeline.py                 # Unified conversion pipeline

output/
  reviews/                    # Review JSON files
    {doc_id}_review.json
  previews/                   # HTML preview files
    {doc_id}_preview.html
  akn/                        # Final AKN XML files
    {doc_id}.xml
```

---

## 5. Extension Points

### 5.1 Adding New Jurisdiction Mappings

Edit `AKNElementMapper.MAPPINGS`:
```python
MAPPINGS = {
    # Existing
    'regulation': 'section',
    'subrule': 'subsection',

    # New jurisdiction support
    'artikel': 'article',      # German
    'paragraf': 'paragraph',   # Swedish
    'articulo': 'article',     # Spanish
}
```

### 5.2 Adding New Native Elements

If AKN adds new elements in future versions:
```python
NATIVE_ELEMENTS = {
    'part', 'chapter', ...,
    'new_element',  # Add here
}
```

### 5.3 Custom hcontainer Handling

For specific jurisdictions requiring custom handling:
```python
class JurisdictionHandler:
    def process(self, node: HierarchyNode) -> HierarchyNode:
        """Override for jurisdiction-specific processing."""
        return node

class IndiaActHandler(JurisdictionHandler):
    def process(self, node: HierarchyNode) -> HierarchyNode:
        # India-specific transformations
        return node
```

---

## 6. Validation Strategy

### 6.1 Schema Validation
- Validate output against AKN 3.0 XSD schema
- Use `lxml.etree.XMLSchema` for validation

### 6.2 Semantic Validation
- Verify FRBR URIs are well-formed
- Check eId uniqueness
- Validate date formats

### 6.3 Round-Trip Testing
- Extract -> Generate -> Re-extract
- Compare structures for consistency

---

## 7. References

- [Akoma Ntoso OASIS Specification](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html)
- [AKN4UN Guidelines](https://unsceb-hlcm.github.io/part1/index-54.html)
- [UK Legislation Structure](https://www.legislation.gov.uk/understanding-legislation)
- [Australian Legislation Structure](https://www.legislation.gov.au/help-and-resources/understanding-legislation/structure-of-a-law)
- [EUR-Lex Joint Practical Guide](https://eur-lex.europa.eu/content/techleg/KB0213228ENN.pdf)
