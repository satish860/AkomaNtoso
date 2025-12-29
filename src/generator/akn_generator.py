"""Akoma Ntoso XML generator."""
import re
import json
from typing import Dict, List, Any, Optional
from lxml import etree
from datetime import date, datetime
from src.parser.document_extractor import Document

# AKN 3.0 namespace
AKN_NAMESPACE = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
NSMAP = {None: AKN_NAMESPACE}


def normalize_date(date_str: str) -> str:
    """
    Convert various date formats to ISO format (YYYY-MM-DD).

    Examples:
        "11th August, 2023" -> "2023-08-11"
        "2023-08-11" -> "2023-08-11"
        "August 11, 2023" -> "2023-08-11"
    """
    if not date_str:
        return date.today().isoformat()

    # Already ISO format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Try various formats
    formats = [
        "%d %B, %Y",      # "11 August, 2023"
        "%dth %B, %Y",    # "11th August, 2023"
        "%dst %B, %Y",    # "1st August, 2023"
        "%dnd %B, %Y",    # "2nd August, 2023"
        "%drd %B, %Y",    # "3rd August, 2023"
        "%B %d, %Y",      # "August 11, 2023"
        "%d %B %Y",       # "11 August 2023"
        "%d/%m/%Y",       # "11/08/2023"
    ]

    # Remove ordinal suffixes (st, nd, rd, th)
    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Fallback: return as-is if can't parse
    return date_str


def _el(tag: str, text: str = None, **attrs) -> etree.Element:
    """Create an element with optional text and attributes."""
    elem = etree.Element(f"{{{AKN_NAMESPACE}}}{tag}", nsmap=NSMAP)
    if text:
        elem.text = text
    for key, value in attrs.items():
        elem.set(key, str(value))
    return elem


def _sub(parent: etree.Element, tag: str, text: str = None, **attrs) -> etree.Element:
    """Create and append a subelement."""
    elem = etree.SubElement(parent, f"{{{AKN_NAMESPACE}}}{tag}")
    if text:
        elem.text = text
    for key, value in attrs.items():
        elem.set(key, str(value))
    return elem


def _generate_frbr_work(identification: etree.Element, doc: Document) -> None:
    """Generate FRBRWork metadata."""
    meta = doc.metadata
    year = meta.year
    num = meta.act_number
    enacted = normalize_date(meta.date_enacted) if meta.date_enacted else f"{year}-01-01"

    work = _sub(identification, "FRBRWork")
    _sub(work, "FRBRthis", value=f"/in/act/{year}/{num}/main")
    _sub(work, "FRBRuri", value=f"/in/act/{year}/{num}")
    _sub(work, "FRBRcountry", value="in")
    _sub(work, "FRBRdate", date=enacted, name="enacted")
    _sub(work, "FRBRnumber", value=str(num))
    _sub(work, "FRBRname", value=meta.short_title or meta.title)


def _generate_frbr_expression(identification: etree.Element, doc: Document) -> None:
    """Generate FRBRExpression metadata."""
    meta = doc.metadata
    year = meta.year
    num = meta.act_number
    enacted = normalize_date(meta.date_enacted) if meta.date_enacted else f"{year}-01-01"

    expr = _sub(identification, "FRBRExpression")
    _sub(expr, "FRBRthis", value=f"/in/act/{year}/{num}/eng@{enacted}/main")
    _sub(expr, "FRBRuri", value=f"/in/act/{year}/{num}/eng@{enacted}")
    _sub(expr, "FRBRdate", date=enacted, name="publication")
    _sub(expr, "FRBRlanguage", language="eng")


def _generate_frbr_manifestation(identification: etree.Element, doc: Document) -> None:
    """Generate FRBRManifestation metadata."""
    meta = doc.metadata
    year = meta.year
    num = meta.act_number
    enacted = normalize_date(meta.date_enacted) if meta.date_enacted else f"{year}-01-01"
    today = date.today().isoformat()

    manif = _sub(identification, "FRBRManifestation")
    _sub(manif, "FRBRthis", value=f"/in/act/{year}/{num}/eng@{enacted}/main.xml")
    _sub(manif, "FRBRuri", value=f"/in/act/{year}/{num}/eng@{enacted}/main.xml")
    _sub(manif, "FRBRdate", date=today, name="transform")


def _generate_meta(act: etree.Element, doc: Document) -> None:
    """Generate meta element with FRBR identification."""
    meta_elem = _sub(act, "meta")
    identification = _sub(meta_elem, "identification", source="#source")

    _generate_frbr_work(identification, doc)
    _generate_frbr_expression(identification, doc)
    _generate_frbr_manifestation(identification, doc)


def _generate_subclause(clause_elem: etree.Element, sec_num: int, clause_letter: str, subclause) -> None:
    """Generate subclause element."""
    eid = f"sec_{sec_num}__clause_{clause_letter}__subclause_{subclause.numeral}"
    subclause_elem = _sub(clause_elem, "paragraph", eId=eid)
    _sub(subclause_elem, "num", text=f"({subclause.numeral})")
    content = _sub(subclause_elem, "content")
    _sub(content, "p", text=subclause.content)


