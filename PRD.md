# Product Requirements Document (PRD)
# Indian Acts to Akoma Ntoso Converter

**Version:** 1.0
**Date:** 2024-12-23
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Problem Statement

Legal documents in India (Acts, Bills, Regulations) are published as PDFs in the Gazette of India. These documents are:
- Difficult to search and cross-reference
- Not machine-readable
- Hard to track amendments and changes
- Inaccessible for legal tech applications

### 1.2 Solution

Build a semi-automated tool that converts Indian Parliamentary Acts from PDF format to Akoma Ntoso (LegalDocML) - an international XML standard for legal documents. This enables:
- Structured, searchable legal content
- Machine-readable format for legal tech applications
- Standardized representation for cross-referencing
- Foundation for legal knowledge graphs and AI applications

### 1.3 Success Metrics

| Metric | Target |
|--------|--------|
| Conversion accuracy | >95% structural elements correctly identified |
| Human review time | <30 minutes per Act |
| Processing time | <5 minutes per Act (excluding human review) |
| XML validity | 100% valid Akoma Ntoso 3.0 schema |

---

## 2. Scope

### 2.1 In Scope (MVP)

- Convert Indian Parliamentary Acts (PDF) to Akoma Ntoso XML
- Support DPDP Act 2023 as primary test case
- Extract document structure (Chapters, Sections, Sub-sections, Clauses)
- Extract metadata (Title, Act Number, Year, Date)
- Identify special elements (Definitions, Illustrations, Provisos, Explanations)
- CLI interface for conversion
- Human review workflow with confidence markers

### 2.2 Out of Scope (MVP)

- Web-based user interface
- Bills, Ordinances, Judgments (different structure)
- Other jurisdictions (UK, USA, EU)
- Amendment tracking and consolidation
- Real-time API service
- User authentication and multi-tenancy

### 2.3 Future Scope

- Support for additional document types
- Multi-jurisdiction support
- Web UI for review and editing
- Batch processing API
- Integration with legal databases

---

## 3. User Personas

### 3.1 Primary: Legal Data Engineer

**Name:** Priya
**Role:** Legal Technology Specialist
**Goals:**
- Convert large volumes of legal documents to structured format
- Build legal knowledge bases and search systems
- Ensure accuracy of converted documents

**Pain Points:**
- Manual conversion is time-consuming
- Existing tools don't handle Indian legal document formats
- Need to verify conversion accuracy

**Needs:**
- Automated conversion with high accuracy
- Clear indication of uncertain conversions
- Ability to review and correct errors efficiently

### 3.2 Secondary: Legal Researcher

**Name:** Amit
**Role:** Policy Researcher
**Goals:**
- Analyze legal documents programmatically
- Cross-reference provisions across Acts
- Track changes in legislation

**Needs:**
- Clean, structured output
- Consistent element identification
- Valid XML for downstream processing

---

## 4. User Stories

### 4.1 Core Conversion

```
US-001: Basic PDF Conversion
As a Legal Data Engineer
I want to convert an Indian Act PDF to Akoma Ntoso XML
So that I can use the document in legal tech applications

Acceptance Criteria:
- Given a valid Indian Act PDF
- When I run the convert command
- Then I receive a valid Akoma Ntoso XML file
- And the XML contains all chapters and sections from the PDF
- And the XML passes schema validation
```

```
US-002: Metadata Extraction
As a Legal Data Engineer
I want the tool to extract document metadata automatically
So that I don't have to manually enter basic information

Acceptance Criteria:
- Given an Indian Act PDF
- When conversion completes
- Then the XML contains correct:
  - Act title
  - Act number
  - Year of enactment
  - Date of enactment
  - Publication details
```

```
US-003: Structure Recognition
As a Legal Data Engineer
I want the tool to identify document hierarchy
So that the XML accurately represents the Act's structure

Acceptance Criteria:
- Given an Act with multiple chapters
- When conversion completes
- Then each chapter is correctly identified with number and title
- And sections are nested within correct chapters
- And sub-sections, clauses, sub-clauses are properly nested
```

### 4.2 Special Elements

```
US-004: Definition Extraction
As a Legal Researcher
I want definitions to be marked in the XML
So that I can build a glossary of legal terms

Acceptance Criteria:
- Given an Act with a Definitions section
- When conversion completes
- Then each definition term is identified
- And the definition text is associated with the term
- And definitions are tagged with appropriate AKN elements
```

```
US-005: Cross-Reference Identification
As a Legal Researcher
I want references to other sections/Acts to be identified
So that I can build a reference graph

Acceptance Criteria:
- Given text containing "section 14 of the Telecom Act, 1997"
- When conversion completes
- Then the reference is tagged as a cross-reference
- And the target section/Act is identified where possible
```

