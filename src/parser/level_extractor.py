"""Level-by-level hierarchy extraction using LLM with line numbers."""
import json
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel

from src.models import LineInfo, Segment, LevelExtraction
from src.extractor.line_numbered_extractor import (
    get_lines_slice,
    get_content,
    get_page_for_line,
)
from .llm_client import get_client, get_model


# Dynamic prompt - LLM discovers child element types
DISCOVER_CHILDREN_PROMPT = """Analyze this legal document section and find its IMMEDIATE children (direct subdivisions).

The text has line numbers prefixed (e.g., "  10| CHAPTER I").

Find the immediate structural children. These could be:
- Parts (PART I, PART II, etc.)
- Chapters (CHAPTER I, II, III)
- Sections or Regulations (1., 2., 3., etc.)
- Subsections ((1), (2), (3))
- Clauses ((a), (b), (c))
- Sub-clauses ((i), (ii), (iii))
- Paragraphs, Rules, Articles, etc.
- Definitions (in a definitions section)
- Any other structural division

IMPORTANT - Recognizing Regulations vs Subsections:
- In Statutory Instruments (S.I.) and Rules, numbered items (1., 2., 3., etc.) are REGULATIONS, not sections
- Pattern "X. (Y)" means Regulation X with subsection (Y) as its CHILD
  Example: "4. (1) The Bank shall..." = Regulation 4 starting here, with (1) as its first subsection
  Example: "21. The Act is amended..." = Regulation 21 (no subsections)
- When you see "X. (Y)", the immediate child is Regulation X (not subsection Y)
- Subsections (1), (2), (3) are children OF regulations, not siblings
- Look for the regulation number BEFORE any parenthesized subsection number

For each immediate child found, provide:
- type: What kind of element is it (e.g., "part", "chapter", "regulation", "section", "subsection", "clause", "definition")
- number: The identifier (e.g., "I", "1", "(1)", "(a)", "(i)")
- title: The heading text if present (often appears on line before the number), null if none
- start_line: Line number where this element STARTS
- end_line: Line number where this element ENDS

Rules:
- Only find IMMEDIATE children, not grandchildren
- Use the LINE NUMBERS shown to the left of "|"
- Children must not overlap
- Children must be in document order
- If this is leaf content with no subdivisions, return empty segments list
- For S.I./Rules: use "regulation" for numbered items (1., 2., 3.), not "section"

TEXT (lines {start_line} to {end_line}):
{text_slice}
"""


# Fixed type prompt - when we know what to look for
FIXED_TYPE_PROMPT = """Find all {element_type} elements in this legal document section.

The text has line numbers prefixed (e.g., "  10| CHAPTER I" or " 42| (1) The Board...").

For each {element_type} found, provide:
- type: "{element_type}"
- number: The identifier (e.g., "I", "II", "1", "2", "(a)", "(b)", "(1)", "(2)", "(i)", "(ii)")
- title: The heading text if present, null if none
- start_line: Line number where this {element_type} STARTS
- end_line: Line number where this {element_type} ENDS (before next {element_type} or section end)

Rules:
- Use the LINE NUMBERS shown to the left of "|"
- Every line in range {start_line} to {end_line} must belong to exactly one {element_type}
- Segments must not overlap
- Segments must be in document order
- If no {element_type} elements found, return empty segments list

TEXT (lines {start_line} to {end_line}):
{text_slice}
"""


