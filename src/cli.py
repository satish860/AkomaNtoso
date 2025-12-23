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
def clean(pdf_path: str, lines: int, save: str):
    """Extract and clean text from a PDF file using LLM."""
    from src.extractor.pdf_extractor import extract_text
    from src.extractor.text_cleaner import clean_text

    console.print(f"[bold blue]Extracting text from:[/] {pdf_path}")
    raw_text = extract_text(pdf_path)
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
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output XML file path')
def convert(pdf_path: str, output: str):
    """Convert PDF to Akoma Ntoso XML (placeholder)."""
    console.print(f"[bold blue]Converting:[/] {pdf_path}")
    console.print("[yellow]Note: Full conversion not yet implemented (Sprint 3)[/]")
    console.print("[dim]Currently available: extract, clean, show-code, test-api[/]")


if __name__ == '__main__':
    cli()
