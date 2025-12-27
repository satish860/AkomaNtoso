"""Generate HTML preview for side-by-side PDF comparison with page navigation."""
import json
from pathlib import Path
from typing import Optional
from src.parser.document_extractor import Document


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - AKN Preview</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}

        .container {{ display: flex; height: 100vh; }}

        .pdf-panel {{
            width: 50%;
            height: 100%;
            border-right: 2px solid #333;
            background: #525659;
        }}
        .pdf-panel iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .pdf-panel .no-pdf {{
            color: #fff;
            padding: 20px;
            text-align: center;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .structure-panel {{
            width: 50%;
            height: 100%;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }}

        .header {{
            background: #1a1a2e;
            color: white;
            padding: 15px 20px;
            margin: -20px -20px 20px -20px;
        }}
        .header h1 {{ font-size: 18px; margin-bottom: 5px; }}
        .header .meta {{ font-size: 12px; color: #aaa; }}

        .chapter {{
            background: white;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .chapter-header {{
            background: #2d3436;
            color: white;
            padding: 12px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .chapter-header:hover {{ background: #3d4446; }}
        .chapter-header .toggle {{ font-size: 12px; }}
        .chapter-title {{ font-weight: 600; }}
        .chapter-content {{ display: none; padding: 0; }}
        .chapter.open .chapter-content {{ display: block; }}
        .chapter.open .toggle {{ transform: rotate(90deg); }}

        .page-badge {{
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 10px;
        }}
        .page-badge:hover {{
            background: #2980b9;
        }}

        .section {{
            border-bottom: 1px solid #eee;
            padding: 12px 15px;
        }}
        .section:last-child {{ border-bottom: none; }}
        .section-header {{
            display: flex;
            align-items: baseline;
            gap: 10px;
            cursor: pointer;
        }}
        .section-num {{
            font-weight: 600;
            color: #e74c3c;
            min-width: 30px;
        }}
        .section-heading {{ color: #333; flex: 1; }}

        .subsections {{
            margin-top: 10px;
            padding-left: 20px;
            display: none;
        }}
        .section.open .subsections {{ display: block; }}

        .subsection {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 8px;
            border-left: 3px solid #3498db;
        }}
        .subsection-num {{
            font-weight: 600;
            color: #3498db;
            margin-right: 8px;
        }}
        .subsection-content {{
            color: #555;
            font-size: 13px;
            margin-top: 5px;
        }}

        .clauses {{
            margin-top: 8px;
            padding-left: 15px;
        }}
        .clause {{
            background: #fff;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 5px;
            border-left: 2px solid #9b59b6;
        }}
        .clause-letter {{
            font-weight: 600;
            color: #9b59b6;
            margin-right: 8px;
        }}

        .subclauses {{
            margin-top: 5px;
            padding-left: 15px;
        }}
        .subclause {{
            font-size: 12px;
            color: #666;
            padding: 4px 0;
        }}
        .subclause-numeral {{
            font-weight: 600;
            color: #e67e22;
            margin-right: 5px;
        }}

        .stats {{
            display: flex;
            gap: 15px;
            margin-top: 10px;
        }}
        .stat {{
            background: rgba(255,255,255,0.1);
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
        }}

        .expand-all {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 15px;
        }}
        .expand-all:hover {{ background: #2980b9; }}

        .clickable {{
            cursor: pointer;
        }}
        .clickable:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="pdf-panel">
            {pdf_viewer}
        </div>
        <div class="structure-panel">
            <div class="header">
                <h1>{title}</h1>
                <div class="meta">Act No. {act_number} of {year}</div>
                <div class="stats">
                    <span class="stat">{chapter_count} Chapters</span>
                    <span class="stat">{section_count} Sections</span>
                    <span class="stat">{subsection_count} Subsections</span>
                </div>
            </div>

            <button class="expand-all" onclick="toggleAll()">Expand/Collapse All</button>

            {chapters_html}
        </div>
    </div>

    <script>
        // PDF navigation using iframe
        const pdfBasePath = '{pdf_path_js}';

        function goToPage(num) {{
            const iframe = document.getElementById('pdf-frame');
            if (iframe && pdfBasePath) {{
                iframe.src = pdfBasePath + '#page=' + num;
            }}
        }}

        // Toggle chapter
        document.querySelectorAll('.chapter-header').forEach(header => {{
            header.addEventListener('click', (e) => {{
                // Don't toggle if clicking on page badge
                if (e.target.classList.contains('page-badge')) return;
                header.parentElement.classList.toggle('open');
            }});
        }});

        // Toggle section
        document.querySelectorAll('.section-header').forEach(header => {{
            header.addEventListener('click', (e) => {{
                // Don't toggle if clicking on page badge
                if (e.target.classList.contains('page-badge')) return;
                e.stopPropagation();
                header.parentElement.classList.toggle('open');
            }});
        }});

        // Page navigation from badges
        document.querySelectorAll('.page-badge').forEach(badge => {{
            badge.addEventListener('click', (e) => {{
                e.stopPropagation();
                const page = parseInt(badge.dataset.page);
                if (page) goToPage(page);
            }});
        }});

        // Expand/collapse all
        let allExpanded = false;
        function toggleAll() {{
            allExpanded = !allExpanded;
            document.querySelectorAll('.chapter, .section').forEach(el => {{
                if (allExpanded) {{
                    el.classList.add('open');
                }} else {{
                    el.classList.remove('open');
                }}
            }});
        }}
    </script>
</body>
</html>
'''


def _generate_subclause_html(subclause) -> str:
    """Generate HTML for a subclause."""
    return f'''
        <div class="subclause">
            <span class="subclause-numeral">({subclause.numeral})</span>
            {subclause.content[:100]}{'...' if len(subclause.content) > 100 else ''}
        </div>
    '''


def _generate_clause_html(clause) -> str:
    """Generate HTML for a clause."""
    subclauses_html = ''.join(_generate_subclause_html(sc) for sc in clause.subclauses)
    subclauses_section = f'<div class="subclauses">{subclauses_html}</div>' if clause.subclauses else ''

    return f'''
        <div class="clause">
            <span class="clause-letter">({clause.letter})</span>
            {clause.content[:150]}{'...' if len(clause.content) > 150 else ''}
            {subclauses_section}
        </div>
    '''


def _generate_subsection_html(subsection) -> str:
    """Generate HTML for a subsection."""
    clauses_html = ''.join(_generate_clause_html(c) for c in subsection.clauses)
    clauses_section = f'<div class="clauses">{clauses_html}</div>' if subsection.clauses else ''

    content = subsection.content[:200] + '...' if len(subsection.content) > 200 else subsection.content

    return f'''
        <div class="subsection">
            <span class="subsection-num">({subsection.number})</span>
            <span class="subsection-content">{content}</span>
            {clauses_section}
        </div>
    '''


def _generate_section_html(section) -> str:
    """Generate HTML for a section."""
    subsections_html = ''.join(_generate_subsection_html(s) for s in section.subsections)
    has_subsections = len(section.subsections) > 0

    # Page badge if page number available
    page_badge = ''
    if section.page:
        page_badge = f'<span class="page-badge" data-page="{section.page}">p.{section.page}</span>'

    return f'''
        <div class="section">
            <div class="section-header">
                <span class="section-num">{section.number}.</span>
                <span class="section-heading">{section.heading or 'Untitled'}</span>
                {page_badge}
                {f'<span style="color:#999;font-size:12px">({len(section.subsections)} subsections)</span>' if has_subsections else ''}
            </div>
            <div class="subsections">
                {subsections_html}
            </div>
        </div>
    '''


def _generate_chapter_html(chapter) -> str:
    """Generate HTML for a chapter."""
    sections_html = ''.join(_generate_section_html(s) for s in chapter.sections)

    # Page badge if page number available
    page_badge = ''
    if chapter.page:
        page_badge = f'<span class="page-badge" data-page="{chapter.page}">p.{chapter.page}</span>'

    return f'''
        <div class="chapter">
            <div class="chapter-header">
                <span class="chapter-title">Chapter {chapter.number}: {chapter.title}</span>
                {page_badge}
                <span class="toggle">&#9654;</span>
            </div>
            <div class="chapter-content">
                {sections_html}
            </div>
        </div>
    '''


def generate_preview(doc: Document, pdf_path: Optional[str] = None) -> str:
    """
    Generate HTML preview with side-by-side PDF comparison.

    Args:
        doc: Extracted Document object
        pdf_path: Optional path to PDF file for embedding

    Returns:
        HTML string
    """
    # Generate chapters HTML
    chapters_html = ''.join(_generate_chapter_html(ch) for ch in doc.chapters)

    # PDF viewer HTML - use iframe with page parameter for navigation
    if pdf_path:
        pdf_viewer = f'''
            <iframe id="pdf-frame" src="{pdf_path}#page=1"></iframe>
        '''
        pdf_path_js = pdf_path.replace('\\', '/')
    else:
        pdf_viewer = '<div class="no-pdf"><p>No PDF provided</p><p>Use --pdf flag to embed original PDF</p></div>'
        pdf_path_js = ''

    # Count stats
    section_count = sum(len(ch.sections) for ch in doc.chapters)
    subsection_count = sum(
        len(sec.subsections)
        for ch in doc.chapters
        for sec in ch.sections
    )

    # Generate HTML
    html = HTML_TEMPLATE.format(
        title=doc.metadata.short_title or doc.metadata.title,
        act_number=doc.metadata.act_number,
        year=doc.metadata.year,
        chapter_count=len(doc.chapters),
        section_count=section_count,
        subsection_count=subsection_count,
        pdf_viewer=pdf_viewer,
        pdf_path_js=pdf_path_js,
        chapters_html=chapters_html
    )

    return html
