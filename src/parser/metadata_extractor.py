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


class DocumentMetadata(BaseModel):
    """Metadata for any legal document (multi-jurisdiction)."""
    title: str                      # Full title
    number: str                     # Document number (can be string like "607")
    year: int                       # Year
    date_enacted: Optional[str] = None   # Date enacted (ISO format preferred)
    country: str                    # ISO 3166-1 alpha-2: in, ie, gb, us, eu
    doc_type: str                   # act, regulation, statutory-instrument, rules, bill
    language: str = "eng"           # ISO 639-2 language code


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


EXTRACT_DOCUMENT_METADATA_PROMPT = """Analyze this legal document and extract metadata.

Identify the document and extract:
1. title: Full official title of the document
2. number: Document number (e.g., "22" for Act No. 22, "607" for S.I. No. 607)
3. year: Year of enactment/publication
4. date_enacted: Date enacted or came into force (ISO format YYYY-MM-DD if possible)
5. country: Country code based on document origin:
   - "in" for India (Acts of Parliament, Gazette of India)
   - "ie" for Ireland (S.I. No., Irish Statute Book)
   - "gb" for United Kingdom (UK Statutory Instruments)
   - "eu" for European Union regulations
   - "us" for United States
6. doc_type: Type of document:
   - "act" for Acts of Parliament
   - "regulation" for Statutory Instruments, S.I., Regulations
   - "rules" for Rules (e.g., DPDP Rules)
   - "bill" for Bills
7. language: "eng" for English, "gle" for Irish, "hin" for Hindi

Patterns to look for:
- India: "THE [NAME] ACT, YEAR", "NO. X OF YEAR", "Gazette of India"
- Ireland: "S.I. No. X of YEAR", "STATUTORY INSTRUMENTS", "Iris Oifigiuil"
- UK: "UK Statutory Instruments", "YEAR No. X"
- EU: "Regulation (EU) YEAR/X", "Directive (EU)"

DOCUMENT TEXT (first 4000 characters):
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


def extract_document_metadata(text: str) -> DocumentMetadata:
    """
    Extract metadata from any legal document (multi-jurisdiction).

    Auto-detects country, document type, and extracts title, number, year, date.

    Args:
        text: Document text (first ~4000 chars used)

    Returns:
        DocumentMetadata with title, number, year, date_enacted, country, doc_type, language
    """
    client = get_client()
    model = get_model()

    # Only need beginning of document for metadata
    text_sample = text[:4000]

    response = client.beta.messages.create(
        model=model,
        max_tokens=1000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": EXTRACT_DOCUMENT_METADATA_PROMPT.format(text=text_sample)
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "number": {"type": "string"},
                    "year": {"type": "integer"},
                    "date_enacted": {"type": ["string", "null"]},
                    "country": {"type": "string"},
                    "doc_type": {"type": "string"},
                    "language": {"type": "string"}
                },
                "required": ["title", "number", "year", "date_enacted", "country", "doc_type", "language"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return DocumentMetadata(**result)
