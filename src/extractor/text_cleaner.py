"""LLM-based text cleaning module.

Uses Claude to generate Python cleaning code, then executes it.
This approach adapts to different document formats without hardcoded patterns.
"""
import re
from src.parser.llm_client import get_client, get_model


CLEANING_CODE_PROMPT = '''You are a code generator. Analyze this sample text from a legal document PDF and write Python code to clean it.

Sample text:
"""
{sample_text}
"""

Write a Python function called `clean(text)` that:
1. Removes page headers/footers (e.g., "THE GAZETTE OF INDIA EXTRAORDINARY", "PART II")
2. Removes standalone page numbers (lines with only digits)
3. Removes registration/metadata lines (e.g., "REGISTERED NO.", "CG-DL-E-")
4. Removes lines that are primarily non-ASCII characters (use character range, NOT literal Hindi text)
5. Normalizes excessive whitespace (multiple newlines to double, multiple spaces to single)
6. Preserves the actual legal content (Act title, chapters, sections, definitions)

IMPORTANT RULES FOR THE CODE:
- Use Unicode ranges to match non-English text: r'[^\x00-\x7F]+' for non-ASCII
- Do NOT copy/paste Hindi or Devanagari characters into regex patterns
- Keep regex patterns simple and ASCII-only
- Use re.MULTILINE flag when matching line patterns

Return ONLY the Python code, no explanations. The code should:
- Import any needed modules (like `re`) at the top
- Define a single function: `def clean(text):`
- Return the cleaned text string

Example format:
```python
import re

def clean(text):
    # Remove lines with primarily non-ASCII characters (Hindi headers)
    text = re.sub(r'^[^\x00-\x7F].*$', '', text, flags=re.MULTILINE)
    # Remove gazette headers
    text = re.sub(r'THE GAZETTE OF INDIA.*', '', text)
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
