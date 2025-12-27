# Product Backlog
# Indian Acts to Akoma Ntoso Converter

**Last Updated:** 2024-12-23

---

## Kanban Board

### DONE
| ID | Task | Points |
|----|------|--------|
| T-001 | Download sample PDF (DPDP Act 2023) | 1 |
| T-002 | Create PRD document | 3 |
| T-003 | Create implementation plan | 2 |
| T-010 | Create project folder structure | 1 |
| T-011 | Create requirements.txt and install deps | 1 |
| T-012 | Create .env.example for API keys | 1 |
| T-013 | Set up pytest configuration | 1 |
| T-014 | Write test_pdf_extractor.py (RED) | 2 |
| T-015 | Implement pdf_extractor.py (GREEN) | 3 |
| T-016 | Set up Claude API client | 2 |
| T-017 | Write test_text_cleaner.py - LLM-based (RED) | 2 |
| T-018 | Implement text_cleaner.py - LLM-based (GREEN) | 3 |
| T-019 | Analyze cleaned text structure (discovery) | 1 |
| T-020 | Extract chapters using structured outputs (TDD) | 2 |
| T-021 | Extract sections within chapters (TDD) | 2 |
| T-022 | Extract metadata from document (TDD) | 2 |
| T-023 | Extract subsections within sections (TDD) | 2 |
| T-024 | Extract clauses within subsections (TDD) | 2 |
| T-025 | Extract subclauses within clauses (TDD) | 2 |
| T-026 | Create unified document extractor | 3 |
| T-027 | Write test_akn_generator.py - basic (TDD) | 2 |

### IN PROGRESS
| ID | Task | Points | Exit Criteria |
|----|------|--------|---------------|
| | | | |

### TO DO
| ID | Task | Points | Sprint |
|----|------|--------|--------|
| T-028 | Add XML validation against AKN schema | 2 | 3 |
| T-029 | End-to-end test: PDF to AKN XML | 3 | 4 |
| T-030 | Generate AKN for DPDP Act and review | 2 | 4 |
| T-031 | Create README with usage docs | 2 | 4 |

### ICEBOX (Future)
| ID | Task | Points |
|----|------|--------|
| F-001 | Support for Bills | 8 |
| F-002 | Support for Ordinances | 5 |
| F-003 | Web UI for review | 13 |
| F-004 | Batch processing API | 8 |
| F-005 | UK jurisdiction support | 13 |
| F-006 | USA jurisdiction support | 13 |
| F-007 | Amendment tracking | 8 |
| F-008 | Cross-reference linking | 5 |
| F-009 | Local LLM support (Ollama) | 5 |
| F-010 | Response caching | 3 |

---

## Sprint Summary

| Sprint | Focus | Points |
|--------|-------|--------|
| 1 | Foundation (PDF extraction) | 14 |
| 2 | Models & LLM parsing | 25 |
| 3 | XML generation & CLI | 24 |
| 4 | Integration & polish | 25 |
| **Total** | | **88** |

---

## How to Use This Backlog

1. **Pick a task** from TO DO (start from top)
2. **Move to IN PROGRESS** and add exit criteria
3. **Complete the task** following TDD (test first)
4. **Move to DONE** when exit criteria met

### Exit Criteria Template
When picking a task, define:
```
Exit Criteria for T-XXX:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass
- [ ] Code reviewed
```

---

## Next Task: T-028

When ready to start, pick T-028 (Add XML validation against AKN schema).