def _generate_clause(subsec_elem: etree.Element, sec_num: int, subsec_num: int, clause) -> None:
    """Generate clause element."""
    eid = f"sec_{sec_num}__subsec_{subsec_num}__clause_{clause.letter}"
    clause_elem = _sub(subsec_elem, "paragraph", eId=eid)
    _sub(clause_elem, "num", text=f"({clause.letter})")
    content = _sub(clause_elem, "content")
    _sub(content, "p", text=clause.content)

    # Generate subclauses
    for subclause in clause.subclauses:
        _generate_subclause(clause_elem, sec_num, clause.letter, subclause)


def _generate_subsection(section: etree.Element, sec_num: int, subsec) -> None:
    """Generate subsection element."""
    eid = f"sec_{sec_num}__subsec_{subsec.number}"
    subsec_elem = _sub(section, "subsection", eId=eid)
    _sub(subsec_elem, "num", text=f"({subsec.number})")

    # Add content if present
    if subsec.content:
        content = _sub(subsec_elem, "content")
        _sub(content, "p", text=subsec.content)

    # Generate clauses
    for clause in subsec.clauses:
        _generate_clause(subsec_elem, sec_num, subsec.number, clause)


def _generate_section(chapter: etree.Element, sec) -> None:
    """Generate section element."""
    eid = f"sec_{sec.number}"
    sec_elem = _sub(chapter, "section", eId=eid)
    _sub(sec_elem, "num", text=f"{sec.number}.")
    if sec.heading:
        _sub(sec_elem, "heading", text=sec.heading)

    # Generate subsections
    for subsec in sec.subsections:
        _generate_subsection(sec_elem, sec.number, subsec)


def _generate_chapter(body: etree.Element, ch) -> None:
    """Generate chapter element."""
    eid = f"chp_{ch.number}"
    ch_elem = _sub(body, "chapter", eId=eid)
    _sub(ch_elem, "num", text=f"CHAPTER {ch.number}")
    _sub(ch_elem, "heading", text=ch.title)

    # Generate sections
    for sec in ch.sections:
        _generate_section(ch_elem, sec)


def _generate_body(act: etree.Element, doc: Document) -> None:
    """Generate body element with chapters and sections."""
    body = _sub(act, "body")

    for ch in doc.chapters:
        _generate_chapter(body, ch)


def generate_akn(doc: Document) -> str:
    """
    Generate Akoma Ntoso XML from extracted document.

    Args:
        doc: Extracted Document object

    Returns:
        XML string in AKN 3.0 format
    """
    # Create root element
    root = _el("akomaNtoso")

    # Create act element
    act_name = doc.metadata.short_title or doc.metadata.title
    act_name = act_name.replace(" ", "").replace(",", "").replace(".", "")
    act = _sub(root, "act", name=act_name)

    # Generate meta
    _generate_meta(act, doc)

    # Generate body
    _generate_body(act, doc)

    # Convert to string
    xml_str = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    ).decode("utf-8")

    return xml_str


# =============================================================================
# NEW: Generate AKN from JSON hierarchy
# =============================================================================

# Mapping from our hierarchy types to AKN element names
TYPE_TO_AKN = {
    "chapter": "chapter",
    "part": "part",
    "section": "section",
    "subsection": "subsection",
    "clause": "paragraph",
    "sub-clause": "paragraph",
    "subclause": "paragraph",
    "definition": "paragraph",
    "rule": "rule",
    "regulation": "rule",
    "article": "article",
    "paragraph": "paragraph",
    "subparagraph": "paragraph",
    "schedule": "attachment",
}


def _sanitize_eid(text: str) -> str:
    """Sanitize text for use in eId attribute."""
    if not text:
        return ""
    # Remove parentheses, convert to lowercase, replace spaces with underscore
    result = re.sub(r'[().\s]+', '_', text.lower())
    result = re.sub(r'_+', '_', result)  # collapse multiple underscores
    result = result.strip('_')
    return result


def _build_eid(ancestors: List[str], node_type: str, node_number: str) -> str:
    """Build hierarchical eId from ancestors."""
    sanitized_num = _sanitize_eid(node_number)
    type_abbrev = {
        "chapter": "chp",
        "part": "part",
        "section": "sec",
        "subsection": "subsec",
        "clause": "cl",
        "sub-clause": "subcl",
        "subclause": "subcl",
        "definition": "def",
        "rule": "rule",
        "paragraph": "para",
        "article": "art",
    }.get(node_type, node_type[:3])

    current = f"{type_abbrev}_{sanitized_num}"
    if ancestors:
        return "__".join(ancestors + [current])
    return current


