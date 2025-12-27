"""Command-line interface for Akoma Ntoso converter."""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


@click.group()
def cli():
    """Indian Acts to Akoma Ntoso Converter."""
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--lines', '-n', default=100, help='Number of lines to show')
def extract(pdf_path: str, lines: int):
    """Extract raw text from a PDF file."""
    from src.extractor.pdf_extractor import extract_text

    console.print(f"[bold blue]Extracting text from:[/] {pdf_path}")

    text = extract_text(pdf_path)

    console.print(f"[green]Extracted {len(text)} characters[/]")
    console.print()

    # Show first N lines
    text_lines = text.split('\n')[:lines]
    preview = '\n'.join(text_lines)

    console.print(Panel(preview, title=f"Raw text (first {lines} lines)", border_style="blue"))


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--lines', '-n', default=100, help='Number of lines to show')
@click.option('--save', '-s', type=click.Path(), help='Save cleaned text to file')
@click.option('--pages', '-p', is_flag=True, help='Include page markers for PDF navigation')
def clean(pdf_path: str, lines: int, save: str, pages: bool):
    """Extract and clean text from a PDF file using LLM."""
    from src.extractor.pdf_extractor import extract_text
    from src.extractor.text_cleaner import clean_text

    console.print(f"[bold blue]Extracting text from:[/] {pdf_path}")
    raw_text = extract_text(pdf_path, include_page_markers=pages)
    if pages:
        console.print("[dim]Page markers enabled for PDF navigation[/]")
    console.print(f"[dim]Raw: {len(raw_text)} characters[/]")

    console.print("[bold blue]Cleaning text (using Claude)...[/]")
    with console.status("[bold green]Generating cleaning code..."):
        cleaned = clean_text(raw_text)
    console.print(f"[green]Cleaned: {len(cleaned)} characters[/]")
    console.print()

    # Show first N lines
    text_lines = cleaned.split('\n')[:lines]
    preview = '\n'.join(text_lines)

    console.print(Panel(preview, title=f"Cleaned text (first {lines} lines)", border_style="green"))

    if save:
        Path(save).write_text(cleaned, encoding='utf-8')
        console.print(f"\n[bold green]Saved to:[/] {save}")


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
def show_code(pdf_path: str):
    """Show the generated cleaning code for a PDF."""
    from src.extractor.pdf_extractor import extract_text
    from src.extractor.text_cleaner import generate_cleaning_code

    console.print(f"[bold blue]Analyzing:[/] {pdf_path}")

    with console.status("[bold green]Extracting text..."):
        raw_text = extract_text(pdf_path)
    sample = raw_text[:3000]

    console.print("[bold blue]Generating cleaning code...[/]")
    with console.status("[bold green]Calling Claude API..."):
        code = generate_cleaning_code(sample)

    console.print()
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Generated Cleaning Code", border_style="yellow"))


@cli.command()
def test_api():
    """Test the Claude API connection."""
    from src.parser.llm_client import hello_world

    console.print("[bold blue]Testing Claude API...[/]")
    try:
        with console.status("[bold green]Connecting..."):
            response = hello_world()
        console.print(f"[bold green]Success![/] Response: {response}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")


@cli.command()
@click.argument('text_path', type=click.Path(exists=True))
def analyze(text_path: str):
    """Analyze document structure from cleaned text file."""
    from src.parser.structure_analyzer import analyze_structure
    import json

    console.print(f"[bold blue]Analyzing structure:[/] {text_path}")

    text = Path(text_path).read_text(encoding='utf-8')
    console.print(f"[dim]Text length: {len(text)} characters[/]")

    with console.status("[bold green]Analyzing with Claude..."):
        result = analyze_structure(text)

    console.print("\n[bold green]Elements Found:[/]")
    for element, found in result["elements_found"].items():
        status = "[green]YES[/]" if found else "[dim]no[/]"
        count = result["counts"].get(element, 0)
        console.print(f"  {element}: {status} (count: {count})")

    # Also print as JSON
    console.print("\n[dim]Raw JSON:[/]")
    console.print(json.dumps(result, indent=2))


@cli.command()
@click.argument('text_path', type=click.Path(exists=True))
def chapters(text_path: str):
    """Extract chapters from cleaned text file."""
    from src.parser.chapter_extractor import extract_chapters

    console.print(f"[bold blue]Extracting chapters:[/] {text_path}")

    text = Path(text_path).read_text(encoding='utf-8')

    with console.status("[bold green]Extracting with Claude..."):
        chapter_list = extract_chapters(text)

    console.print(f"\n[bold green]Found {len(chapter_list)} chapters:[/]")
    for ch in chapter_list:
        console.print(f"  Chapter {ch.number}: {ch.title} (lines {ch.start_line}-{ch.end_line})")


