"""Line-numbered text extraction with page tracking."""
import re
from typing import List, Tuple

from src.models import LineInfo
from src.extractor.pdf_extractor import extract_text


def extract_with_line_info(
    pdf_path: str,
    remove_hindi: bool = True
) -> Tuple[List[LineInfo], str]:
    """
    Extract PDF text with line-level metadata and page tracking.

    Uses extract_text(include_page_markers=True) which inserts [PAGE:N] markers.
    Parses markers to track current page, skips markers in output.

    Args:
        pdf_path: Path to PDF file
        remove_hindi: Whether to remove Hindi text (default True)

    Returns:
        line_infos: List of LineInfo (line_num, page, text)
        numbered_text: Formatted text for LLM ("  1| CHAPTER I\\n  2| ...")
    """
    raw_text = extract_text(pdf_path, remove_hindi=remove_hindi, include_page_markers=True)

    line_infos = []
    line_num = 0
    current_page = 1

    for line in raw_text.split('\n'):
        # Track page from [PAGE:N] markers
        if line.startswith('[PAGE:'):
            match = re.match(r'\[PAGE:(\d+)\]', line)
            if match:
                current_page = int(match.group(1))
            continue  # Skip marker line

        # Skip empty lines
        if not line.strip():
            continue

        line_num += 1
        line_infos.append(LineInfo(
            line_num=line_num,
            page=current_page,
            text=line
        ))

    numbered_text = format_numbered_text(line_infos)
    return line_infos, numbered_text


def format_numbered_text(line_infos: List[LineInfo]) -> str:
    """
    Format lines with line numbers for LLM consumption.

    Example output:
        1| CHAPTER I
        2| PRELIMINARY
      ...
      456| (b) any other matter...

    Line number width adjusts based on total lines.
    """
    if not line_infos:
        return ""

    max_width = len(str(line_infos[-1].line_num))
    lines = []
    for li in line_infos:
        numbered = f"{li.line_num:>{max_width}}| {li.text}"
        lines.append(numbered)

    return '\n'.join(lines)


def get_lines_slice(
    line_infos: List[LineInfo],
    start_line: int,
    end_line: int
) -> str:
    """
    Get numbered text for a specific line range.

    Used for level-by-level extraction - extracts a subset of lines
    for the LLM to analyze.

    Args:
        line_infos: Full list of LineInfo
        start_line: First line number (inclusive)
        end_line: Last line number (inclusive)

    Returns:
        Numbered text for the range, e.g.:
           42| Part II
           43| REGULATIONS
           ...
           58| (2) These regulations...
    """
    subset = [li for li in line_infos if start_line <= li.line_num <= end_line]
    return format_numbered_text(subset)


def get_content(
    line_infos: List[LineInfo],
    start_line: int,
    end_line: int
) -> str:
    """
    Get raw content (no line numbers) for a line range.

    Used for extracting leaf node content.

    Args:
        line_infos: Full list of LineInfo
        start_line: First line number (inclusive)
        end_line: Last line number (inclusive)

    Returns:
        Raw text content joined by newlines
    """
    subset = [li for li in line_infos if start_line <= li.line_num <= end_line]
    return '\n'.join(li.text for li in subset)


def get_page_for_line(line_infos: List[LineInfo], line_num: int) -> int:
    """
    Get PDF page number for a specific line.

    Args:
        line_infos: Full list of LineInfo
        line_num: Line number to look up

    Returns:
        PDF page number (1-indexed), or 1 if not found
    """
    for li in line_infos:
        if li.line_num == line_num:
            return li.page
    return 1


def get_page_range(
    line_infos: List[LineInfo],
    start_line: int,
    end_line: int
) -> Tuple[int, int]:
    """
    Get (first_page, last_page) for a line range.

    Args:
        line_infos: Full list of LineInfo
        start_line: First line number
        end_line: Last line number

    Returns:
        Tuple of (start_page, end_page)
    """
    start_page = get_page_for_line(line_infos, start_line)
    end_page = get_page_for_line(line_infos, end_line)
    return start_page, end_page
