"""Clause extraction using Claude structured outputs."""
import json
from typing import List
from pydantic import BaseModel
from .llm_client import get_client, get_model


class Clause(BaseModel):
    """A clause in an Indian legal Act subsection."""
    letter: str      # Clause letter like "a", "b", "c" (from (a), (b), (c))
    content: str     # The clause text/content


EXTRACT_CLAUSES_PROMPT = """Analyze this chapter text and extract all clauses for Section {section_num}, Subsection ({subsection_num}).

For each clause, identify:
1. letter: The clause letter (lowercase like "a", "b", "c" from "(a)", "(b)", "(c)")
2. content: The text of the clause

Look for patterns like:
- "(a) ..." - first clause
- "(b) ..." - second clause
- "(c) ..." - third clause

IMPORTANT:
- Only extract clauses for Section {section_num}, Subsection ({subsection_num})
- Clauses are lettered like (a), (b), (c)
- Do NOT include sub-clauses (i), (ii), (iii) - those are different
- Content should be the main text of the clause

CHAPTER TEXT:
{text}
"""


def extract_clauses(chapter_text: str, section_num: int, subsection_num: int) -> List[Clause]:
    """
    Extract clauses from a subsection using structured outputs.

    Args:
        chapter_text: Text of the chapter containing the section
        section_num: Section number
        subsection_num: Subsection number to extract clauses from

    Returns:
        List of Clause objects with letter and content
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
                "content": EXTRACT_CLAUSES_PROMPT.format(
                    section_num=section_num,
                    subsection_num=subsection_num,
                    text=chapter_text
                )
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "clauses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "letter": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["letter", "content"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["clauses"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return [Clause(**clause) for clause in result["clauses"]]