@cli.command()
@click.argument('text_path', type=click.Path(exists=True))
def metadata(text_path: str):
    """Extract metadata from cleaned text file."""
    from src.parser.metadata_extractor import extract_metadata

    console.print(f"[bold blue]Extracting metadata:[/] {text_path}")

    text = Path(text_path).read_text(encoding='utf-8')

    with console.status("[bold green]Extracting metadata with Claude..."):
        meta = extract_metadata(text)

    console.print("\n[bold green]Metadata:[/]")
    console.print(f"  Title: {meta.title}")
    console.print(f"  Act Number: {meta.act_number}")
    console.print(f"  Year: {meta.year}")
    console.print(f"  Short Title: {meta.short_title}")
    console.print(f"  Date Enacted: {meta.date_enacted}")


@cli.command()
@click.argument('text_path', type=click.Path(exists=True))
def sections(text_path: str):
    """Extract sections from cleaned text file (uses hierarchy)."""
    from src.parser.structure_analyzer import analyze_structure, get_hierarchy
    from src.parser.chapter_extractor import extract_chapters, get_chapter_text
    from src.parser.section_extractor import extract_sections

    console.print(f"[bold blue]Extracting sections:[/] {text_path}")

    text = Path(text_path).read_text(encoding='utf-8')

    # Step 1: Analyze structure to get hierarchy
    with console.status("[bold green]Analyzing structure..."):
        structure = analyze_structure(text)
        hierarchy = get_hierarchy(structure)

    console.print(f"[dim]Hierarchy: {' > '.join(hierarchy)}[/]")

    # Step 2: Check if chapters exist in hierarchy
    if "chapters" in hierarchy:
        # Extract chapters first, then sections within each
        with console.status("[bold green]Extracting chapters..."):
            chapter_list = extract_chapters(text)

        console.print(f"\n[bold green]Found {len(chapter_list)} chapters:[/]")

        for ch in chapter_list:
            chapter_text = get_chapter_text(text, ch)
            with console.status(f"[bold green]Extracting sections from Chapter {ch.number}..."):
                section_list = extract_sections(chapter_text, chapter_num=ch.number)

            console.print(f"\n  [bold]Chapter {ch.number}: {ch.title}[/]")
            for sec in section_list:
                console.print(f"    Section {sec.number}: {sec.heading}")
    else:
        # No chapters - extract sections directly from full text
        with console.status("[bold green]Extracting sections..."):
            section_list = extract_sections(text)

        console.print(f"\n[bold green]Found {len(section_list)} sections:[/]")
        for sec in section_list:
            console.print(f"  Section {sec.number}: {sec.heading}")


@cli.command()
@click.argument('text_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output XML file path')
@click.option('--quick', '-q', is_flag=True, help='Skip subsection extraction for faster processing')
@click.option('--parallel', '-p', is_flag=True, help='Extract chapters in parallel (faster but may hit rate limits)')
@click.option('--workers', '-w', default=3, help='Number of parallel workers (default: 3)')
def generate(text_path: str, output: str, quick: bool, parallel: bool, workers: int):
    """Generate Akoma Ntoso XML from cleaned text file."""
    from src.parser.document_extractor import extract_document
    from src.generator.akn_generator import generate_akn

    console.print(f"[bold blue]Generating AKN XML:[/] {text_path}")
    if quick:
        console.print("[yellow]Quick mode: skipping subsection extraction[/]")
    if parallel:
        console.print(f"[yellow]Parallel mode: {workers} workers[/]")

    text = Path(text_path).read_text(encoding='utf-8')

    # Progress callback
    def on_progress(msg: str):
        console.print(f"[dim]{msg}[/]")

    # Extract document structure with progress
    doc = extract_document(
        text,
        extract_subsections_flag=not quick,
        on_progress=on_progress,
        parallel=parallel,
        max_workers=workers
    )

    console.print(f"\n[green]Extracted: {len(doc.chapters)} chapters, {sum(len(ch.sections) for ch in doc.chapters)} sections[/]")

    # Generate AKN XML
    with console.status("[bold green]Generating Akoma Ntoso XML..."):
        xml = generate_akn(doc)

    # Output
    if output:
        Path(output).write_text(xml, encoding='utf-8')
        console.print(f"\n[bold green]Saved to:[/] {output}")
    else:
        # Show preview
        lines = xml.split('\n')[:30]
        preview = '\n'.join(lines)
        console.print(Panel(preview + "\n...", title="AKN XML Preview (first 30 lines)", border_style="green"))

    console.print(f"\n[dim]Total XML size: {len(xml)} characters[/]")


