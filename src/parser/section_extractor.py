"""Section extraction using Claude structured outputs."""
import json
from typing import List
from pydantic import BaseModel
from .llm_client import get_client, get_model
from .chapter_extractor import Chapter, get_chapter_text


class Section(BaseModel):
    """A section in an Indian legal Act."""
    number: int      # Section number like 1, 2, 3
    heading: str     # Section heading like "Short title and commencement"


EXTRACT_SECTIONS_PROMPT = """Analyze this chapter from an Indian legal Act and extract all sections.

For each section, identify:
1. number: The section number (integer like 1, 2, 3)
2. heading: The section heading/title (e.g., "Short title and commencement", "Definitions")

Look for patterns like:
- "1. (1) This Act may be called..." with marginal heading "Short title and commencement"
- "2. In this Act, unless the context otherwise requires" with heading "Definitions"
- Section numbers at the start of lines followed by content

This is Chapter {chapter_num}. Extract only sections from this chapter.

CHAPTER TEXT:
{text}
"""


def extract_sections(chapter_text: str, chapter_num: str = "") -> List[Section]:
    """
    Extract sections from a chapter using structured outputs.

    Args:
        chapter_text: Text of a single chapter
        chapter_num: Chapter number for context (optional)

    Returns:
        List of Section objects with number and heading
    """
    client = get_client()
    model = get_model()

    response = client.beta.messages.create(
        model=model,
        max_tokens=2000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": EXTRACT_SECTIONS_PROMPT.format(
                    chapter_num=chapter_num,
                    text=chapter_text
                )
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "number": {"type": "integer"},
                                "heading": {"type": "string"}
                            },
                            "required": ["number", "heading"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["sections"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return [Section(**sec) for sec in result["sections"]]
