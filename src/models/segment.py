"""Segment model for level-by-level extraction."""
from typing import Optional, List
from pydantic import BaseModel


class Segment(BaseModel):
    """A segment found by LLM at a single hierarchy level."""
    type: str                   # "chapter", "section", "rule", etc.
    number: str                 # "I", "1", "(a)", "(i)"
    title: Optional[str] = None # Heading text if present
    start_line: int             # Line number where segment starts
    end_line: int               # Line number where segment ends


class LevelExtraction(BaseModel):
    """All segments found at one level - LLM structured output schema."""
    segments: List[Segment]
