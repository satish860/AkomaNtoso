# Project: Indian Acts to Akoma Ntoso Converter

## Overview
Convert Indian Parliamentary Acts (PDF) to Akoma Ntoso (LegalDocML) XML format using Claude API for intelligent parsing.

## Project Documents

- **PRD.md** - Product Requirements Document (requirements, user stories, technical specs)
- **BACKLOG.md** - Kanban backlog (tasks to pick and complete)

## Development Approach

- **TDD** - Write tests first, then implement
- **Kanban** - Pick one task at a time from BACKLOG.md
- **Exit Criteria** - Define when picking each task

## Key Files

```
data/                     # Input PDFs
output/                   # Generated XML
src/extractor/            # PDF to text
src/parser/               # LLM-based parsing (Claude API)
src/generator/            # Akoma Ntoso XML generation
src/models/               # Data classes
tests/                    # pytest tests
```

## Commands

```bash
# Run tests
pytest

# Convert PDF to AKN
python -m src.cli convert data/act.pdf -o output/act.xml
```

## Current Status

Check BACKLOG.md for current task and progress.
