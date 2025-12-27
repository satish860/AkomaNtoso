"""Metadata extraction using Claude structured outputs."""
import json
from typing import Optional
from pydantic import BaseModel
from .llm_client import get_client, get_model


class ActMetadata(BaseModel):
    """Metadata for an Indian legal Act."""
    title: str                      # Full title like "THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023"
    act_number: int                 # Act number like 22
    year: int                       # Year like 2023
    short_title: Optional[str] = None    # Short title like "Digital Personal Data Protection Act, 2023"
    date_enacted: Optional[str] = None   # Date enacted like "2023-08-11"


EXTRACT_METADATA_PROMPT = """Analyze this Indian legal Act and extract the metadata.

Extract the following information:
1. title: The full official title (e.g., "THE DIGITAL PERSONAL DATA PROTECTION ACT, 2023")
2. act_number: The act number (integer, e.g., 22 from "NO. 22 OF 2023")
3. year: The year of the act (integer, e.g., 2023)
4. short_title: The short title from Section 1 (e.g., "Digital Personal Data Protection Act, 2023")
5. date_enacted: The date the act received assent (e.g., "2023-08-11" or "11th August, 2023")

Look for patterns like:
- "THE [ACT NAME] ACT, YEAR" for the title
- "(NO. X OF YEAR)" for the act number
- "[Date]" in brackets or "received the assent...on [date]" for date enacted
- "This Act may be called..." in Section 1 for short title

DOCUMENT TEXT (first 3000 characters):
{text}
"""


def extract_metadata(text: str) -> ActMetadata:
    """
    Extract metadata from an Indian legal Act using structured outputs.

    Args:
        text: Cleaned document text

    Returns:
        ActMetadata object with title, act_number, year, short_title, date_enacted
    """
    client = get_client()
    model = get_model()

    # Only need beginning of document for metadata
    text_sample = text[:3000]

    response = client.beta.messages.create(
        model=model,
        max_tokens=1000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": EXTRACT_METADATA_PROMPT.format(text=text_sample)
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "act_number": {"type": "integer"},
                    "year": {"type": "integer"},
                    "short_title": {"type": "string"},
                    "date_enacted": {"type": "string"}
                },
                "required": ["title", "act_number", "year", "short_title", "date_enacted"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return ActMetadata(**result)
