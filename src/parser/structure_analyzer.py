"""Structure analyzer - uses LLM to discover document elements."""
import json
from typing import Dict, Any, List
from .llm_client import get_client, get_model


# Standard hierarchy order for Indian legal documents (top to bottom)
HIERARCHY_ORDER = [
    "parts",
    "chapters",
    "sections",
    "subsections",
    "clauses",
    "subclauses",
]


ANALYZE_STRUCTURE_PROMPT = """Analyze this Indian legal document text and identify what structural elements exist.

Return a JSON object with:
1. "elements_found": dict of element type -> true/false
2. "counts": dict of element type -> count (number found)

Element types to check:
- chapters: Does the document have CHAPTER divisions? (Count all CHAPTER I, II, III, etc.)
- sections: Does it have numbered sections (1., 2., 3.)? (Count all)
- subsections: Does it have subsections like (1), (2)?
- clauses: Does it have clauses like (a), (b), (c)?
- subclauses: Does it have sub-clauses like (i), (ii) or (A), (B)?
- explanations: Are there "Explanation.--" or "Explanation.-" elements?
- provisos: Are there "Provided that" provisos?
- schedules: Is there a Schedule/Annexure at the end?
- illustrations: Are there example illustrations (e.g., "X, an individual...")?

Return ONLY valid JSON, no other text.

DOCUMENT TEXT (beginning, middle, and end sections):
{text}
"""


def analyze_structure(text: str) -> Dict[str, Any]:
    """
    Use LLM to analyze document structure and discover elements.

    Args:
        text: Cleaned document text

    Returns:
        Dict with:
            - elements_found: dict of element type -> bool
            - counts: dict of element type -> int
    """
    client = get_client()
    model = get_model()

    # Sample beginning, middle, and end to get full picture
    text_len = len(text)
    if text_len <= 20000:
        text_sample = text
    else:
        # Take 8000 from start, 4000 from middle, 8000 from end
        start = text[:8000]
        middle_start = (text_len // 2) - 2000
        middle = text[middle_start:middle_start + 4000]
        end = text[-8000:]
        text_sample = f"{start}\n\n[...MIDDLE SECTION...]\n\n{middle}\n\n[...END SECTION...]\n\n{end}"

    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": ANALYZE_STRUCTURE_PROMPT.format(text=text_sample)
            }
        ]
    )

    # Parse JSON response
    response_text = response.content[0].text.strip()

    # Handle potential markdown code blocks
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    return json.loads(response_text)


def get_hierarchy(structure_result: Dict[str, Any]) -> List[str]:
    """
    Determine document hierarchy from structure analysis.

    Args:
        structure_result: Result from analyze_structure()

    Returns:
        Ordered list of hierarchy levels found in document.
        E.g., ["chapters", "sections", "subsections", "clauses"]
    """
    elements_found = structure_result.get("elements_found", {})

    # Filter standard hierarchy to only include found elements
    hierarchy = [
        level for level in HIERARCHY_ORDER
        if elements_found.get(level, False)
    ]

    return hierarchy