```
US-006: Special Elements
As a Legal Data Engineer
I want Illustrations, Explanations, and Provisos to be identified
So that the XML captures the full semantic structure

Acceptance Criteria:
- Illustrations are tagged and associated with parent section
- Explanations are tagged appropriately
- Provisos are identified and nested correctly
```

### 4.3 Human Review

```
US-007: Confidence Markers
As a Legal Data Engineer
I want to see confidence scores for parsed elements
So that I can focus review on uncertain areas

Acceptance Criteria:
- Given a converted document
- When there is parsing uncertainty
- Then the XML contains review comments
- And comments indicate what needs verification
```

```
US-008: Preview Mode
As a Legal Data Engineer
I want to preview the structure before full conversion
So that I can verify the tool understands the document

Acceptance Criteria:
- Given a PDF file
- When I run preview command
- Then I see the detected structure (chapters, sections)
- And I see any warnings or issues
- And no XML file is created
```

### 4.4 Validation

```
US-009: Schema Validation
As a Legal Data Engineer
I want to validate generated XML against AKN schema
So that I can ensure interoperability

Acceptance Criteria:
- Given a generated XML file
- When I run validate command
- Then I see validation results
- And any schema violations are clearly reported
```

---

## 5. Functional Requirements

### 5.1 PDF Extraction

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | Extract text from PDF preserving reading order | Must |
| FR-002 | Handle multi-column layouts | Must |
| FR-003 | Detect and extract marginal notes | Should |
| FR-004 | Handle Hindi/bilingual content gracefully | Should |
| FR-005 | Remove headers, footers, page numbers | Must |

### 5.2 Structure Parsing

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-010 | Identify Act title and number | Must |
| FR-011 | Identify chapter boundaries and titles | Must |
| FR-012 | Identify section numbers and headings | Must |
| FR-013 | Parse sub-sections (1), (2), etc. | Must |
| FR-014 | Parse clauses (a), (b), etc. | Must |
| FR-015 | Parse sub-clauses (i), (ii), etc. | Must |
| FR-016 | Identify Preamble | Must |
| FR-017 | Identify Enacting Formula | Should |
| FR-018 | Identify Schedules/Annexures | Must |

### 5.3 Semantic Elements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-020 | Identify and tag definitions | Must |
| FR-021 | Identify and tag illustrations | Must |
| FR-022 | Identify and tag explanations | Must |
| FR-023 | Identify and tag provisos | Must |
| FR-024 | Identify cross-references to sections | Should |
| FR-025 | Identify cross-references to other Acts | Should |

### 5.4 XML Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-030 | Generate valid Akoma Ntoso 3.0 XML | Must |
| FR-031 | Generate FRBR identification metadata | Must |
| FR-032 | Generate proper eId attributes for all elements | Must |
| FR-033 | Include publication metadata | Should |
| FR-034 | Generate human-readable XML (proper indentation) | Should |

### 5.5 CLI Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-040 | `convert` command: PDF to XML | Must |
| FR-041 | `validate` command: Check XML against schema | Should |
| FR-042 | `preview` command: Show detected structure | Should |
| FR-043 | `--verbose` flag: Detailed logging | Should |
| FR-044 | `--output` flag: Specify output path | Must |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | PDF extraction time | <30 seconds for 50-page Act |
| NFR-002 | LLM parsing time | <3 minutes per Act |
| NFR-003 | XML generation time | <5 seconds |
| NFR-004 | Memory usage | <500MB for typical Act |

### 6.2 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-010 | Conversion success rate | >99% (no crashes) |
| NFR-011 | Structural accuracy | >95% elements correct |
| NFR-012 | Graceful error handling | Clear error messages |

### 6.3 Maintainability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-020 | Test coverage | >80% code coverage |
| NFR-021 | Code documentation | All public functions documented |
| NFR-022 | Modular architecture | Easy to add new jurisdictions |

### 6.4 Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-030 | API key protection | Keys in .env, not in code |
| NFR-031 | No data persistence | PDFs not stored after processing |

---

## 7. Technical Architecture

### 7.1 High-Level Architecture

```
+-------------+     +---------------+     +-------------+     +---------------+
|   PDF       | --> |   Extractor   | --> |   Parser    | --> |   Generator   |
|   Input     |     |   (pdfplumber)|     |   (Claude)  |     |   (lxml)      |
+-------------+     +---------------+     +-------------+     +---------------+
                                                                      |
                                                                      v
                                                              +---------------+
                                                              |   AKN XML     |
                                                              |   Output      |
                                                              +---------------+
```