@cli.command("full-extract")
@click.argument('text_path', type=click.Path(exists=True))
@click.option('--save', '-s', type=click.Path(), help='Save extracted JSON to file')
def full_extract(text_path: str, save: str):
    """Extract full document structure (metadata, chapters, sections, subsections)."""
    import json
    from src.parser.document_extractor import extract_document

    console.print(f"[bold blue]Extracting full document:[/] {text_path}")
    console.print("[dim]This may take several minutes...[/]")

    text = Path(text_path).read_text(encoding='utf-8')

    with console.status("[bold green]Extracting document structure..."):
        doc = extract_document(text)

    # Display summary
    console.print(f"\n[bold green]Document Extracted:[/]")
    console.print(f"  Title: {doc.metadata.title}")
    console.print(f"  Act Number: {doc.metadata.act_number} of {doc.metadata.year}")
    console.print(f"  Hierarchy: {' > '.join(doc.hierarchy)}")
    console.print(f"  Chapters: {len(doc.chapters)}")

    total_sections = sum(len(ch.sections) for ch in doc.chapters)
    console.print(f"  Total Sections: {total_sections}")

    # Show structure
    console.print("\n[bold]Structure:[/]")
    for ch in doc.chapters:
        console.print(f"  Chapter {ch.number}: {ch.title}")
        for sec in ch.sections:
            sub_count = len(sec.subsections)
            sub_info = f" ({sub_count} subsections)" if sub_count > 0 else ""
            console.print(f"    Section {sec.number}: {sec.heading}{sub_info}")

    # Save to JSON if requested
    if save:
        doc_dict = doc.model_dump()
        Path(save).write_text(json.dumps(doc_dict, indent=2, ensure_ascii=False), encoding='utf-8')
        console.print(f"\n[bold green]Saved to:[/] {save}")


@cli.command()
@click.argument('text_path', type=click.Path(exists=True))
@click.option('--pdf', '-p', type=click.Path(exists=True), help='Original PDF for side-by-side view')
@click.option('--output', '-o', type=click.Path(), default='output/preview.html', help='Output HTML file')
@click.option('--quick', '-q', is_flag=True, help='Quick extraction (sections only)')
@click.option('--open', 'open_browser', is_flag=True, help='Open in browser after generating')
def preview(text_path: str, pdf: str, output: str, quick: bool, open_browser: bool):
    """Generate HTML preview with side-by-side PDF comparison."""
    import webbrowser
    from src.parser.document_extractor import extract_document
    from src.generator.preview_generator import generate_preview

    console.print(f"[bold blue]Generating preview:[/] {text_path}")

    text = Path(text_path).read_text(encoding='utf-8')

    # Progress callback
    def on_progress(msg: str):
        console.print(f"[dim]{msg}[/]")

    # Extract document (pass PDF path for page number extraction)
    doc = extract_document(
        text,
        extract_subsections_flag=not quick,
        on_progress=on_progress,
        pdf_path=pdf
    )

    # Generate preview HTML
    console.print("[bold green]Generating HTML preview...[/]")

    # Copy PDF to output folder (same folder as HTML for relative path to work)
    pdf_filename = None
    if pdf:
        import shutil
        output_dir = Path(output).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_filename = Path(pdf).name
        pdf_dest = output_dir / pdf_filename
        shutil.copy2(pdf, pdf_dest)
        console.print(f"[dim]Copied PDF to {pdf_dest}[/]")

    html = generate_preview(doc, pdf_path=pdf_filename)

    # Save
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html, encoding='utf-8')
    console.print(f"\n[bold green]Saved to:[/] {output}")

    # Open in browser
    if open_browser:
        webbrowser.open(f'file://{Path(output).resolve()}')
        console.print("[dim]Opened in browser[/]")


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output XML file path')
def convert(pdf_path: str, output: str):
    """Convert PDF to Akoma Ntoso XML (placeholder)."""
    console.print(f"[bold blue]Converting:[/] {pdf_path}")
    console.print("[yellow]Note: Use 'generate' command for AKN XML generation[/]")
    console.print("[dim]Or use 'preview' command for side-by-side verification[/]")


if __name__ == '__main__':
    cli()