def _call_llm_for_segments(prompt: str) -> List[Segment]:
    """Make LLM call and return segments."""
    client = get_client()
    model = get_model()

    response = client.beta.messages.create(
        model=model,
        max_tokens=8000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {"role": "user", "content": prompt}
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "number": {"type": "string"},
                                "title": {"type": ["string", "null"]},
                                "start_line": {"type": "integer"},
                                "end_line": {"type": "integer"}
                            },
                            "required": ["type", "number", "title", "start_line", "end_line"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["segments"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return [Segment(**seg) for seg in result.get("segments", [])]


def discover_children(
    line_infos: List[LineInfo],
    start_line: int,
    end_line: int
) -> List[Segment]:
    """
    Discover immediate children in a line range - LLM decides the type.

    Args:
        line_infos: Full list of LineInfo from document
        start_line: First line of range (inclusive)
        end_line: Last line of range (inclusive)

    Returns:
        List of Segments with dynamically discovered types
    """
    text_slice = get_lines_slice(line_infos, start_line, end_line)

    if not text_slice.strip():
        return []

    prompt = DISCOVER_CHILDREN_PROMPT.format(
        start_line=start_line,
        end_line=end_line,
        text_slice=text_slice
    )

    return _call_llm_for_segments(prompt)


def extract_level(
    line_infos: List[LineInfo],
    element_type: str,
    start_line: int,
    end_line: int
) -> List[Segment]:
    """
    Extract all segments of a specific type from a line range.

    Single LLM call to find all elements of element_type within the range.

    Args:
        line_infos: Full list of LineInfo from document
        element_type: What to extract ("chapter", "section", "rule", etc.)
        start_line: First line of range (inclusive)
        end_line: Last line of range (inclusive)

    Returns:
        List of Segments with line ranges
    """
    text_slice = get_lines_slice(line_infos, start_line, end_line)

    if not text_slice.strip():
        return []

    prompt = FIXED_TYPE_PROMPT.format(
        element_type=element_type,
        start_line=start_line,
        end_line=end_line,
        text_slice=text_slice
    )

    return _call_llm_for_segments(prompt)


class HierarchyNode(BaseModel):
    """A node in the document hierarchy with source citation."""
    level: int                          # 1 = top level, 2 = child, etc.
    type: str                           # "chapter", "section", "rule", etc.
    number: str                         # "I", "1", "(a)", "(i)"
    title: Optional[str] = None         # Heading text
    content: Optional[str] = None       # Leaf node text content
    start_line: int                     # Line where this starts
    end_line: int                       # Line where this ends
    page: int                           # PDF page number
    children: List["HierarchyNode"] = []


# Enable self-referencing
HierarchyNode.model_rebuild()


def extract_hierarchy_dynamic(
    line_infos: List[LineInfo],
    start_line: int,
    end_line: int,
    level: int = 0,
    max_depth: int = 10,
    on_progress: Optional[callable] = None
) -> List[HierarchyNode]:
    """
    Recursively extract document hierarchy with dynamic child discovery.

    LLM decides what children exist at each level - no fixed hierarchy.

    Args:
        line_infos: Full list of LineInfo from document
        start_line: First line of range to extract from
        end_line: Last line of range to extract from
        level: Current depth (0 = top level)
        max_depth: Maximum recursion depth (safety limit)
        on_progress: Optional callback for progress updates

    Returns:
        List of HierarchyNode with nested children
    """
    # Safety: prevent infinite recursion
    if level >= max_depth:
        return []

    # Small ranges are likely leaf content
    if end_line - start_line < 2:
        return []

    if on_progress:
        on_progress(f"{'  ' * level}Discovering children in lines {start_line}-{end_line}")

    # Let LLM discover what children exist
    segments = discover_children(line_infos, start_line, end_line)

    if not segments:
        return []  # Leaf node - no children

    if on_progress:
        types_found = set(seg.type for seg in segments)
        on_progress(f"{'  ' * level}  Found {len(segments)} children: {', '.join(types_found)}")

    nodes = []
    for seg in segments:
        # Recurse into this segment's range
        children = extract_hierarchy_dynamic(
            line_infos,
            seg.start_line,
            seg.end_line,
            level + 1,
            max_depth,
            on_progress
        )

        # If leaf node (no children), extract content
        content = None
        if not children:
            content = get_content(line_infos, seg.start_line, seg.end_line)

        node = HierarchyNode(
            level=level + 1,
            type=seg.type,
            number=seg.number,
            title=seg.title,
            content=content,
            start_line=seg.start_line,
            end_line=seg.end_line,
            page=get_page_for_line(line_infos, seg.start_line),
            children=children
        )
        nodes.append(node)

    return nodes


def extract_document_hierarchy(
    line_infos: List[LineInfo],
    on_progress: Optional[callable] = None,
    max_depth: int = 10
) -> List[HierarchyNode]:
    """
    Extract full document hierarchy with dynamic child discovery.

    Starts from full document and recursively discovers structure.

    Args:
        line_infos: Full list of LineInfo from document
        on_progress: Optional callback for progress updates
        max_depth: Maximum recursion depth (default 10)

    Returns:
        List of top-level HierarchyNode with nested children
    """
    if not line_infos:
        return []

    start_line = line_infos[0].line_num
    end_line = line_infos[-1].line_num

    return extract_hierarchy_dynamic(
        line_infos,
        start_line,
        end_line,
        level=0,
        max_depth=max_depth,
        on_progress=on_progress
    )


# Keep old function for backward compatibility / fixed hierarchy use
def extract_hierarchy_fixed(
    line_infos: List[LineInfo],
    hierarchy_types: List[str],
    start_line: int,
    end_line: int,
    level: int = 0,
    on_progress: Optional[callable] = None
) -> List[HierarchyNode]:
    """
    Recursively extract using fixed hierarchy types.

    Use this when you know the exact hierarchy structure.

    Args:
        line_infos: Full list of LineInfo from document
        hierarchy_types: List of element types ["chapter", "section", "subsection"]
        start_line: First line of range to extract from
        end_line: Last line of range to extract from
        level: Current depth (0 = top level)
        on_progress: Optional callback for progress updates

    Returns:
        List of HierarchyNode with nested children
    """
    if level >= len(hierarchy_types):
        return []

    element_type = hierarchy_types[level]

    if on_progress:
        on_progress(f"Extracting {element_type}s from lines {start_line}-{end_line}")

    segments = extract_level(line_infos, element_type, start_line, end_line)

    if on_progress:
        on_progress(f"  Found {len(segments)} {element_type}(s)")

    nodes = []
    for seg in segments:
        children = extract_hierarchy_fixed(
            line_infos,
            hierarchy_types,
            seg.start_line,
            seg.end_line,
            level + 1,
            on_progress
        )

        content = None
        if not children:
            content = get_content(line_infos, seg.start_line, seg.end_line)

        node = HierarchyNode(
            level=level + 1,
            type=seg.type,
            number=seg.number,
            title=seg.title,
            content=content,
            start_line=seg.start_line,
            end_line=seg.end_line,
            page=get_page_for_line(line_infos, seg.start_line),
            children=children
        )
        nodes.append(node)

    return nodes


def print_hierarchy(nodes: List[HierarchyNode], indent: int = 0):
    """Pretty print hierarchy for debugging."""
    for node in nodes:
        prefix = "  " * indent
        title_part = f" - {node.title}" if node.title else ""
        page_part = f" (p.{node.page}, lines {node.start_line}-{node.end_line})"
        print(f"{prefix}{node.type} {node.number}{title_part}{page_part}")
        if node.children:
            print_hierarchy(node.children, indent + 1)


def extract_level_by_level(
    line_infos: List[LineInfo],
    max_depth: int = 10,
    parallel: bool = False,
    max_workers: int = 5,
    on_level_complete: Optional[callable] = None,
    on_progress: Optional[callable] = None
) -> List[HierarchyNode]:
    """
    Extract hierarchy level-by-level (breadth-first).

    Extracts all nodes at level 1, then all at level 2, etc.
    Better for parallelization and progress visibility.

    Args:
        line_infos: Full list of LineInfo from document
        max_depth: Maximum levels to extract
        parallel: Whether to process parents in parallel (default False)
        max_workers: Max parallel workers (default 5)
        on_level_complete: Callback after each level: fn(level, nodes)
        on_progress: Callback for individual extractions

    Returns:
        List of top-level HierarchyNode with nested children
    """
    if not line_infos:
        return []

    start_line = line_infos[0].line_num
    end_line = line_infos[-1].line_num

    # Level 1: discover top-level children
    if on_progress:
        on_progress(f"Level 1: Discovering top-level elements...")

    segments = discover_children(line_infos, start_line, end_line)

    if not segments:
        return []

    # Build initial nodes (level 1)
    root_nodes = []
    for seg in segments:
        node = HierarchyNode(
            level=1,
            type=seg.type,
            number=seg.number,
            title=seg.title,
            content=None,
            start_line=seg.start_line,
            end_line=seg.end_line,
            page=get_page_for_line(line_infos, seg.start_line),
            children=[]
        )
        root_nodes.append(node)

    if on_level_complete:
        on_level_complete(1, root_nodes)

    # Process level by level
    current_level = 1
    nodes_at_current_level = root_nodes

    while current_level < max_depth and nodes_at_current_level:
        next_level = current_level + 1
        nodes_at_next_level = []

        # Filter parents that need processing
        parents_to_process = [
            p for p in nodes_at_current_level
            if p.end_line - p.start_line >= 2
        ]

        if on_progress:
            mode = f"parallel, {max_workers} workers" if parallel else "sequential"
            on_progress(f"Level {next_level}: Processing {len(parents_to_process)} parent nodes ({mode})...")

        if parallel and len(parents_to_process) > 1:
            # Parallel extraction
            def process_parent(parent):
                child_segments = discover_children(line_infos, parent.start_line, parent.end_line)
                return parent, child_segments

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_parent, p): p for p in parents_to_process}

                for future in as_completed(futures):
                    parent, child_segments = future.result()

                    if on_progress:
                        on_progress(f"  {parent.type} {parent.number}: {len(child_segments)} children")

                    for seg in child_segments:
                        # Skip if child has same range as parent (LLM returned parent as child)
                        if seg.start_line == parent.start_line and seg.end_line == parent.end_line:
                            continue
                        child_node = HierarchyNode(
                            level=next_level,
                            type=seg.type,
                            number=seg.number,
                            title=seg.title,
                            content=None,
                            start_line=seg.start_line,
                            end_line=seg.end_line,
                            page=get_page_for_line(line_infos, seg.start_line),
                            children=[]
                        )
                        parent.children.append(child_node)
                        nodes_at_next_level.append(child_node)
        else:
            # Sequential extraction
            for parent in parents_to_process:
                if on_progress:
                    on_progress(f"  {parent.type} {parent.number}: lines {parent.start_line}-{parent.end_line}")

                child_segments = discover_children(line_infos, parent.start_line, parent.end_line)

                for seg in child_segments:
                    # Skip if child has same range as parent (LLM returned parent as child)
                    if seg.start_line == parent.start_line and seg.end_line == parent.end_line:
                        continue
                    child_node = HierarchyNode(
                        level=next_level,
                        type=seg.type,
                        number=seg.number,
                        title=seg.title,
                        content=None,
                        start_line=seg.start_line,
                        end_line=seg.end_line,
                        page=get_page_for_line(line_infos, seg.start_line),
                        children=[]
                    )
                    parent.children.append(child_node)
                    nodes_at_next_level.append(child_node)

        if on_level_complete and nodes_at_next_level:
            on_level_complete(next_level, nodes_at_next_level)

        # Move to next level
        current_level = next_level
        nodes_at_current_level = nodes_at_next_level

    # Fill content for leaf nodes
    _fill_leaf_content(root_nodes, line_infos)

    return root_nodes


