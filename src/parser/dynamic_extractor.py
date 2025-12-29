"""Dynamic hierarchy extraction - works with any legal document structure."""
import json
from typing import List, Optional, Callable
from pydantic import BaseModel
from .llm_client import get_client, get_model


class HierarchyNode(BaseModel):
    """A node in the document hierarchy - works for any jurisdiction/document type."""
    level: int                          # 1 = top level, 2 = child, etc.
    type: str                           # "chapter", "section", "rule", "article", etc.
    number: str                         # "I", "1", "(a)", "i", etc.
    title: Optional[str] = None         # Optional heading/title
    content: Optional[str] = None       # Leaf node content
    children: List["HierarchyNode"] = []


# Enable self-referencing
HierarchyNode.model_rebuild()


class DocumentStructure(BaseModel):
    """Analyzed document structure."""
    document_type: str                  # "act", "rules", "regulation", "bill", etc.
    jurisdiction: str                   # "India", "UK", "USA", etc.
    hierarchy_types: List[str]          # ["chapter", "section", "subsection"] or ["rule", "subrule", "clause"]
    title: str
    enactment_date: Optional[str] = None
    number: Optional[str] = None        # Act number, Rule number, etc.


ANALYZE_STRUCTURE_PROMPT = """Analyze this legal document and identify its structure.

Determine:
1. document_type: What kind of document is this? (act, rules, regulation, bill, ordinance, notification, etc.)
2. jurisdiction: Which country/state? (India, UK, USA, etc.)
3. hierarchy_types: What are the hierarchical levels used? List from top to bottom.
   Examples:
   - Indian Act: ["chapter", "section", "subsection", "clause", "subclause"]
   - Indian Rules: ["rule", "subrule", "clause", "subclause"]
   - UK Act: ["part", "section", "subsection"]
   - US Code: ["title", "chapter", "section", "subsection"]
4. title: The full title of the document
5. enactment_date: When was it enacted/notified (if mentioned)
6. number: Document number (e.g., "Act No. 22 of 2023", "G.S.R. 760(E)")

DOCUMENT TEXT (first 2000 chars):
{text}
"""


EXTRACT_HIERARCHY_PROMPT = """Extract the complete hierarchical structure of this legal document.

Document type: {document_type}
Hierarchy levels: {hierarchy_types}

Extract ALL nodes at each level. For each node provide:
- level: 1 for top level ({top_level}), 2 for next level, etc.
- type: The type of node (from hierarchy_types)
- number: The number/identifier (e.g., "I", "1", "(a)", "i")
- title: The heading/title if present (null if none)
- content: The actual text content (for leaf nodes or nodes with direct content)
- children: Nested child nodes

IMPORTANT:
- Capture the FULL hierarchy with all nested levels
- Include all content - don't summarize
- Preserve exact numbering scheme used in document
- For bilingual documents, extract the English content only
- Every node must have children array (empty if leaf node)

DOCUMENT TEXT:
{text}
"""


