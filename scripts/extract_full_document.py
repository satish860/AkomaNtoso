"""Script to extract full document hierarchy with progress output.

Usage:
    python scripts/extract_full_document.py [pdf_path]

Examples:
    python scripts/extract_full_document.py data/irish_si_607.pdf
    python scripts/extract_full_document.py  # Uses default DPDP Act
"""
import sys
import time
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from src.extractor.line_numbered_extractor import extract_with_line_info
from src.parser.level_extractor import extract_level_by_level, print_hierarchy


def count_nodes(nodes):
    """Count total nodes in hierarchy."""
    total = len(nodes)
    for n in nodes:
        total += count_nodes(n.children)
    return total


def main():
    parser = argparse.ArgumentParser(description="Extract document hierarchy from PDF")
    parser.add_argument("pdf_path", nargs="?", default="data/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf",
                        help="Path to PDF file (default: DPDP Act)")
    parser.add_argument("--max-depth", type=int, default=10, help="Maximum hierarchy depth")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel workers")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between LLM calls (seconds)")
    parser.add_argument("--sequential", action="store_true", help="Disable parallel processing")
    args = parser.parse_args()

    pdf_path = args.pdf_path
    max_depth = args.max_depth
    parallel = not args.sequential
    max_workers = args.workers
    call_delay = args.delay

    # Derive output filename from input
    pdf_name = Path(pdf_path).stem
    output_path = Path(f"output/{pdf_name}_hierarchy.json")

    print("=" * 60)
    print(f"Hierarchy Extraction: {Path(pdf_path).name}")
    print("=" * 60)
    print()

    # Load PDF
    print(f"Loading PDF: {pdf_path}")
    line_infos, _ = extract_with_line_info(pdf_path)
    print(f"Total lines: {len(line_infos)}")
    print(f"Pages: {line_infos[0].page} to {line_infos[-1].page}")
    print()

    # Callback to show level completion
    def on_level_complete(level, nodes):
        print()
        print(f"{'=' * 60}")
        print(f"LEVEL {level} COMPLETE - Found {len(nodes)} nodes:")
        print(f"{'=' * 60}")
        for node in nodes:
            title = f" - {node.title[:40]}..." if node.title and len(node.title) > 40 else (f" - {node.title}" if node.title else "")
            print(f"  {node.type} {node.number}{title} (p.{node.page}, lines {node.start_line}-{node.end_line})")
        print()

    # Extract hierarchy level by level
    mode = f"parallel with {max_workers} workers" if parallel else "sequential"
    print(f"Extracting hierarchy level-by-level ({mode}, {call_delay}s delay)...")
    print("-" * 60)

    start = time.time()

    nodes = extract_level_by_level(
        line_infos,
        max_depth=max_depth,
        parallel=parallel,
        max_workers=max_workers,
        call_delay=call_delay,
        on_level_complete=on_level_complete,
        on_progress=print
    )

    elapsed = time.time() - start
    print("-" * 60)
    print(f"Extraction completed in {elapsed:.1f} seconds")
    print()

    # Summary
    total = count_nodes(nodes)
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total nodes extracted: {total}")
    print()

    print("Top-level structure:")
    for node in nodes:
        child_count = count_nodes(node.children)
        title = node.title[:40] + "..." if node.title and len(node.title) > 40 else node.title
        print(f"  {node.type} {node.number}: {title} ({child_count} descendants)")

    print()
    print("=" * 60)
    print("FULL HIERARCHY")
    print("=" * 60)
    print_hierarchy(nodes)

    # Export to JSON
    output_path.parent.mkdir(exist_ok=True)

    # Convert nodes to JSON-serializable format
    def node_to_dict(node):
        return {
            "level": node.level,
            "type": node.type,
            "number": node.number,
            "title": node.title,
            "start_line": node.start_line,
            "end_line": node.end_line,
            "page": node.page,
            "content": node.content,
            "children": [node_to_dict(c) for c in node.children]
        }

    output_data = {
        "source_pdf": pdf_path,
        "total_lines": len(line_infos),
        "total_nodes": total,
        "extraction_time_seconds": round(elapsed, 1),
        "hierarchy": [node_to_dict(n) for n in nodes]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print(f"JSON exported to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