def _fill_leaf_content(nodes: List[HierarchyNode], line_infos: List[LineInfo]):
    """Fill content for leaf nodes (nodes with no children)."""
    for node in nodes:
        if node.children:
            _fill_leaf_content(node.children, line_infos)
        else:
            node.content = get_content(line_infos, node.start_line, node.end_line)


# Prompt to find missing title (marginal note)
FIND_TITLE_PROMPT = """This is a {element_type} from a legal document. The title/heading may appear as a marginal note within the text.

Find the title or heading for this {element_type}. Look for:
- Short phrases in title case
- Marginal notes (often 2-5 words describing what the section is about)
- Headings that describe the purpose of this section

If you find a title, return it. If no title exists, return null.

TEXT ({element_type} {number}, lines {start_line}-{end_line}):
{text}
"""


def find_missing_title(
    line_infos: List[LineInfo],
    node_type: str,
    node_number: str,
    start_line: int,
    end_line: int
) -> Optional[str]:
    """
    Find title for a node that's missing one (e.g., from marginal notes).

    Uses LLM to identify title/heading within the node's text.
    """
    text = get_content(line_infos, start_line, end_line)

    if not text.strip():
        return None

    prompt = FIND_TITLE_PROMPT.format(
        element_type=node_type,
        number=node_number,
        start_line=start_line,
        end_line=end_line,
        text=text[:2000]  # Limit text length
    )

    client = get_client()
    model = get_model()

    response = client.beta.messages.create(
        model=model,
        max_tokens=200,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {"role": "user", "content": prompt}
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]}
                },
                "required": ["title"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return result.get("title")


def fill_missing_titles(
    nodes: List[HierarchyNode],
    line_infos: List[LineInfo],
    on_progress: Optional[callable] = None
):
    """
    Post-process to fill in missing titles using LLM.

    Only calls LLM for nodes where title is None.
    """
    nodes_missing_title = []

    def collect_missing(node_list):
        for node in node_list:
            if node.title is None:
                nodes_missing_title.append(node)
            if node.children:
                collect_missing(node.children)

    collect_missing(nodes)

    if not nodes_missing_title:
        return

    if on_progress:
        on_progress(f"Finding titles for {len(nodes_missing_title)} nodes...")

    for node in nodes_missing_title:
        if on_progress:
            on_progress(f"  {node.type} {node.number}: looking for title...")

        title = find_missing_title(
            line_infos,
            node.type,
            node.number,
            node.start_line,
            node.end_line
        )

        if title:
            node.title = title
            if on_progress:
                on_progress(f"    Found: {title}")