### 7.2 Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Extractor | PDF to text with layout | pdfplumber |
| Cleaner | Normalize text, remove noise | Python |
| Parser | Structure recognition | Claude API |
| Models | Document data structures | Python dataclasses |
| Generator | XML output | lxml |
| CLI | User interface | click |

### 7.3 LLM Integration

**Model:** Claude API (claude-sonnet-4-20250514 or similar)

**Usage Points:**
1. Metadata extraction from first pages
2. Document structure identification (chapters, sections)
3. Section content parsing (sub-sections, clauses)
4. Semantic element detection (definitions, illustrations)

**Prompt Management:**
- Prompts stored as separate text files
- Easy to iterate and improve
- Version controlled

---

## 8. Data Models

### 8.1 ActDocument

```python
@dataclass
class ActDocument:
    # Identification
    title: str                    # "THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023"
    short_title: Optional[str]    # "DPDP Act"
    act_number: int               # 22
    year: int                     # 2023

    # Dates
    date_enacted: Optional[date]  # 2023-08-11
    date_published: Optional[date]

    # Content
    preamble: Optional[str]
    enacting_formula: Optional[str]
    chapters: List[Chapter]
    schedules: List[Schedule]

    # Metadata
    jurisdiction: str = "in"      # India
    language: str = "en"
```

### 8.2 Chapter

```python
@dataclass
class Chapter:
    number: str          # "I", "II", "III"
    title: str           # "PRELIMINARY"
    sections: List[Section]
```

### 8.3 Section

```python
@dataclass
class Section:
    number: int                      # 1, 2, 3
    heading: Optional[str]           # "Short title and commencement"
    content: Optional[str]           # Direct content (if no subsections)
    subsections: List[SubSection]
    provisos: List[Proviso]
    explanations: List[Explanation]
    illustrations: List[Illustration]
```

### 8.4 SubSection, Clause, SubClause

```python
@dataclass
class SubSection:
    number: int                  # 1, 2, 3
    content: str
    clauses: List[Clause]

@dataclass
class Clause:
    letter: str                  # "a", "b", "c"
    content: str
    subclauses: List[SubClause]

@dataclass
class SubClause:
    numeral: str                 # "i", "ii", "iii" or "A", "B"
    content: str
```

---

## 9. Akoma Ntoso Output Format

### 9.1 Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="DigitalPersonalDataProtection">

    <!-- Metadata -->
    <meta>
      <identification source="#source">
        <FRBRWork>
          <FRBRthis value="/in/act/2023/22/main"/>
          <FRBRuri value="/in/act/2023/22"/>
          <FRBRcountry value="in"/>
          <FRBRdate date="2023-08-11" name="enacted"/>
          <FRBRnumber value="22"/>
          <FRBRname value="Digital Personal Data Protection Act"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/in/act/2023/22/eng@2023-08-11/main"/>
          <FRBRuri value="/in/act/2023/22/eng@2023-08-11"/>
          <FRBRdate date="2023-08-11" name="publication"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/in/act/2023/22/eng@2023-08-11/main.xml"/>
          <FRBRuri value="/in/act/2023/22/eng@2023-08-11/main.xml"/>
          <FRBRdate date="2024-12-23" name="transform"/>
        </FRBRManifestation>
      </identification>
      <publication date="2023-08-11" name="Gazette of India" number="25"/>
    </meta>

    <!-- Preamble -->
    <preamble>
      <p>An Act to provide for the processing of digital personal data...</p>
    </preamble>

    <!-- Body -->
    <body>
      <chapter eId="chp_I">
        <num>CHAPTER I</num>
        <heading>PRELIMINARY</heading>

        <section eId="sec_1">
          <num>1.</num>
          <heading>Short title and commencement.</heading>

          <subsection eId="sec_1__subsec_1">
            <num>(1)</num>
            <content>
              <p>This Act may be called the Digital Personal Data Protection Act, 2023.</p>
            </content>
          </subsection>

          <subsection eId="sec_1__subsec_2">
            <num>(2)</num>
            <content>
              <p>It shall come into force on such date...</p>
            </content>
          </subsection>
        </section>

        <section eId="sec_2">
          <num>2.</num>
          <heading>Definitions.</heading>

          <intro>
            <p>In this Act, unless the context otherwise requires,--</p>
          </intro>

          <paragraph eId="sec_2__para_a">
            <num>(a)</num>
            <content>
              <p>"<def refersTo="#appellate_tribunal">Appellate Tribunal</def>" means...</p>
            </content>
          </paragraph>
        </section>
      </chapter>
    </body>

    <!-- Schedules -->
    <attachments>
      <attachment>
        <doc name="schedule">
          <mainBody>
            <p>THE SCHEDULE</p>
            <!-- Schedule content -->
          </mainBody>
        </doc>
      </attachment>
    </attachments>

  </act>
