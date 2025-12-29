"""Convert PDF to Akoma Ntoso XML.

Complete pipeline: PDF -> JSON hierarchy -> AKN XML (validated)

Usage:
    python scripts/pdf_to_akn.py <pdf_path> [options]

Examples:
    # Indian Act
    python scripts/pdf_to_akn.py data/dpdp_act.pdf --title "Digital Personal Data Protection Act, 2023" --year 2023 --number 22 --date 2023-08-11

    # Irish Statutory Instrument
    python scripts/pdf_to_akn.py data/irish_si_607.pdf --title "European Union (Markets in Crypto-Assets) Regulations 2024" --year 2024 --number 607 --date 2024-11-08 --country ie --doc-type regulation

    # Quick run (metadata derived from filename)
    python scripts/pdf_to_akn.py data/irish_si_607.pdf --country ie
"""
import sys
import time
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractor.line_numbered_extractor import extract_with_line_info
from src.parser.level_extractor import extract_level_by_level, print_hierarchy
from src.parser.metadata_extractor import extract_document_metadata
from src.generator.akn_generator import generate_akn_from_hierarchy


def count_nodes(nodes):
    """Count total nodes in hierarchy."""
    total = len(nodes)
    for n in nodes:
        total += count_nodes(n.children)
    return total


