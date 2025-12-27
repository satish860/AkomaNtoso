"""Unified document extraction - orchestrates all extractors."""
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel

from .structure_analyzer import analyze_structure, get_hierarchy
from .metadata_extractor import extract_metadata, ActMetadata
from .chapter_extractor import extract_chapters, get_chapter_text, Chapter
from .section_extractor import extract_sections, Section
from .subsection_extractor import extract_subsections, SubSection
from .clause_extractor import extract_clauses, Clause
from .subclause_extractor import extract_subclauses, SubClause


class ExtractedSubClause(BaseModel):
    """Subclause with extracted content."""
    numeral: str  # i, ii, iii
    content: str


class ExtractedClause(BaseModel):
    """Clause with nested subclauses."""
    letter: str  # a, b, c
    content: str
    subclauses: List[ExtractedSubClause] = []


class ExtractedSubSection(BaseModel):
    """Subsection with extracted content and clauses."""
    number: int
    content: str
    clauses: List[ExtractedClause] = []


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
    on_progress: Optional[Callable[[str], None]] = None,
    parallel: bool = False,
    max_workers: int = 3
) -> Document:
    """
    Extract full document structure using all extractors.

    Args:
        text: Cleaned document text
        extract_subsections_flag: Whether to extract subsections (default True)
        on_progress: Optional callback for progress updates
        parallel: Whether to extract chapters in parallel (default False)
        max_workers: Max parallel workers (default 3 to avoid rate limits)

    Returns:
        Document with metadata, hierarchy, and nested chapters/sections
    """
    import threading
    lock = threading.Lock()

    def report(msg: str):
        if on_progress:
            with lock:
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

    def extract_single_chapter(ch, idx):
        """Extract all content for a single chapter."""
        report(f"  Chapter {ch.number} ({idx}/{len(chapters_raw)}): {ch.title}")
        chapter_text = get_chapter_text(text, ch)

        # Extract sections for this chapter
        sections_raw = extract_sections(chapter_text, chapter_num=ch.number)
        report(f"    [Chapter {ch.number}] Found {len(sections_raw)} sections")

        extracted_sections = []
        for sec in sections_raw:
            extracted_subsections = []

            # Extract subsections if enabled and in hierarchy
            if extract_subsections_flag and "subsections" in hierarchy:
                report(f"    [Chapter {ch.number}] Section {sec.number}: extracting subsections...")
                try:
                    subsections_raw = extract_subsections(chapter_text, section_num=sec.number)
                    if subsections_raw:
                        report(f"      [Chapter {ch.number}] Section {sec.number}: {len(subsections_raw)} subsections")

                    for sub in subsections_raw:
                        extracted_clauses = []

                        # Extract clauses if in hierarchy
                        if "clauses" in hierarchy:
                            report(f"      [Chapter {ch.number}] Sec {sec.number} Sub ({sub.number}): extracting clauses...")
                            try:
                                clauses_raw = extract_clauses(chapter_text, section_num=sec.number, subsection_num=sub.number)
                                if clauses_raw:
                                    report(f"        [Chapter {ch.number}] Found {len(clauses_raw)} clauses")

                                for clause in clauses_raw:
                                    extracted_subclauses = []

                                    # Extract subclauses if in hierarchy
                                    if "subclauses" in hierarchy:
                                        try:
                                            subclauses_raw = extract_subclauses(chapter_text, section_num=sec.number, clause_letter=clause.letter)
                                            extracted_subclauses = [
                                                ExtractedSubClause(numeral=sc.numeral, content=sc.content)
                                                for sc in subclauses_raw
                                            ]
                                            if extracted_subclauses:
                                                report(f"          [Chapter {ch.number}] Clause ({clause.letter}): {len(extracted_subclauses)} subclauses")
                                        except Exception:
                                            pass

                                    extracted_clauses.append(ExtractedClause(
                                        letter=clause.letter,
                                        content=clause.content,
                                        subclauses=extracted_subclauses
                                    ))
                            except Exception:
                                pass

                        extracted_subsections.append(ExtractedSubSection(
                            number=sub.number,
                            content=sub.content,
                            clauses=extracted_clauses
                        ))
                except Exception:
                    # Some sections may not have subsections
                    pass

            extracted_sections.append(ExtractedSection(
                number=sec.number,
                heading=sec.heading,
                subsections=extracted_subsections
            ))

        return ExtractedChapter(
            number=ch.number,
            title=ch.title,
            start_line=ch.start_line,
            end_line=ch.end_line,
            sections=extracted_sections
        )

    # Extract chapters (parallel or sequential)
    if parallel:
        report(f"  [Parallel mode: {max_workers} workers]")
        extracted_chapters = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(extract_single_chapter, ch, i): ch
                for i, ch in enumerate(chapters_raw, 1)
            }
            for future in as_completed(futures):
                extracted_chapters.append(future.result())
        # Sort by chapter number to maintain order
        extracted_chapters.sort(key=lambda c: c.start_line)
    else:
        extracted_chapters = [
            extract_single_chapter(ch, i)
            for i, ch in enumerate(chapters_raw, 1)
        ]

    report("Extraction complete!")

    return Document(
        metadata=metadata,
        hierarchy=hierarchy,
        chapters=extracted_chapters
    )