</akomaNtoso>
```

### 9.2 Element ID Convention

| Element | Pattern | Example |
|---------|---------|---------|
| Chapter | `chp_{number}` | `chp_I`, `chp_II` |
| Section | `sec_{number}` | `sec_1`, `sec_2` |
| SubSection | `sec_{s}__subsec_{n}` | `sec_1__subsec_1` |
| Clause | `sec_{s}__subsec_{n}__cla_{l}` | `sec_2__subsec_1__cla_a` |
| SubClause | `...__subcla_{r}` | `sec_2__subsec_1__cla_a__subcla_i` |

---

## 10. Testing Strategy

### 10.1 Test Pyramid

```
         /\
        /  \       E2E Tests (1-2)
       /----\      - Full pipeline with DPDP Act
      /      \
     /--------\    Integration Tests (5-10)
    /          \   - Extractor + Cleaner
   /------------\  - Parser + Generator
  /              \
 /----------------\ Unit Tests (50+)
                    - Each function tested
                    - Edge cases covered
```

### 10.2 Test Categories

| Category | Purpose | Tools |
|----------|---------|-------|
| Unit | Test individual functions | pytest |
| Integration | Test component interactions | pytest |
| E2E | Full pipeline validation | pytest |
| Schema | Validate XML output | lxml + AKN schema |
| Golden | Compare against known-good output | pytest |

### 10.3 Test Data

**Primary Test Case:** DPDP Act 2023
- 21 pages
- 9 chapters
- 44 sections
- 1 schedule
- Multiple definitions, illustrations, provisos

---

## 11. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM parsing inconsistency | Medium | Medium | Structured prompts, validation, human review |
| PDF layout variations | High | High | Test with multiple Acts, fallback strategies |
| API rate limits/costs | Medium | Low | Caching, batching, cost monitoring |
| Schema compliance issues | Medium | Low | Validation at generation time |
| Hindi content handling | Low | High | Skip/mark for manual review |

---

## 12. Implementation Phases

### Phase 1: Foundation (Sprint 1)
- Project setup
- PDF extraction
- Text cleaning
- Basic tests

### Phase 2: Core Parsing (Sprint 2)
- Document models
- Claude API integration
- Metadata extraction
- Structure parsing

### Phase 3: XML Generation (Sprint 3)
- Akoma Ntoso generator
- Schema validation
- CLI interface

### Phase 4: Polish (Sprint 4)
- E2E testing with DPDP Act
- Human review workflow
- Documentation
- Bug fixes

---

## 13. Dependencies

### 13.1 External Services

| Service | Purpose | Fallback |
|---------|---------|----------|
| Claude API | Structure parsing | Manual parsing |

### 13.2 Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pdfplumber | >=0.9.0 | PDF extraction |
| lxml | >=4.9.0 | XML generation |
| anthropic | >=0.18.0 | Claude API client |
| click | >=8.0.0 | CLI framework |
| rich | >=13.0.0 | Terminal output |
| pytest | >=7.0.0 | Testing |
| python-dotenv | >=1.0.0 | Environment management |

---

## 14. Glossary

| Term | Definition |
|------|------------|
| Akoma Ntoso | XML standard for legislative documents (OASIS LegalDocML) |
| FRBR | Functional Requirements for Bibliographic Records - identification scheme |
| Act | Primary legislation passed by Parliament |
| Section | Major division of an Act (numbered 1, 2, 3...) |
| Sub-section | Division within a section (numbered (1), (2), (3)...) |
| Clause | Division within a sub-section (lettered (a), (b), (c)...) |
| Sub-clause | Division within a clause (numbered (i), (ii), (iii)...) |
| Proviso | Exception or condition starting with "Provided that" |
| Explanation | Clarifying text for a provision |
| Illustration | Example demonstrating application of a provision |
| Schedule | Supplementary content at end of Act (tables, forms) |
| Gazette | Official government publication for laws |

---

## 15. Appendix

### A. Sample Input (DPDP Act First Page)

```
THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023
(NO. 22 OF 2023)
[11th August, 2023.]

An Act to provide for the processing of digital personal data in a manner that
recognises both the right of individuals to protect their personal data and the
need to process such personal data for lawful purposes and for matters
connected therewith or incidental thereto.

BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as
follows:--

CHAPTER I
PRELIMINARY

1. (1) This Act may be called the Digital Personal Data Protection Act, 2023.

(2) It shall come into force on such date as the Central Government may, by notification
in the Official Gazette, appoint...
```

### B. References

- Akoma Ntoso 3.0 Specification: http://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0.html
- Gazette of India: https://egazette.gov.in/
- India Code: https://www.indiacode.nic.in/

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-23 | - | Initial draft |
