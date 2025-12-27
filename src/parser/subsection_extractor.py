"""Subsection extraction using Claude structured outputs."""
import json
from typing import List
from pydantic import BaseModel
from .llm_client import get_client, get_model


class SubSection(BaseModel):
    """A subsection in an Indian legal Act section."""
    number: int      # Subsection number like 1, 2, 3 (from (1), (2), (3))
    content: str     # The subsection text/content


EXTRACT_SUBSECTIONS_PROMPT = """Analyze this chapter text and extract all subsections for Section {section_num}.

For each subsection, identify:
1. number: The subsection number (integer like 1, 2, 3 from "(1)", "(2)", "(3)")
2. content: The main text of the subsection (first sentence or key content)

Look for patterns like:
- "{section_num}. (1) ..." - first subsection of section
- "(2) ..." - second subsection
- "(3) ..." - third subsection

IMPORTANT:
- Only extract subsections for Section {section_num}
- Subsections are numbered like (1), (2), (3)
- Do NOT include clauses (a), (b), (c) - those are different
- Content should be the main text of the subsection, not the full paragraph

CHAPTER TEXT:
{text}
"""


def extract_subsections(chapter_text: str, section_num: int) -> List[SubSection]:
    """
    Extract subsections from a section using structured outputs.

    Args:
        chapter_text: Text of the chapter containing the section
        section_num: Section number to extract subsections from

    Returns:
        List of SubSection objects with number and content
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
                "content": EXTRACT_SUBSECTIONS_PROMPT.format(
                    section_num=section_num,
                    text=chapter_text
                )
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "subsections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "number": {"type": "integer"},
                                "content": {"type": "string"}
                            },
                            "required": ["number", "content"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["subsections"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return [SubSection(**sub) for sub in result["subsections"]]
