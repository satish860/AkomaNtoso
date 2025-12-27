"""Subclause extraction using Claude structured outputs."""
import json
from typing import List
from pydantic import BaseModel
from .llm_client import get_client, get_model


class SubClause(BaseModel):
    """A subclause in an Indian legal Act clause."""
    numeral: str     # Subclause numeral like "i", "ii", "iii" (from (i), (ii), (iii))
    content: str     # The subclause text/content


EXTRACT_SUBCLAUSES_PROMPT = """Analyze this chapter text and extract all subclauses for Section {section_num}, clause ({clause_letter}).

For each subclause, identify:
1. numeral: The subclause numeral (lowercase roman like "i", "ii", "iii" from "(i)", "(ii)", "(iii)")
2. content: The text of the subclause

Look for patterns like:
- "(i) ..." - first subclause
- "(ii) ..." - second subclause
- "(iii) ..." - third subclause

IMPORTANT:
- Only extract subclauses for Section {section_num}, clause ({clause_letter})
- Subclauses use roman numerals like (i), (ii), (iii), (iv), etc.
- Content should be the main text of the subclause

CHAPTER TEXT:
{text}
"""


def extract_subclauses(chapter_text: str, section_num: int, clause_letter: str) -> List[SubClause]:
    """
    Extract subclauses from a clause using structured outputs.

    Args:
        chapter_text: Text of the chapter containing the section
        section_num: Section number
        clause_letter: Clause letter to extract subclauses from (e.g., "j")

    Returns:
        List of SubClause objects with numeral and content
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
                "content": EXTRACT_SUBCLAUSES_PROMPT.format(
                    section_num=section_num,
                    clause_letter=clause_letter,
                    text=chapter_text
                )
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "subclauses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "numeral": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["numeral", "content"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["subclauses"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return [SubClause(**sc) for sc in result["subclauses"]]
