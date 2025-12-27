"""Akoma Ntoso XML generator."""
import re
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


def _generate_subsection(section: etree.Element, sec_num: int, subsec) -> None:
    """Generate subsection element."""
    eid = f"sec_{sec_num}__subsec_{subsec.number}"
    subsec_elem = _sub(section, "subsection", eId=eid)
    _sub(subsec_elem, "num", text=f"({subsec.number})")
    content = _sub(subsec_elem, "content")
    _sub(content, "p", text=subsec.content)


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