def _generate_hierarchy_node(
    parent_elem: etree.Element,
    node: Dict[str, Any],
    ancestors: List[str]
) -> None:
    """Recursively generate AKN elements from hierarchy node."""
    node_type = node.get("type", "unknown")
    node_number = node.get("number", "")
    node_title = node.get("title")
    node_content = node.get("content")
    children = node.get("children", [])

    # Determine AKN element type
    akn_type = TYPE_TO_AKN.get(node_type, "hcontainer")

    # Build eId
    eid = _build_eid(ancestors, node_type, node_number)

    # Create element - hcontainer requires 'name' attribute
    if akn_type == "hcontainer":
        elem = _sub(parent_elem, akn_type, eId=eid, name=node_type)
    else:
        elem = _sub(parent_elem, akn_type, eId=eid)

    # Add num element
    if node_number:
        # Format number appropriately
        if node_type == "chapter":
            num_text = f"CHAPTER {node_number}"
        elif node_type == "part":
            num_text = f"PART {node_number}"
        elif node_type == "section":
            num_text = f"{node_number}."
        else:
            num_text = node_number
        _sub(elem, "num", text=num_text)

    # Add heading if present
    if node_title:
        _sub(elem, "heading", text=node_title)

    # If leaf node with content, add content element
    if node_content and not children:
        content_elem = _sub(elem, "content")
        # Split content into paragraphs
        paragraphs = node_content.strip().split('\n')
        for para in paragraphs:
            if para.strip():
                _sub(content_elem, "p", text=para.strip())

    # Recursively process children
    new_ancestors = ancestors + [_build_eid([], node_type, node_number)]
    for child in children:
        _generate_hierarchy_node(elem, child, new_ancestors)


def generate_akn_from_hierarchy(
    hierarchy_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate Akoma Ntoso XML from JSON hierarchy.

    Args:
        hierarchy_data: Dictionary with 'hierarchy' key containing nodes
        metadata: Optional metadata dict with title, year, act_number, date_enacted

    Returns:
        XML string in AKN 3.0 format
    """
    # Extract metadata
    if metadata is None:
        metadata = {}

    title = metadata.get("title", "Untitled Act")
    year = metadata.get("year", date.today().year)
    act_number = metadata.get("act_number", 1)
    date_enacted = metadata.get("date_enacted", f"{year}-01-01")

    # Normalize date
    if date_enacted and not re.match(r'^\d{4}-\d{2}-\d{2}$', date_enacted):
        date_enacted = normalize_date(date_enacted)

    # Create root element
    root = _el("akomaNtoso")

    # Create act element
    act_name = re.sub(r'[,.\s]+', '', title)
    act = _sub(root, "act", name=act_name)

    # Generate meta
    meta_elem = _sub(act, "meta")
    identification = _sub(meta_elem, "identification", source="#source")

    # FRBRWork - order: FRBRthis, FRBRuri, FRBRdate, FRBRauthor, FRBRcountry, FRBRnumber, FRBRname
    work = _sub(identification, "FRBRWork")
    _sub(work, "FRBRthis", value=f"/in/act/{year}/{act_number}/main")
    _sub(work, "FRBRuri", value=f"/in/act/{year}/{act_number}")
    _sub(work, "FRBRdate", date=date_enacted, name="enacted")
    _sub(work, "FRBRauthor", href="#parliament")
    _sub(work, "FRBRcountry", value="in")
    _sub(work, "FRBRnumber", value=str(act_number))
    _sub(work, "FRBRname", value=title)

    # FRBRExpression - order: FRBRthis, FRBRuri, FRBRdate, FRBRauthor, FRBRlanguage
    expr = _sub(identification, "FRBRExpression")
    _sub(expr, "FRBRthis", value=f"/in/act/{year}/{act_number}/eng@{date_enacted}/main")
    _sub(expr, "FRBRuri", value=f"/in/act/{year}/{act_number}/eng@{date_enacted}")
    _sub(expr, "FRBRdate", date=date_enacted, name="publication")
    _sub(expr, "FRBRauthor", href="#parliament")
    _sub(expr, "FRBRlanguage", language="eng")

    # FRBRManifestation - order: FRBRthis, FRBRuri, FRBRdate, FRBRauthor
    today = date.today().isoformat()
    manif = _sub(identification, "FRBRManifestation")
    _sub(manif, "FRBRthis", value=f"/in/act/{year}/{act_number}/eng@{date_enacted}/main.xml")
    _sub(manif, "FRBRuri", value=f"/in/act/{year}/{act_number}/eng@{date_enacted}/main.xml")
    _sub(manif, "FRBRdate", date=today, name="transform")
    _sub(manif, "FRBRauthor", href="#converter")

    # Generate body
    body = _sub(act, "body")

    # Process hierarchy nodes
    hierarchy = hierarchy_data.get("hierarchy", [])
    for node in hierarchy:
        _generate_hierarchy_node(body, node, [])

    # Convert to string
    xml_str = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    ).decode("utf-8")

    return xml_str


def generate_akn_from_json_file(json_path: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate AKN XML from JSON hierarchy file.

    Args:
        json_path: Path to JSON hierarchy file
        output_path: Path for output XML file
        metadata: Optional metadata overrides

    Returns:
        Path to generated XML file
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        hierarchy_data = json.load(f)

    xml_str = generate_akn_from_hierarchy(hierarchy_data, metadata)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)

    return output_path