def analyze_document_structure(text: str) -> DocumentStructure:
    """
    Analyze document to determine its type and hierarchy structure.
    Uses structured outputs for guaranteed schema compliance.

    Args:
        text: Document text (can be raw or cleaned)

    Returns:
        DocumentStructure with type, jurisdiction, and hierarchy levels
    """
    client = get_client()
    model = get_model()

    # Use first 2000 chars for structure analysis
    sample_text = text[:2000]

    response = client.beta.messages.create(
        model=model,
        max_tokens=1000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": ANALYZE_STRUCTURE_PROMPT.format(text=sample_text)
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "document_type": {"type": "string"},
                    "jurisdiction": {"type": "string"},
                    "hierarchy_types": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "title": {"type": "string"},
                    "enactment_date": {"type": ["string", "null"]},
                    "number": {"type": ["string", "null"]}
                },
                "required": ["document_type", "jurisdiction", "hierarchy_types", "title", "enactment_date", "number"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    return DocumentStructure(**result)


def _build_node_schema(max_depth: int) -> dict:
    """Build a flattened node schema (no recursion - that's not supported)."""
    # Since recursive schemas aren't supported, we'll use a flat array
    # and reconstruct the tree ourselves
    return {
        "type": "object",
        "properties": {
            "level": {"type": "integer"},
            "type": {"type": "string"},
            "number": {"type": "string"},
            "title": {"type": ["string", "null"]},
            "content": {"type": ["string", "null"]},
            "parent_number": {"type": ["string", "null"]}  # Reference to parent
        },
        "required": ["level", "type", "number", "title", "content", "parent_number"],
        "additionalProperties": False
    }


EXTRACT_FLAT_PROMPT = """Extract the complete hierarchical structure of this legal document as a FLAT list of nodes.

Document type: {document_type}
Hierarchy levels: {hierarchy_types}

Extract ALL nodes at each level. For each node provide:
- level: 1 for top level ({top_level}), 2 for next level, etc.
- type: The type of node (from hierarchy_types)
- number: The number/identifier (e.g., "I", "1", "(a)", "i")
- title: The heading/title if present (null if none)
- content: The actual text content (null if has children with content)
- parent_number: The number of the parent node (null for level 1)

IMPORTANT:
- Return a FLAT list - no nesting
- Use parent_number to indicate hierarchy (e.g., clause "(a)" under subsection "1" has parent_number "1")
- For level 1 nodes, parent_number is null
- For level 2+ nodes, parent_number is the number of immediate parent
- Include ALL nodes from the document
- For bilingual documents, extract the English content only

DOCUMENT TEXT:
{text}
"""


def extract_hierarchy(text: str, structure: DocumentStructure) -> List[HierarchyNode]:
    """
    Extract full document hierarchy based on analyzed structure.
    Uses flat extraction then reconstructs tree (since recursive schemas not supported).

    Args:
        text: Full document text
        structure: Analyzed document structure

    Returns:
        List of top-level HierarchyNode objects with nested children
    """
    client = get_client()
    model = get_model()

    response = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": EXTRACT_FLAT_PROMPT.format(
                    document_type=structure.document_type,
                    hierarchy_types=", ".join(structure.hierarchy_types),
                    top_level=structure.hierarchy_types[0] if structure.hierarchy_types else "section",
                    text=text
                )
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": _build_node_schema(len(structure.hierarchy_types))
                    }
                },
                "required": ["nodes"],
                "additionalProperties": False
            }
        }
    )

    result = json.loads(response.content[0].text)
    flat_nodes = result.get("nodes", [])

    # Reconstruct tree from flat list
    return _build_tree(flat_nodes)


def _build_tree(flat_nodes: List[dict]) -> List[HierarchyNode]:
    """Reconstruct tree from flat node list using parent_number references."""
    # Create nodes indexed by (level, number) for parent lookup
    node_map = {}
    all_nodes = []

    # First pass: create all nodes
    for data in flat_nodes:
        node = HierarchyNode(
            level=data.get("level", 1),
            type=data.get("type", "unknown"),
            number=data.get("number", ""),
            title=data.get("title"),
            content=data.get("content"),
            children=[]
        )
        key = (node.level, node.number)
        node_map[key] = node
        all_nodes.append((node, data.get("parent_number")))

    # Second pass: build tree by linking children to parents
    root_nodes = []
    for node, parent_number in all_nodes:
        if node.level == 1 or parent_number is None:
            root_nodes.append(node)
        else:
            # Find parent at level - 1
            parent_key = (node.level - 1, parent_number)
            parent = node_map.get(parent_key)
            if parent:
                parent.children.append(node)
            else:
                # Fallback: if parent not found, add to root
                root_nodes.append(node)

    return root_nodes


def extract_document_dynamic(
    text: str,
    on_progress: Optional[Callable[[str], None]] = None
) -> tuple[DocumentStructure, List[HierarchyNode]]:
    """
    Extract document using dynamic hierarchy detection.

    Args:
        text: Document text
        on_progress: Optional progress callback

    Returns:
        Tuple of (DocumentStructure, List[HierarchyNode])
    """
    def report(msg):
        if on_progress:
            on_progress(msg)

    report("Step 1/2: Analyzing document structure...")
    structure = analyze_document_structure(text)
    report(f"  Type: {structure.document_type}")
    report(f"  Jurisdiction: {structure.jurisdiction}")
    report(f"  Hierarchy: {' > '.join(structure.hierarchy_types)}")
    report(f"  Title: {structure.title[:60]}...")

    report("Step 2/2: Extracting hierarchy...")
    nodes = extract_hierarchy(text, structure)
    report(f"  Extracted {len(nodes)} top-level nodes")

    # Count total nodes
    def count_nodes(node_list):
        total = len(node_list)
        for n in node_list:
            total += count_nodes(n.children)
        return total

    total = count_nodes(nodes)
    report(f"  Total nodes: {total}")

    return structure, nodes


def print_hierarchy(nodes: List[HierarchyNode], indent: int = 0):
    """Pretty print the hierarchy for debugging."""
    for node in nodes:
        prefix = "  " * indent
        title_part = f" - {node.title}" if node.title else ""
        content_preview = ""
        if node.content:
            preview = node.content[:50].replace("\n", " ")
            content_preview = f" [{preview}...]"
        print(f"{prefix}{node.type} {node.number}{title_part}{content_preview}")
        if node.children:
            print_hierarchy(node.children, indent + 1)
