"""Chapter extraction using Claude structured outputs."""
import json
from typing import List
from pydantic import BaseModel
from .llm_client import get_client, get_model


class Chapter(BaseModel):
    """A chapter in an Indian legal Act."""
    number: str      # Roman numeral like "I", "II"
    title: str       # Chapter title like "PRELIMINARY"
    start_line: int  # Line number where chapter starts
    end_line: int    # Line number where chapter ends


EXTRACT_CHAPTERS_PROMPT = """Analyze this Indian legal Act and extract all chapters.

For each chapter, identify:
1. number: The roman numeral (I, II, III, IV, V, VI, VII, VIII, IX, etc.)
2. title: The chapter title (e.g., "PRELIMINARY", "OBLIGATIONS OF DATA FIDUCIARY")
3. start_line: Line number where "CHAPTER X" appears
4. end_line: Line number before next chapter starts (or last line of document)

IMPORTANT:
- Line numbers are shown at the start of each line (e.g., "  25| CHAPTER I")
- Extract ALL chapters in the document
- If chapter title is not on same line, look at the next non-empty line

Document has {total_lines} lines.

DOCUMENT TEXT (with line numbers):
{text}
"""


def add_line_numbers(text: str) -> str:
    """Add line numbers to text for LLM reference."""
    lines = text.split('\n')
    numbered = []
    for i, line in enumerate(lines, 1):
        numbered.append(f"{i:4d}| {line}")
    return '\n'.join(numbered)


def extract_chapters(text: str) -> List[Chapter]:
    """
    Extract chapters from cleaned legal document text using structured outputs.

    Args:
        text: Cleaned document text

    Returns:
        List of Chapter objects with number, title, start_line, end_line
    """
    client = get_client()
    model = get_model()

    lines = text.split('\n')
    total_lines = len(lines)
    numbered_text = add_line_numbers(text)

    response = client.beta.messages.create(
        model=model,
        max_tokens=2000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": EXTRACT_CHAPTERS_PROMPT.format(
                    total_lines=total_lines,
                    text=numbered_text
                )
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "chapters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "number": {"type": "string"},
                                "title": {"type": "string"},
                                "start_line": {"type": "integer"},
                                "end_line": {"type": "integer"}
                            },
                            "required": ["number", "title", "start_line", "end_line"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["chapters"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return [Chapter(**ch) for ch in result["chapters"]]


def get_chapter_text(full_text: str, chapter: Chapter) -> str:
    """Extract text for a specific chapter using line numbers."""
    lines = full_text.split('\n')
    start = chapter.start_line - 1  # Convert to 0-indexed
    end = chapter.end_line
    return '\n'.join(lines[start:end])
