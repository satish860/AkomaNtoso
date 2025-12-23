"""LLM-based text cleaning module.

Uses Claude to generate Python cleaning code, then executes it.
This approach adapts to different document formats without hardcoded patterns.
"""
import re
from src.parser.llm_client import get_client, get_model


CLEANING_CODE_PROMPT = '''You are a code generator. Write Python code to clean legal document text extracted from an Indian Gazette PDF.

Sample text:
"""
{sample_text}
"""

Write a Python function called `clean(text)` that removes noise while preserving legal content.

REMOVE these patterns:
1. Lines with "GAZETTE OF INDIA", "EXTRAORDINARY", "PART II", "PUBLISHED BY AUTHORITY"
2. Registration lines containing: "REGISTERED NO.", "CG-DL-E-", "xxxGIDExxx"
3. Standalone page numbers (lines with only digits)
4. Lines starting with "No." followed by "]"
5. Lines that are ONLY non-ASCII characters (use: r'^[^\x00-\x7F]+$')
6. "Separate paging" informational lines

PRESERVE:
- Act titles (THE ... ACT)
- CHAPTER headings
- Section numbers and content
- MINISTRY OF LAW header
- All legal content in English

CODING RULES:
- To match non-ASCII: use exactly r'[^\x00-\x7F]'
- Only remove lines that are ENTIRELY non-ASCII, not lines with mixed content
- Use re.MULTILINE for line-based patterns
- Normalize multiple newlines at the end

Return ONLY the Python code:
```python
import re

def clean(text):
    # Remove lines that are ONLY non-ASCII (pure Hindi lines)
    text = re.sub(r'^[^\x00-\x7F]+$', '', text, flags=re.MULTILINE)
    # Remove gazette headers
    text = re.sub(r'^.*GAZETTE OF INDIA.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*EXTRAORDINARY.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*PUBLISHED BY AUTHORITY.*$', '', text, flags=re.MULTILINE)
    # Remove registration metadata
    text = re.sub(r'^.*REGISTERED NO\..*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*CG-DL-E-.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*xxxGIDExxx.*$', '', text, flags=re.MULTILINE)
    # Remove standalone page numbers
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    # Normalize whitespace
    text = re.sub(r'\n{{3,}}', '\n\n', text)
    return text.strip()
```
'''


def generate_cleaning_code(sample_text: str, jurisdiction: str = "in") -> str:
    """Use Claude to generate Python cleaning code based on sample text.

    Args:
        sample_text: Sample of raw text to analyze
        jurisdiction: Country code for context

    Returns:
        Python code string with a clean() function
    """
    client = get_client()
    model = get_model()

    prompt = CLEANING_CODE_PROMPT.format(sample_text=sample_text[:3000])

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    code = response.content[0].text

    # Extract code from markdown code blocks if present
    code_match = re.search(r'```python\s*(.*?)\s*```', code, re.DOTALL)
    if code_match:
        code = code_match.group(1)

    # Also try without python specifier
    if '```' in code and 'def clean' not in code.split('```')[0]:
        code_match = re.search(r'```\s*(.*?)\s*```', code, re.DOTALL)
        if code_match:
            code = code_match.group(1)

    return code.strip()


def execute_cleaning_code(code: str, raw_text: str) -> str:
    """Execute the generated cleaning code on raw text.

    Args:
        code: Python code with clean() function
        raw_text: Full raw text to clean

    Returns:
        Cleaned text
    """
    # Create namespace with necessary modules pre-imported
    import builtins
    namespace = {
        '__builtins__': builtins,
        're': __import__('re'),
    }

    # Execute the generated code
    exec(code, namespace)

    # Call the clean function
    if 'clean' in namespace:
        return namespace['clean'](raw_text)
    elif 'clean_text' in namespace:
        return namespace['clean_text'](raw_text)
    else:
        raise ValueError("Generated code does not define a clean() or clean_text() function")


def clean_text(raw_text: str, jurisdiction: str = "in") -> str:
    """Clean raw PDF text using LLM-generated code.

    Args:
        raw_text: Raw text from PDF extraction
        jurisdiction: Country code for context (in, uk, us)

    Returns:
        Cleaned text with noise removed
    """
    # Take a sample for Claude to analyze
    sample = raw_text[:3000]

    # Generate cleaning code
    code = generate_cleaning_code(sample, jurisdiction)

    # Execute the code on full text
    cleaned = execute_cleaning_code(code, raw_text)

    return cleaned
