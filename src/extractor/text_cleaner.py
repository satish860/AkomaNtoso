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
- Page markers in format [PAGE:N] (e.g. [PAGE:1], [PAGE:2]) - these are important for PDF navigation

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


def verify_cleaned_text(raw_text: str, cleaned_text: str) -> tuple[bool, str]:
    """Verify the cleaned text preserves important content.

    Args:
        raw_text: Original raw text
        cleaned_text: Cleaned text to verify

    Returns:
        Tuple of (is_valid, error_message)
    """
    errors = []

    # Check not empty
    if len(cleaned_text.strip()) == 0:
        errors.append("Cleaned text is empty")

    # Check not too short (should preserve most content)
    if len(cleaned_text) < len(raw_text) * 0.3:
        errors.append(f"Too much removed: {len(cleaned_text)}/{len(raw_text)} chars")

    # Check key legal content preserved (case-insensitive)
    key_phrases = ["chapter", "act", "section", "shall"]
    cleaned_lower = cleaned_text.lower()
    found = sum(1 for phrase in key_phrases if phrase in cleaned_lower)
    if found < 2:
        errors.append(f"Missing key legal content (found {found}/4 key phrases)")

    if errors:
        return False, "; ".join(errors)
    return True, ""


def generate_fix_prompt(original_code: str, error: str, sample: str) -> str:
    """Generate a prompt to fix the cleaning code."""
    return f'''The cleaning code you generated has issues:
ERROR: {error}

Original code:
```python
{original_code}
```

Sample text being cleaned:
"""
{sample[:1500]}
"""

Please fix the code. The issue is that it's removing too much content.
Make the patterns MORE SPECIFIC to only remove actual noise.
Keep all legal content (chapters, sections, definitions).

Return ONLY the fixed Python code.
'''


def clean_text(raw_text: str, jurisdiction: str = "in", max_retries: int = 3) -> str:
    """Clean raw PDF text using LLM-generated code with verification loop.

    Args:
        raw_text: Raw text from PDF extraction
        jurisdiction: Country code for context (in, uk, us)
        max_retries: Maximum retry attempts if verification fails

    Returns:
        Cleaned text with noise removed
    """
    sample = raw_text[:3000]
    client = get_client()
    model = get_model()

    # Initial code generation
    code = generate_cleaning_code(sample, jurisdiction)

    for attempt in range(max_retries):
        try:
            # Execute the code
            cleaned = execute_cleaning_code(code, raw_text)

            # Verify the output
            is_valid, error = verify_cleaned_text(raw_text, cleaned)

            if is_valid:
                return cleaned

            # If not valid and we have retries left, ask Claude to fix it
            if attempt < max_retries - 1:
                fix_prompt = generate_fix_prompt(code, error, sample)
                response = client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": fix_prompt}]
                )
                new_code = response.content[0].text

                # Extract code from markdown if present
                code_match = re.search(r'```python\s*(.*?)\s*```', new_code, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()
                else:
                    code = new_code.strip()

        except SyntaxError as e:
            # Code has syntax error, ask Claude to fix
            if attempt < max_retries - 1:
                fix_prompt = generate_fix_prompt(code, f"SyntaxError: {e}", sample)
                response = client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": fix_prompt}]
                )
                new_code = response.content[0].text
                code_match = re.search(r'```python\s*(.*?)\s*```', new_code, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()
                else:
                    code = new_code.strip()
            else:
                raise

    # Return best effort after max retries
    return cleaned