def node_to_dict(node):
    """Convert HierarchyNode to JSON-serializable dict."""
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


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Akoma Ntoso XML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pdf_to_akn.py data/dpdp_act.pdf --title "DPDP Act 2023" --year 2023 --number 22
  python scripts/pdf_to_akn.py data/irish_si_607.pdf --country ie --doc-type regulation
        """
    )

    # Required
    parser.add_argument("pdf_path", help="Path to PDF file")

    # Metadata
    parser.add_argument("--title", "-t", help="Document title")
    parser.add_argument("--year", "-y", type=int, help="Year of enactment")
    parser.add_argument("--number", "-n", help="Act/SI number")
    parser.add_argument("--date", "-d", help="Date enacted (YYYY-MM-DD)")
    parser.add_argument("--country", "-c", default="in",
                        help="Country code (in=India, ie=Ireland, gb=UK)")
    parser.add_argument("--doc-type", default="act",
                        help="Document type (act, regulation, bill)")
    parser.add_argument("--language", default="eng",
                        help="Language code (eng=English)")

    # Processing options
    parser.add_argument("--max-depth", type=int, default=10,
                        help="Maximum hierarchy depth (default: 10)")
    parser.add_argument("--workers", type=int, default=3,
                        help="Number of parallel workers (default: 3, reduce if rate limited)")
    parser.add_argument("--sequential", action="store_true",
                        help="Disable parallel processing")
    parser.add_argument("--json-only", action="store_true",
                        help="Only extract JSON, skip XML generation")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Skip XML schema validation")
    parser.add_argument("--no-auto-detect", action="store_true",
                        help="Disable auto-detection of metadata")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Minimal output")

    # Output
    parser.add_argument("--output-dir", "-o", default="output",
                        help="Output directory (default: output)")

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    # Derive output paths
    pdf_name = pdf_path.stem
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    json_path = output_dir / f"{pdf_name}_hierarchy.json"
    xml_path = output_dir / f"{pdf_name}.xml"

    if not args.quiet:
        print("=" * 60)
        print("PDF to Akoma Ntoso Converter")
        print("=" * 60)
        print(f"Input: {pdf_path}")
        print()

    # Step 1: Extract text with line numbers
    if not args.quiet:
        print("Step 1: Extracting text from PDF...")

    line_infos, numbered_text = extract_with_line_info(str(pdf_path))

    if not args.quiet:
        print(f"  Lines: {len(line_infos)}")
        print(f"  Pages: {line_infos[0].page} to {line_infos[-1].page}")
        print()

    # Step 2: Auto-detect or use provided metadata
    needs_auto_detect = not args.no_auto_detect and not all([args.title, args.year, args.number])

    if needs_auto_detect:
        if not args.quiet:
            print("Step 2: Auto-detecting metadata...")

        # Get raw text for metadata extraction
        raw_text = "\n".join(li.text for li in line_infos[:200])  # First ~200 lines
        detected = extract_document_metadata(raw_text)

        # Use detected values, but allow command-line overrides
        title = args.title or detected.title
        year = args.year or detected.year
        number = args.number or detected.number
        date_enacted = args.date or detected.date_enacted or f"{year}-01-01"
        country = args.country if args.country != "in" else detected.country  # Override default
        doc_type = args.doc_type if args.doc_type != "act" else detected.doc_type  # Override default
        language = args.language or detected.language

        if not args.quiet:
            print(f"  Title:   {title}")
            print(f"  Country: {country}")
            print(f"  Type:    {doc_type}")
            print(f"  Year:    {year}")
            print(f"  Number:  {number}")
            print(f"  Date:    {date_enacted}")
            print()
    else:
        # Use provided arguments
        title = args.title or pdf_name.replace("_", " ").title()
        year = args.year or 2024
        number = args.number or "1"
        date_enacted = args.date or f"{year}-01-01"
        country = args.country
        doc_type = args.doc_type
        language = args.language

        if not args.quiet:
            print("Step 2: Using provided metadata...")
            print(f"  Title:   {title}")
            print(f"  Country: {country}")
            print(f"  Type:    {doc_type}")
            print(f"  Year:    {year}")
            print(f"  Number:  {number}")
            print()

    # Step 3: Extract hierarchy
    if not args.quiet:
        print("Step 3: Extracting document hierarchy...")
        mode = "sequential" if args.sequential else f"parallel ({args.workers} workers)"
        print(f"  Mode: {mode}")

    start_time = time.time()

    def on_level_complete(level, nodes):
        if not args.quiet:
            print(f"  Level {level}: {len(nodes)} nodes")

    nodes = extract_level_by_level(
        line_infos,
        max_depth=args.max_depth,
        parallel=not args.sequential,
        max_workers=args.workers,
        on_level_complete=on_level_complete
    )

    extraction_time = time.time() - start_time
    total_nodes = count_nodes(nodes)

    if not args.quiet:
        print(f"  Total nodes: {total_nodes}")
        print(f"  Time: {extraction_time:.1f}s")
        print()

    # Step 4: Save JSON
    if not args.quiet:
        print(f"Step 4: Saving JSON to {json_path}...")

    hierarchy_data = {
        "source_pdf": str(pdf_path),
        "total_lines": len(line_infos),
        "total_nodes": total_nodes,
        "extraction_time_seconds": round(extraction_time, 1),
        "hierarchy": [node_to_dict(n) for n in nodes]
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(hierarchy_data, f, indent=2, ensure_ascii=False)

    if not args.quiet:
        print(f"  Saved: {json_path}")
        print()

    if args.json_only:
        print(f"Done! JSON saved to {json_path}")
        return

    # Step 5: Generate AKN XML
    if not args.quiet:
        print(f"Step 5: Generating AKN XML...")

    metadata = {
        "title": title,
        "year": year,
        "act_number": number,
        "date_enacted": date_enacted,
        "country": args.country,
        "doc_type": args.doc_type,
        "language": args.language
    }

    xml_str = generate_akn_from_hierarchy(hierarchy_data, metadata)

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    if not args.quiet:
        print(f"  Saved: {xml_path}")
        print()

    # Step 6: Validate against schema
    if not args.skip_validation:
        if not args.quiet:
            print("Step 6: Validating against AKN 3.0 schema...")

        try:
            from lxml import etree
            import os

            schema_path = Path(__file__).parent.parent / "schemas" / "akomantoso30.xsd"
            if schema_path.exists():
                orig_dir = os.getcwd()
                os.chdir(schema_path.parent)
                schema = etree.XMLSchema(etree.parse("akomantoso30.xsd"))
                os.chdir(orig_dir)

                doc = etree.parse(str(xml_path))
                is_valid = schema.validate(doc)

                if is_valid:
                    if not args.quiet:
                        print("  Schema: VALID")
                else:
                    print("  Schema: INVALID")
                    for error in schema.error_log[:5]:
                        print(f"    Line {error.line}: {error.message[:60]}")
            else:
                if not args.quiet:
                    print("  Schema: Skipped (schema file not found)")
        except Exception as e:
            if not args.quiet:
                print(f"  Schema: Error - {e}")

    # Summary
    if not args.quiet:
        print()
        print("=" * 60)
        print("COMPLETE")
        print("=" * 60)
        print(f"JSON: {json_path}")
        print(f"XML:  {xml_path}")
        print(f"Nodes: {total_nodes}")
        print(f"Time: {extraction_time:.1f}s")
    else:
        print(f"Done: {xml_path}")


if __name__ == "__main__":
    main()
