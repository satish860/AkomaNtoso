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

### IN PROGRESS
| ID | Task | Points | Exit Criteria |
|----|------|--------|---------------|
| | | | |

### TO DO
| ID | Task | Points | Sprint |
|----|------|--------|--------|
| T-016 | Set up Claude API client | 2 | 1 |
| T-017 | Write test_text_cleaner.py - LLM-based (RED) | 2 | 1 |
| T-018 | Implement text_cleaner.py - LLM-based (GREEN) | 3 | 1 |
| T-020 | Write test_models.py (RED) | 2 | 2 |
| T-021 | Implement document.py models (GREEN) | 2 | 2 |
| T-023 | Create extract_metadata prompt | 2 | 2 |
| T-024 | Write test_llm_parser.py - metadata (RED) | 2 | 2 |
| T-025 | Implement extract_metadata function (GREEN) | 3 | 2 |
| T-026 | Create parse_structure prompt | 2 | 2 |
| T-027 | Write test_llm_parser.py - structure (RED) | 2 | 2 |
| T-028 | Implement parse_structure function (GREEN) | 5 | 2 |
| T-029 | Create parse_section prompt | 2 | 2 |
| T-030 | Write test_llm_parser.py - section (RED) | 2 | 2 |
| T-031 | Implement parse_section function (GREEN) | 3 | 2 |
| T-040 | Write test_akn_generator.py - basic (RED) | 2 | 3 |
| T-041 | Implement basic AKN XML structure (GREEN) | 3 | 3 |
| T-042 | Write test_akn_generator.py - metadata (RED) | 2 | 3 |
| T-043 | Implement FRBR metadata generation (GREEN) | 3 | 3 |
| T-044 | Write test_akn_generator.py - body (RED) | 2 | 3 |
| T-045 | Implement body generation (GREEN) | 5 | 3 |
| T-046 | Write test_akn_generator.py - special (RED) | 2 | 3 |
| T-047 | Implement special elements (GREEN) | 3 | 3 |
| T-048 | Write test_cli.py (RED) | 2 | 3 |
| T-049 | Implement cli.py (GREEN) | 3 | 3 |
| T-050 | Write test_e2e.py (RED) | 3 | 4 |
| T-051 | Run full pipeline on DPDP Act (GREEN) | 5 | 4 |
| T-052 | Add confidence markers to output | 3 | 4 |
| T-053 | Add validate command to CLI | 2 | 4 |
| T-054 | Add preview command to CLI | 2 | 4 |
| T-055 | Manual review of DPDP Act output | 3 | 4 |
| T-056 | Fix issues found in review | 5 | 4 |
| T-057 | Create README.md | 2 | 4 |

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

## Next Task: T-016

When ready to start, pick T-016 (Set up Claude API client - needed for LLM-based text cleaning).
