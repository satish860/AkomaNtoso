"""Unified document extraction - orchestrates all extractors."""
from typing import List, Optional, Callable
from pydantic import BaseModel

from .structure_analyzer import analyze_structure, get_hierarchy
from .metadata_extractor import extract_metadata, ActMetadata
from .chapter_extractor import extract_chapters, get_chapter_text, Chapter
from .section_extractor import extract_sections, Section
from .subsection_extractor import extract_subsections, SubSection


class ExtractedSubSection(BaseModel):
    """Subsection with extracted content."""
    number: int
    content: str


class ExtractedSection(BaseModel):
    """Section with nested subsections."""
    number: int
    heading: Optional[str] = None
    subsections: List[ExtractedSubSection] = []


class ExtractedChapter(BaseModel):
    """Chapter with nested sections."""
    number: str
    title: str
    start_line: int
    end_line: int
    sections: List[ExtractedSection] = []


class Document(BaseModel):
    """Full extracted document structure."""
    metadata: ActMetadata
    hierarchy: List[str]
    chapters: List[ExtractedChapter] = []


def extract_document(
    text: str,
    extract_subsections_flag: bool = True,
    on_progress: Optional[Callable[[str], None]] = None
) -> Document:
    """
    Extract full document structure using all extractors.

    Args:
        text: Cleaned document text
        extract_subsections_flag: Whether to extract subsections (default True)
        on_progress: Optional callback for progress updates

    Returns:
        Document with metadata, hierarchy, and nested chapters/sections
    """
    def report(msg: str):
        if on_progress:
            on_progress(msg)

    # Step 1: Analyze structure to get hierarchy
    report("Step 1/4: Analyzing document structure...")
    structure = analyze_structure(text)
    hierarchy = get_hierarchy(structure)
    report(f"  Hierarchy: {' > '.join(hierarchy)}")

    # Step 2: Extract metadata
    report("Step 2/4: Extracting metadata...")
    metadata = extract_metadata(text)
    report(f"  Title: {metadata.title[:50]}...")

    # Step 3: Extract chapters
    report("Step 3/4: Extracting chapters...")
    chapters_raw = extract_chapters(text)
    report(f"  Found {len(chapters_raw)} chapters")

    # Step 4: For each chapter, extract sections
    report("Step 4/4: Extracting sections from each chapter...")
    extracted_chapters = []

    for i, ch in enumerate(chapters_raw, 1):
        report(f"  Chapter {ch.number} ({i}/{len(chapters_raw)}): {ch.title}")
        chapter_text = get_chapter_text(text, ch)

        # Extract sections for this chapter
        sections_raw = extract_sections(chapter_text, chapter_num=ch.number)
        report(f"    Found {len(sections_raw)} sections")

        extracted_sections = []
        for sec in sections_raw:
            extracted_subsections = []

            # Extract subsections if enabled and in hierarchy
            if extract_subsections_flag and "subsections" in hierarchy:
                report(f"    Section {sec.number}: extracting subsections...")
                try:
                    subsections_raw = extract_subsections(chapter_text, section_num=sec.number)
                    extracted_subsections = [
                        ExtractedSubSection(number=sub.number, content=sub.content)
                        for sub in subsections_raw
                    ]
                    if extracted_subsections:
                        report(f"      Found {len(extracted_subsections)} subsections")
                except Exception:
                    # Some sections may not have subsections
                    pass

            extracted_sections.append(ExtractedSection(
                number=sec.number,
                heading=sec.heading,
                subsections=extracted_subsections
            ))

        extracted_chapters.append(ExtractedChapter(
            number=ch.number,
            title=ch.title,
            start_line=ch.start_line,
            end_line=ch.end_line,
            sections=extracted_sections
        ))

    report("Extraction complete!")

    return Document(
        metadata=metadata,
        hierarchy=hierarchy,
        chapters=extracted_chapters
    )
