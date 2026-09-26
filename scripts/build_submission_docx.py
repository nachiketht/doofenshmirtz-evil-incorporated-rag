#!/usr/bin/env python3
"""Build the DEI RAG submission packet (DOCX with screenshot path placeholders)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "DEI_RAG_Submission.docx"

# Letter page, 1" margins → 6.5" content width. Word tblW/tcW use twips (1440/inch), not EMUs.
CONTENT_WIDTH_IN = 6.5
DXA_PER_INCH = 1440

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
ACCENT = RGBColor(0x2F, 0x5D, 0x8A)
BODY = RGBColor(0x2C, 0x33, 0x3A)
MUTED = RGBColor(0x5C, 0x65, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CODE = RGBColor(0x1F, 0x29, 0x37)
PLACEHOLDER_FILL = "EEF3F8"
CODE_FILL = "F5F6F8"
HEADER_FILL = "1B2A4A"
NOTE_FILL = "F7F4EA"
ROW_ALT = "F7F8FA"


def set_run_font(run, name="Calibri", size=11, color=BODY, bold=False, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.bold = bold
    run.italic = italic


def shade_cell(cell, hex_color: str) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    for child in list(tc_pr):
        if child.tag == qn("w:shd"):
            tc_pr.remove(child)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tc_pr.append(shd)


def set_cell_borders(cell, color="C5CDD8", sz="8") -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    for child in list(tc_pr):
        if child.tag == qn("w:tcBorders"):
            tc_pr.remove(child)
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), sz)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tc_pr.append(borders)


def set_cell_margins(cell, top=40, bottom=40, left=60, right=60) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for edge, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        tc_mar.append(node)
    tc_pr.append(tc_mar)


def to_dxa(inches: float) -> int:
    return int(round(inches * DXA_PER_INCH))


def set_table_widths(table, widths_inches: list[float]) -> None:
    """Column widths in twips (1440/inch). Never pass python-docx EMUs into w:w."""
    total_in = sum(widths_inches) or CONTENT_WIDTH_IN
    if total_in > CONTENT_WIDTH_IN:
        scale = CONTENT_WIDTH_IN / total_in
        widths_inches = [w * scale for w in widths_inches]
        total_in = CONTENT_WIDTH_IN
    dxas = [to_dxa(w) for w in widths_inches]
    table.autofit = False
    table.allow_autofit = False
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(dxas)))
    tbl_w.set(qn("w:type"), "dxa")
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for child in list(grid):
            grid.remove(child)
    else:
        grid = OxmlElement("w:tblGrid")
        tbl_pr.addnext(grid)
    for dxa in dxas:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(dxa))
        grid.append(col)
    for row in table.rows:
        for cell, width, dxa in zip(row.cells, widths_inches, dxas, strict=False):
            cell.width = Inches(width)
            tc = cell._tc
            tc_pr = tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(dxa))
            tc_w.set(qn("w:type"), "dxa")


def paragraph_space(paragraph, before=0, after=8, line=1.15) -> None:
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = line


def add_text(paragraph, text, **kwargs) -> None:
    run = paragraph.add_run(text)
    set_run_font(run, **kwargs)


def heading(doc, text, level=1) -> None:
    paragraph = doc.add_paragraph()
    paragraph.style = doc.styles[f"Heading {level}"]
    paragraph.clear()
    if level == 1:
        paragraph.paragraph_format.space_before = Pt(16)
        paragraph.paragraph_format.space_after = Pt(6)
        add_text(paragraph, text, name="Calibri", size=16, color=NAVY, bold=True)
    elif level == 2:
        paragraph.paragraph_format.space_before = Pt(12)
        paragraph.paragraph_format.space_after = Pt(4)
        add_text(paragraph, text, name="Calibri", size=13, color=ACCENT, bold=True)
    else:
        paragraph.paragraph_format.space_before = Pt(10)
        paragraph.paragraph_format.space_after = Pt(4)
        add_text(paragraph, text, name="Calibri", size=12, color=NAVY, bold=True)


def body(doc, text, *, after=8) -> None:
    paragraph = doc.add_paragraph()
    paragraph_space(paragraph, before=0, after=after, line=1.15)
    add_text(paragraph, text, size=11, color=BODY)


def italic_note(doc, text) -> None:
    paragraph = doc.add_paragraph()
    paragraph_space(paragraph, before=0, after=8, line=1.15)
    add_text(paragraph, text, size=10, color=MUTED, italic=True)


def bullets(doc, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.clear()
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.left_indent = Inches(0.25)
        add_text(paragraph, item, size=11, color=BODY)


def kv_line(doc, label: str, value: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph_space(paragraph, before=0, after=2, line=1.1)
    add_text(paragraph, f"{label}:  ", size=11, color=NAVY, bold=True)
    add_text(paragraph, value, size=11, color=BODY)


def shade_paragraph(paragraph, fill: str) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    for child in list(p_pr):
        if child.tag == qn("w:shd"):
            p_pr.remove(child)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_code_block(doc, code: str, *, caption: str | None = None) -> None:
    if caption:
        paragraph = doc.add_paragraph()
        paragraph_space(paragraph, before=4, after=2, line=1.0)
        add_text(paragraph, caption, name="Calibri", size=9, color=MUTED, italic=True)

    lines = code.replace("\t", "    ").splitlines() or [""]
    for index, line in enumerate(lines):
        paragraph = doc.add_paragraph()
        paragraph_space(paragraph, before=0, after=0, line=1.08)
        paragraph.paragraph_format.left_indent = Inches(0.1)
        shade_paragraph(paragraph, CODE_FILL)
        add_text(paragraph, line if line else " ", name="Consolas", size=9, color=CODE)

    spacer = doc.add_paragraph()
    paragraph_space(spacer, before=0, after=8, line=1.0)


def add_placeholder(doc, path: str, capture: str, *, extra: str | None = None) -> None:
    label = doc.add_paragraph()
    paragraph_space(label, before=6, after=0, line=1.08)
    shade_paragraph(label, PLACEHOLDER_FILL)
    add_text(label, "Screenshot  ", size=11, color=NAVY, bold=True)
    add_text(label, path, name="Consolas", size=10, color=ACCENT)

    hint = doc.add_paragraph()
    paragraph_space(hint, before=0, after=0, line=1.08)
    shade_paragraph(hint, PLACEHOLDER_FILL)
    add_text(hint, capture, size=10, color=BODY)
    if extra:
        extra_p = doc.add_paragraph()
        paragraph_space(extra_p, before=0, after=0, line=1.08)
        shade_paragraph(extra_p, PLACEHOLDER_FILL)
        add_text(extra_p, extra, size=9, color=MUTED, italic=True)

    spacer = doc.add_paragraph()
    paragraph_space(spacer, before=0, after=8, line=1.0)


def add_callout(doc, title: str, body_text: str) -> None:
    title_p = doc.add_paragraph()
    paragraph_space(title_p, before=4, after=0, line=1.08)
    shade_paragraph(title_p, NOTE_FILL)
    add_text(title_p, title, size=11, color=NAVY, bold=True)

    body_p = doc.add_paragraph()
    paragraph_space(body_p, before=0, after=8, line=1.12)
    shade_paragraph(body_p, NOTE_FILL)
    add_text(body_p, body_text, size=11, color=BODY)


def add_table(doc, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_widths(table, widths)

    for index, header in enumerate(headers):
        cell = table.cell(0, index)
        shade_cell(cell, HEADER_FILL)
        set_cell_borders(cell, color="1B2A4A", sz="4")
        set_cell_margins(cell, top=40, bottom=40, left=70, right=70)
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        add_text(paragraph, header, size=9, color=WHITE, bold=True)

    for row_index, values in enumerate(rows):
        for col_index, value in enumerate(values):
            cell = table.cell(row_index + 1, col_index)
            shade_cell(cell, "FFFFFF" if row_index % 2 == 0 else ROW_ALT)
            set_cell_borders(cell, color="D8DEE6", sz="4")
            set_cell_margins(cell, top=40, bottom=40, left=70, right=70)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            add_text(paragraph, value, size=9, color=BODY)

    spacer = doc.add_paragraph()
    paragraph_space(spacer, before=2, after=10, line=1.0)


def read_excerpt(rel: str, start: int, end: int) -> str:
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1 : end])


def configure_styles(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = BODY
    normal.paragraph_format.line_spacing = 1.08

    for style_name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 12)):
        style = doc.styles[style_name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = NAVY
        style.font.bold = True

    footer = section.footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(
        paragraph,
        "Doofenshmirtz Evil Incorporated  ·  Policy RAG Submission Packet  ·  ",
        size=8,
        color=MUTED,
    )
    run = paragraph.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    run._r.append(fld1)
    run2 = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    run2._r.append(instr)
    set_run_font(run2, size=8, color=MUTED)
    run3 = paragraph.add_run()
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run3._r.append(fld2)

    core = doc.core_properties
    core.title = "Doofenshmirtz Evil Incorporated RAG — Submission Packet"
    core.subject = "Policy RAG: ingest, hybrid retrieve, rerank, generate, evaluate"
    core.author = "DEI RAG"
    core.category = "Course submission"


def add_cover(doc: Document) -> None:
    kicker = doc.add_paragraph()
    paragraph_space(kicker, before=0, after=2, line=1.0)
    add_text(kicker, "DOOFENSHMIRTZ EVIL INCORPORATED", size=11, color=ACCENT, bold=True)

    title = doc.add_paragraph()
    paragraph_space(title, before=0, after=4, line=1.0)
    add_text(title, "Policy RAG Submission Packet", size=20, color=NAVY, bold=True)

    subtitle = doc.add_paragraph()
    paragraph_space(subtitle, before=0, after=10, line=1.08)
    add_text(
        subtitle,
        "Heading-aware ingest · Dense + BM25 hybrid · Cohere rerank · Grounded JSON answers · Gold-set eval",
        size=11,
        color=MUTED,
    )

    body(
        doc,
        "This packet follows the required deliverable order. Each section includes the written evidence "
        "from the repository, plus a screenshot path. Insert the picture under that path line before "
        "exporting the final PDF.",
    )

    add_callout(
        doc,
        "Screenshot folder",
        "Create a folder named screenshots/ next to this document (repo root). File names are listed in "
        "the index below. Section 2 — the minimal embed-store-retrieve loop on two known texts — is "
        "intentionally left without a placeholder so you can insert that capture later.",
    )

    heading(doc, "Deliverable map", 2)
    add_table(
        doc,
        ["#", "Required item", "In this draft"],
        [
            ["1", "Generated source documents, planted data-quality issue identified", "Written + screenshot path"],
            ["2", "Minimal embed-store-retrieve loop (Suggested Approach steps 2–3)", "Deferred — no placeholder"],
            ["3", "Chunking, embedding, and vector store code (full pipeline)", "Code + screenshot path"],
            ["4", "Basic RAG pipeline end to end on a sample question", "Run transcript + screenshot path"],
            ["5", "Hybrid retrieval code, and a query beating vector-only search", "Code, table + screenshot path"],
            ["6", "Reranking code", "Code + screenshot path"],
            ["7", "Evaluation test set and harness code", "Gold set, harness + screenshot path"],
            ["8", "Evaluation harness terminal output with recall / accuracy", "Scores + screenshot path"],
            ["9", "Planted-issue question, flawed answer, written diagnosis", "Full write-up + screenshot path"],
            ["10", "Source attribution: answer with cited source(s)", "Example + screenshot path"],
            ["11", "Passing pipeline run confirming the full submission", "Eval 11/11 + screenshot path"],
        ],
        [0.5, 4.4, 2.2],
    )

    heading(doc, "Screenshot index", 2)
    body(doc, "Use these exact relative paths when you attach captures later.")
    add_table(
        doc,
        ["Path", "Section"],
        [
            ["screenshots/01a-preparedness-v1-v2-nuclear.png", "1. Source docs — nuclear wait conflict"],
            ["screenshots/01b-time-usage-v1-v2-tokens.png", "1. Source docs — token allocation conflict"],
            ["screenshots/03-ingest-chunk-embed-store.png", "3. Chunk / embed / Chroma pipeline code"],
            ["screenshots/04-rag-end-to-end-sample.png", "4. End-to-end RAG on a sample question"],
            ["screenshots/05a-hybrid-retrieval-code.png", "5. Hybrid retrieval code"],
            ["screenshots/05b-hybrid-beats-dense.png", "5. Query where hybrid outperforms dense"],
            ["screenshots/06-rerank-code.png", "6. Cohere rerank code"],
            ["screenshots/07a-gold-set.png", "7. Evaluation test set"],
            ["screenshots/07b-eval-harness-code.png", "7. Evaluation harness code"],
            ["screenshots/08-eval-harness-terminal.png", "8. Harness run with recall / accuracy"],
            ["screenshots/09-planted-issue-flawed-answer.png", "9. Question + flawed unfiltered answer"],
            ["screenshots/10-source-attribution.png", "10. Answer with cited sources"],
            ["screenshots/11-passing-pipeline.png", "11. Passing pytest / eval confirmation"],
        ],
        [4.4, 2.7],
    )


def add_overview(doc: Document) -> None:
    heading(doc, "System snapshot")
    body(
        doc,
        "Policy question answering over the DEI employee handbooks in docs/. Files are parsed by numbered "
        "heading, split into leaf chunks, version-diffed (added / unchanged / stale), embedded with "
        "EmbeddingGemma, and stored in a persistent Chroma collection. At query time a router sends the "
        "question to the current lane (in-force leaves only) or the history lane (including superseded "
        "versions). Retrieval is the union of dense top-10 and BM25 top-10, Cohere rerank-v3.5 keeps five "
        "chunks, and gemma3:12b answers as validated JSON.",
    )
    add_code_block(
        doc,
        "question\n"
        "  -> router (qwen3:4b, regex fallback)\n"
        "  -> dense top 10  +  BM25 top 10  (dedupe by chunk id, no fused rank)\n"
        "  -> Cohere rerank-v3.5 top 5\n"
        "  -> gemma3:12b answer\n"
        "  -> JSON: answer, retrieved_chunks, router",
        caption="Pipeline (from README.md)",
    )
    add_table(
        doc,
        ["Stage", "Implementation", "Path"],
        [
            ["Load", "PDF / DOCX → numbered section trees", "src/ingestion/load.py"],
            ["Chunk", "Heading leaves; split only if > 500 words", "src/ingestion/chunk.py"],
            ["Version diff", "Mark added / unchanged / stale across v1→v2", "src/ingestion/diff.py"],
            ["Embed + store", "EmbeddingGemma → Chroma HNSW cosine", "src/ingestion/index.py"],
            ["Route", "current vs history (LLM, regex fallback)", "src/retrieval/route.py"],
            ["Dense", "Query vector, metadata filter, top 10", "src/retrieval/dense.py"],
            ["Sparse", "Okapi BM25 k1=1.5, b=0.75, top 10", "src/retrieval/sparse.py"],
            ["Hybrid", "Union by chunk id; Cohere ranks the pool", "src/retrieval/hybrid.py"],
            ["Rerank", "Cohere rerank-v3.5, top 5", "src/retrieval/rerank.py"],
            ["Generate", "Grounded answer + citations + JSON schema", "src/generation/"],
            ["Eval", "11 gold questions, recall + answer keys", "evaluation_harness/"],
        ],
        [1.4, 3.5, 2.2],
    )


def add_section_source_docs(doc: Document) -> None:
    heading(doc, "1. Generated source documents")
    body(
        doc,
        "The corpus lives in docs/. Four policy families were written for this project. HR, Time & Usage, "
        "and Preparedness each have a v1 PDF and a v2 DOCX. Health & Wellness is a single v1 document. "
        "v1 and v2 are ingested together on purpose so version conflicts can be observed.",
    )
    add_table(
        doc,
        ["File", "Role in the corpus"],
        [
            ["docs/HR Policy v1.0.pdf", "Original HR rules"],
            ["docs/HR Policy v2.0.docx", "In-force HR (pet leave, email joke, fridge)"],
            ["docs/Health and Wellness Policy v1.0.pdf", "Gym, protein, caffeine (no v2)"],
            ["docs/Time and Usage Policy v1.0.pdf", "Planted issue: 1,000,000 tokens / cycle"],
            ["docs/Time and Usage Policy v2.0.docx", "In-force: 500,000 tokens; winner-takes-tokens"],
            ["docs/Preparedness Policy v1.0.pdf", "Planted issue: desk shelter; two-hour all-clear"],
            ["docs/Preparedness Policy v2.0.docx", "In-force: break-room fridge; two-week shelter"],
        ],
        [3.6, 3.5],
    )

    heading(doc, "Planted data-quality issue", 2)
    body(
        doc,
        "The planted defect is outdated duplicates: v1 PDFs sit next to v2 DOCX files for the same "
        "policy and disagree on material rules. Naive RAG retrieves both, so the model hedges. That is a "
        "source-data problem, not a retrieval or generation bug.",
    )

    heading(doc, "Primary conflict — nuclear protocol", 3)
    add_table(
        doc,
        ["Rule", "Preparedness Policy v1.0.pdf", "Preparedness Policy v2.0.docx"],
        [
            [
                "Shelter",
                "Under the desk (§4.1 Shelter Position). Called the only sanctioned position.",
                "Break-room industrial refrigerator (§4.1 Shelter Location).",
            ],
            [
                "All-clear",
                "Employees may go outside after two hours (§4.2 All-Clear Timing).",
                "Remain indoors for two weeks (§4.3 Duration of Sheltering).",
            ],
        ],
        [1.3, 2.9, 2.9],
    )
    add_placeholder(
        doc,
        "screenshots/01a-preparedness-v1-v2-nuclear.png",
        "Open both Preparedness files. Capture v1 §4.1–4.2 (desk / two hours) beside v2 §4.1 and §4.3 "
        "(refrigerator / two weeks). Circle or highlight the conflicting numbers.",
        extra="Mark the screenshot: PLANTED ISSUE — conflicting all-clear times.",
    )

    heading(doc, "Secondary conflict — token allocation", 3)
    add_table(
        doc,
        ["Rule", "Time and Usage Policy v1.0.pdf", "Time and Usage Policy v2.0.docx"],
        [
            [
                "Allocation",
                "1,000,000 tokens each six-hour cycle (§5.1).",
                "500,000 tokens (§6.1 Allocation Amount).",
            ],
            [
                "Transfers",
                "Gifting and pooling prohibited (§8.1).",
                "Winner-takes-tokens foosball transfer (§4.2).",
            ],
        ],
        [1.3, 2.9, 2.9],
    )
    add_placeholder(
        doc,
        "screenshots/01b-time-usage-v1-v2-tokens.png",
        "Open both Time & Usage files. Capture v1 §5.1 (1,000,000) beside v2 §6.1 (500,000). Highlight "
        "the two amounts.",
        extra="Optional: also show v1 §8.1 vs v2 §4.2 (transfer rules).",
    )
    add_callout(
        doc,
        "Why both files are still in docs/",
        "Both versions are real source documents and both are ingested. After ingest, v1 nuclear and "
        "token leaves are marked stale and v2 added. The router is a retrieve-time filter on that "
        "metadata. It does not rewrite the PDFs. Section 9 shows what happens when that filter is off.",
    )


def add_section_deferred_loop(doc: Document) -> None:
    heading(doc, "2. Minimal embed-store-retrieve loop")
    italic_note(
        doc,
        "Deferred. No screenshot placeholder in this draft. Insert the terminal capture for Suggested "
        "Approach steps 2–3 here later, between Sections 1 and 3.",
    )
    body(
        doc,
        "When you add it, use two known pieces of text, embed them, store them, and retrieve one with a "
        "matching query so the loop is visibly working before the full policy corpus.",
    )


def add_section_pipeline_code(doc: Document) -> None:
    heading(doc, "3. Chunking, embedding, and vector store")
    body(
        doc,
        "Ingest is python -m ingestion.ingest. It loads every PDF and DOCX under docs/, parses numbered "
        "sections, diffs versions, embeds leaf text with EmbeddingGemma, and upserts into Chroma "
        "(collection dei_policies, cosine HNSW). Unchanged section bodies reuse stored vectors.",
    )
    add_code_block(
        doc,
        "python -m ingestion.ingest\npython -m ingestion.show_chunks",
        caption="Commands",
    )

    heading(doc, "Orchestrator", 2)
    add_code_block(
        doc,
        read_excerpt("src/ingestion/ingest.py", 16, 27),
        caption="src/ingestion/ingest.py — main()",
    )

    heading(doc, "Chunking", 2)
    body(
        doc,
        "A numbered section with no subsections becomes one leaf. Subsections become child leaves with "
        "parent_id set. Bodies over 500 words are sentence-split (650 tokens, 130 overlap). Node ids "
        "are stable slugs: policy:v{version}:{section}:{subsection}.",
    )
    add_code_block(
        doc,
        read_excerpt("src/ingestion/chunk.py", 23, 79),
        caption="src/ingestion/chunk.py — section_nodes()",
    )

    heading(doc, "Version diff", 2)
    body(
        doc,
        "Versions are replayed in order. The first copy is stored with an empty change_status. A later "
        "file marks identical text unchanged, rewritten or new text added, and the previous live copy "
        "stale. That metadata is what the current-lane filter uses.",
    )
    add_code_block(
        doc,
        read_excerpt("src/ingestion/diff.py", 21, 77),
        caption="src/ingestion/diff.py — resolve_nodes()",
    )

    heading(doc, "Embedding and Chroma upsert", 2)
    add_code_block(
        doc,
        read_excerpt("src/ingestion/index.py", 25, 43),
        caption="src/ingestion/index.py — PolicyIndex.sync()",
    )
    add_code_block(
        doc,
        read_excerpt("src/adapter/embedding_adapter.py", 14, 63),
        caption="src/adapter/embedding_adapter.py — Ollama EmbeddingGemma",
    )
    add_code_block(
        doc,
        read_excerpt("src/adapter/db_adapter.py", 13, 84),
        caption="src/adapter/db_adapter.py — persistent Chroma collection",
    )
    add_placeholder(
        doc,
        "screenshots/03-ingest-chunk-embed-store.png",
        "IDE screenshot of the ingest pipeline. Suggested: ingest.py, chunk.py, and index.py visible "
        "(split editor or a single scrolled capture of the three files).",
        extra="Also acceptable: terminal output of python -m ingestion.ingest plus the open source files.",
    )


def add_section_rag_e2e(doc: Document) -> None:
    heading(doc, "4. Basic RAG pipeline, end to end")
    body(
        doc,
        "Interactive JSON is python -m generation. A single-shot run with citations is "
        "python -m utility.show_answer. Both path through route → hybrid retrieve → Cohere rerank → "
        "grounded generate.",
    )
    add_code_block(
        doc,
        'python -m generation\n'
        'python -m utility.show_answer "How many gym sessions per week am I expected to complete, and how long is each session?"',
        caption="Commands",
    )

    heading(doc, "Sample question", 2)
    kv_line(doc, "Query", "How many gym sessions per week am I expected to complete, and how long is each session?")
    kv_line(doc, "Gold chunk", "health-and-wellness-policy:v1.0:gym-routine-requirements:minimum-requirement")
    kv_line(doc, "Router", "current (llm)")

    heading(doc, "Answer (live eval run)", 2)
    add_callout(
        doc,
        "Generated answer",
        "You are expected to complete a minimum of three structured training sessions per week, with "
        "each session lasting at least 45 minutes. These sessions should include a mix of resistance "
        "training and cardiovascular conditioning. A suggested schedule is two days for resistance "
        "training, one day for cardio or conditioning, and at least one full rest day.",
    )

    heading(doc, "Validated JSON payload", 2)
    body(
        doc,
        "The CLI validates GenerationResponse and rejects extra keys. Policy names stay in "
        "retrieved_chunks, not in the answer body. At most five chunks.",
    )
    add_code_block(
        doc,
        """{
  "answer": "You are expected to complete a minimum of three structured training sessions per week, with each session lasting at least 45 minutes. ...",
  "retrieved_chunks": [
    {
      "policy_id": "health-and-wellness-policy",
      "version": "1.0",
      "section": "3. Gym Routine Requirements > 3.1 Minimum Requirement",
      "rerank_Score": 0.8256
    },
    {
      "policy_id": "health-and-wellness-policy",
      "version": "1.0",
      "section": "3. Gym Routine Requirements > 3.2 Suggested Weekly Split",
      "rerank_Score": 0.3352
    }
  ],
  "router": "current (llm)"
}""",
        caption="Shape produced by python -m generation (trimmed to two chunks)",
    )
    add_code_block(
        doc,
        read_excerpt("src/generation/respond.py", 14, 40),
        caption="src/generation/respond.py — generate_response()",
    )
    add_placeholder(
        doc,
        "screenshots/04-rag-end-to-end-sample.png",
        "Terminal showing python -m generation or python -m utility.show_answer for the gym-minimum "
        "question: the answer, retrieved_chunks, and router lane.",
        extra="Use a real run, not this reconstructed JSON.",
    )


def add_section_hybrid(doc: Document) -> None:
    heading(doc, "5. Hybrid retrieval vs vector-only")
    body(
        doc,
        "Hybrid is the union of dense top 10 and BM25 top 10, de-duplicated by chunk id. Dense hits "
        "are listed first, then BM25-only leftovers. There is no weighted fusion and no RRF — Cohere "
        "ranks the pool. Vector-only is the same dense list with BM25 turned off.",
    )
    add_code_block(
        doc,
        read_excerpt("src/retrieval/hybrid.py", 30, 78),
        caption="src/retrieval/hybrid.py — hybrid_search() and fuse_hits()",
    )
    add_placeholder(
        doc,
        "screenshots/05a-hybrid-retrieval-code.png",
        "IDE screenshot of src/retrieval/hybrid.py (and optionally sparse.py). Show fuse_hits and the "
        "union-by-id behavior.",
    )

    heading(doc, "Query where hybrid wins", 2)
    body(
        doc,
        "On most gold questions EmbeddingGemma already places the right leaf in the dense top 10, so "
        "hybrid cannot “win” there. The counterexample is a rare lexical phrase that embeddings treat "
        "as office clutter and BM25 treats as an exact match.",
    )
    kv_line(
        doc,
        "Query",
        "What does the health policy say about alphabetizing the supply closet unprompted?",
    )
    kv_line(
        doc,
        "Gold leaf",
        "health-and-wellness-policy:v1.0:caffeine-guidelines:monitoring-and-tapering",
    )
    kv_line(
        doc,
        "Why",
        "Health §5.2 lists alphabetizing the supply closet unprompted as a caffeine overconsumption symptom.",
    )
    add_code_block(
        doc,
        "python -m utility.show_compare --no-rerank "
        '"What does the health policy say about alphabetizing the supply closet unprompted?"\n'
        "python -m utility.show_compare "
        '"What does the health policy say about alphabetizing the supply closet unprompted?"\n'
        "python -m pytest tests/test_hybrid_outperform.py -v",
        caption="Replay commands",
    )

    heading(doc, "Vector-only (dense top 10)", 3)
    body(
        doc,
        "The gold leaf is absent. Cosine ranks fridge ownership and acknowledgment sections instead. "
        "The same leaf sits at dense rank 17 if k is raised to 20 (cosine 0.26). A vector-only pipeline "
        "that sends the top 10 (or the Cohere top 5 of that list) never sees the caffeine rule.",
    )
    add_table(
        doc,
        ["dense", "cosine", "section"],
        [
            ["1", "0.469", "Health 7. Acknowledgment"],
            ["2", "0.469", "HR 7.1 Ownership"],
            ["3", "0.450", "HR 8. Enforcement and Culture"],
            ["4", "0.444", "Preparedness 11. Acknowledgment"],
            ["5", "0.436", "HR 1. Purpose"],
            ["6", "0.435", "HR 7.3 Weekend Abandonment"],
            ["7", "0.422", "Preparedness 2. Scope"],
            ["8", "0.422", "Health 2. Scope"],
            ["9", "0.421", "Health 1. Purpose"],
            ["10", "0.420", "Preparedness 7.2 AI Conduct"],
        ],
        [1.0, 1.2, 4.9],
    )

    heading(doc, "BM25 (sparse top 5)", 3)
    add_table(
        doc,
        ["sparse", "bm25", "section"],
        [
            ["1", "14.57", "Health 5.2 Monitoring and Tapering  ← gold"],
            ["2", "7.40", "Time & Usage 2. Scope"],
            ["3", "5.86", "Preparedness 3.2 Weapon Eligibility"],
            ["4", "5.14", "Health 2. Scope"],
            ["5", "5.01", "HR 7.3 Weekend Abandonment"],
        ],
        [1.0, 1.2, 4.9],
    )

    heading(doc, "Hybrid + Cohere rerank", 3)
    body(
        doc,
        "Union by chunk id: gold has dense_rank=None, sparse_rank=1. It is the first BM25-only leftover "
        "after the ten dense hits. Cohere then puts that BM25-only hit first for generation. Hybrid "
        "recall of the gold leaf is 1 where vector-only is 0.",
    )
    add_table(
        doc,
        ["rerank", "score", "dense", "sparse", "section"],
        [
            ["1", "0.778", "—", "1", "Health 5.2 Monitoring and Tapering  ← gold"],
            ["2", "0.037", "10", "—", "Preparedness 7.2 AI Conduct"],
            ["3", "0.023", "3", "—", "HR 8. Enforcement and Culture"],
            ["4", "0.020", "7", "—", "Preparedness 2. Scope"],
            ["5", "0.017", "—", "2", "Time & Usage 2. Scope"],
        ],
        [1.0, 1.0, 0.9, 1.0, 3.2],
    )
    add_placeholder(
        doc,
        "screenshots/05b-hybrid-beats-dense.png",
        "Terminal output of python -m utility.show_compare on the alphabetizing query. The gold Health "
        "5.2 row must be missing from dense and present (rank 1) in sparse / hybrid.",
        extra="Pair with pytest tests/test_hybrid_outperform.py if you want the assertion in the same shot.",
    )


def add_section_rerank(doc: Document) -> None:
    heading(doc, "6. Reranking")
    body(
        doc,
        "Cohere rerank-v3.5 scores the full dense/BM25 union. Input order is not treated as a rank. "
        "The top 5 documents are what generation sees. The header line is stripped so the model ranks "
        "policy body, not the leaf title prefix.",
    )
    add_code_block(
        doc,
        read_excerpt("src/retrieval/rerank.py", 1, 49),
        caption="src/retrieval/rerank.py",
    )
    add_code_block(
        doc,
        read_excerpt("src/adapter/rerank_adapter.py", 10, 76),
        caption="src/adapter/rerank_adapter.py — Cohere v2 rerank",
    )
    add_placeholder(
        doc,
        "screenshots/06-rerank-code.png",
        "IDE screenshot of src/retrieval/rerank.py and src/adapter/rerank_adapter.py.",
        extra="Optional: include a show_hybrid --rerank JSON snippet showing rerank scores.",
    )


def add_section_eval_code(doc: Document) -> None:
    heading(doc, "7. Evaluation test set and harness")
    body(
        doc,
        "Gold questions live in evaluation_harness/gold_set.json (11 cases, above the required eight). "
        "The harness scores union recall, Cohere top-5 recall, router lane, answer key phrases, and "
        "latency. Pytest in tests/test_eval.py asserts every case.",
    )
    add_code_block(
        doc,
        "python -m pytest tests/test_eval.py -v --tb=short",
        caption="Live eval (writes results/eval_report.md and results/eval_results.json)",
    )

    heading(doc, "Gold set", 2)
    add_table(
        doc,
        ["id", "lane", "question (short)", "Must appear in answer"],
        [
            ["gym-minimum", "current", "Gym sessions / length", "three / 3, and 45"],
            ["intern-gym-exempt", "current", "Interns and gym minimum", "exempt / not required"],
            ["caffeine-limit", "current", "Daily caffeine limit", "400"],
            ["dog-adoption-leave", "current", "Paid days for adopting a dog", "7"],
            ["email-joke", "current", "Must emails include a joke?", "joke"],
            ["foosball-winner-tokens", "current", "Winner-takes-tokens rule", "winner/defeat + token"],
            ["token-allocation-current", "current", "Tokens per six-hour cycle", "500,000"],
            ["token-allocation-history", "history", "What changed for tokens?", "1,000,000 and 500,000"],
            ["hazmat-suit", "current", "How to get a hazmat suit", "top 10 / leaderboard"],
            ["nuclear-shelter", "current", "Where to shelter", "refrigerator / fridge"],
            ["nuclear-history-wait", "history", "Old all-clear timing", "two hours"],
        ],
        [2.15, 0.9, 2.15, 1.9],
    )
    add_placeholder(
        doc,
        "screenshots/07a-gold-set.png",
        "IDE or editor screenshot of evaluation_harness/gold_set.json showing several cases, including "
        "a current and a history item.",
    )

    heading(doc, "Scoring", 2)
    add_code_block(
        doc,
        read_excerpt("evaluation_harness/scoring.py", 41, 52),
        caption="evaluation_harness/scoring.py — answer_covers() and recall_ok()",
    )

    heading(doc, "Harness loop", 2)
    add_code_block(
        doc,
        read_excerpt("evaluation_harness/run.py", 83, 143),
        caption="evaluation_harness/run.py — route, hybrid, rerank, generate, score",
    )
    add_code_block(
        doc,
        read_excerpt("tests/test_eval.py", 13, 55),
        caption="tests/test_eval.py — per-case pytest assertions",
    )
    add_placeholder(
        doc,
        "screenshots/07b-eval-harness-code.png",
        "IDE screenshot of evaluation_harness/run.py (the scoring loop) and tests/test_eval.py.",
    )


def add_section_eval_terminal(doc: Document) -> None:
    heading(doc, "8. Evaluation harness results")
    body(
        doc,
        "Last live run scored 11/11 on union recall, rerank@5 recall, answer accuracy, and router "
        "accuracy. Mean end-to-end latency was 17.45 seconds per question, dominated by generation.",
    )
    add_table(
        doc,
        ["Metric", "What it measures", "Score"],
        [
            ["Retrieval recall (union)", "Gold chunk(s) in the dense/BM25 pool", "11/11 (100.0%)"],
            ["Retrieval recall (rerank@5)", "Gold chunk in the Cohere top 5", "11/11 (100.0%)"],
            ["Answer accuracy", "Generated answer contains every key group", "11/11 (100.0%)"],
            ["Router accuracy", "Lane is current vs history as labeled", "11/11 (100.0%)"],
            ["Average latency", "Mean end-to-end time per question", "17.45s"],
        ],
        [2.3, 3.1, 1.7],
    )
    add_table(
        doc,
        ["Stage", "Mean", "Total (11 questions)"],
        [
            ["route", "2.40s", "26.44s"],
            ["retrieve", "1.19s", "13.12s"],
            ["rerank", "0.26s", "2.81s"],
            ["generate", "13.60s", "149.64s"],
            ["end-to-end", "17.45s", "192.01s"],
        ],
        [2.3, 2.4, 2.4],
    )
    add_table(
        doc,
        ["id", "lane", "union", "rerank@5", "answer", "total s"],
        [
            ["gym-minimum", "current (llm)", "pass", "pass", "pass", "24.16"],
            ["intern-gym-exempt", "current (llm)", "pass", "pass", "pass", "16.17"],
            ["caffeine-limit", "current (llm)", "pass", "pass", "pass", "18.73"],
            ["dog-adoption-leave", "current (llm)", "pass", "pass", "pass", "15.52"],
            ["email-joke", "current (llm)", "pass", "pass", "pass", "16.77"],
            ["foosball-winner-tokens", "current (llm)", "pass", "pass", "pass", "15.62"],
            ["token-allocation-current", "current (llm)", "pass", "pass", "pass", "17.96"],
            ["token-allocation-history", "history (llm)", "pass", "pass", "pass", "18.24"],
            ["hazmat-suit", "current (llm)", "pass", "pass", "pass", "16.54"],
            ["nuclear-shelter", "current (llm)", "pass", "pass", "pass", "15.67"],
            ["nuclear-history-wait", "history (llm)", "pass", "pass", "pass", "16.63"],
        ],
        [2.3, 1.5, 0.8, 1.0, 0.8, 0.7],
    )
    add_code_block(
        doc,
        "Eval scores: retrieval recall (rerank@5) 11/11 (100.0%)  "
        "answer accuracy 11/11 (100.0%)  latency mean 17.45s  total 192.01s\n"
        "Wrote results/eval_results.json\n"
        "Wrote results/eval_report.md",
        caption="Harness summary line (from evaluation_harness/run.py)",
    )
    add_placeholder(
        doc,
        "screenshots/08-eval-harness-terminal.png",
        "Terminal of python -m pytest tests/test_eval.py -v --tb=short, including the harness summary "
        "with recall and accuracy (11/11) and the pytest PASSED lines.",
        extra="Scroll so both the per-question log and the final scores are visible, or use two stacked shots in one image.",
    )


def add_section_diagnosis(doc: Document) -> None:
    heading(doc, "9. Planted issue: question, flawed answer, diagnosis")
    body(
        doc,
        "The probing question is a current-rule ask that matches both versions. With no version filter, "
        "dense search ranks the v1 and v2 nuclear leaves together because the wording is almost the "
        "same. The generator then has two live-looking excerpts that contradict each other.",
    )

    heading(doc, "The question", 2)
    add_callout(
        doc,
        "Probing question",
        "When can I go outside after a nuclear blast?",
    )
    italic_note(
        doc,
        "This is not phrased as history (“what changed”, “old version”). A current-lane router would "
        "drop stale v1. The flawed answer below is what happens when both files are treated as in force.",
    )

    heading(doc, "The system’s flawed answer", 2)
    body(
        doc,
        "Without the stale filter, retrieved context includes Preparedness v1 §4.2 (two hours) and "
        "Preparedness v2 §4.3 (two weeks). A grounded model should not invent a third number, so it "
        "surfaces both. That looks like a confused assistant. The confusion is already in the corpus.",
    )
    add_callout(
        doc,
        "Flawed answer (unfiltered retrieval — both versions treated as live)",
        "You may go outside after a two-hour waiting period, assuming radiation levels are acceptable. "
        "You must also remain indoors for a minimum of two weeks following the event, and going outside "
        "before that is prohibited except for verified emergency personnel.",
    )
    body(
        doc,
        "The same pattern appears for tokens. “How many tokens do I get at the start of each six-hour "
        "cycle?” retrieves 1,000,000 from v1 and 500,000 from v2 unless stale v1 is dropped. The "
        "answer becomes both numbers, or an ambiguous mix.",
    )
    add_placeholder(
        doc,
        "screenshots/09-planted-issue-flawed-answer.png",
        "Capture the probing question and the conflicting answer in one frame: terminal, notebook, or "
        "chat UI. Ideally show retrieved chunks from both v1 (two hours) and v2 (two weeks).",
        extra="If you re-run this, temporarily search with no stale filter, or use the history pool without saying so in the question, so both versions appear.",
    )

    heading(doc, "Written diagnosis", 2)
    body(
        doc,
        "Root cause is source data, not the embedder, the index, or the generator.",
    )
    bullets(
        doc,
        [
            "Two files for one policy are both in docs/ and both are ingested: Preparedness Policy v1.0.pdf and Preparedness Policy v2.0.docx.",
            "v1 §4.2 All-Clear Timing says employees may go outside after two hours. v2 §4.3 Duration of Sheltering says remain indoors for two weeks.",
            "The question “when can I go outside after a blast?” is semantically identical to both sections, so cosine retrieval ranks both.",
            "Once both excerpts are in the prompt and both look current, a grounded model should report the conflict rather than pick a winner. Hedging is correct behavior on bad inputs.",
            "Chunking, embeddings, and generation are doing what they should with conflicting excerpts. Fixing the answer by prompting “prefer v2” would hide the data bug.",
        ],
    )

    heading(doc, "Trace from answer back to files", 3)
    add_table(
        doc,
        ["Observed in the answer", "Retrieved leaf", "Source file and section"],
        [
            [
                "two-hour waiting period",
                "preparedness-policy:v1.0:nuclear-apocalypse-protocol:all-clear-timing",
                "docs/Preparedness Policy v1.0.pdf — §4.2 All-Clear Timing",
            ],
            [
                "remain indoors for two weeks",
                "preparedness-policy:v2.0:nuclear-apocalypse-protocol-updated:duration-of-sheltering",
                "docs/Preparedness Policy v2.0.docx — §4.3 Duration of Sheltering",
            ],
        ],
        [2.2, 2.5, 2.4],
    )

    heading(doc, "Why this is not a pipeline bug", 3)
    bullets(
        doc,
        [
            "Both versions are real files in docs/ and both are ingested on purpose.",
            "The questions are semantically identical across versions, so dense search ranks both.",
            "Once both excerpts are in the prompt, a grounded model should surface the conflict rather than invent a third number.",
            "After ingest, v1 nuclear and token leaves are marked stale and v2 added. The router is a retrieve-time filter on that metadata. It does not rewrite the PDFs.",
        ],
    )

    heading(doc, "What the current pipeline does about it", 3)
    body(
        doc,
        "Mitigation is retrieve-time, not a rewrite of the handbooks. The router sends “current rule” "
        "questions to in-force leaves only (change_status != stale) and “what changed / old version” "
        "questions to the full history pool.",
    )
    add_table(
        doc,
        ["Lane", "Filter", "Nuclear wait", "Token allocation"],
        [
            [
                "current (default)",
                "drop stale",
                "refrigerator / two weeks",
                "500,000 per cycle",
            ],
            [
                "history",
                "keep v1 and v2",
                "previously two hours / now two weeks",
                "previously 1,000,000 / now 500,000",
            ],
        ],
        [1.6, 1.4, 2.1, 2.0],
    )
    add_code_block(
        doc,
        read_excerpt("src/retrieval/filters.py", 8, 12),
        caption="src/retrieval/filters.py — current lane drops stale chunks",
    )
    body(
        doc,
        "Eval cases nuclear-shelter, nuclear-history-wait, token-allocation-current, and "
        "token-allocation-history check both lanes. With the filter on, the gym-style current question "
        "no longer mixes versions. The planted files remain in the corpus so the defect can still be "
        "demonstrated.",
    )


def add_section_attribution(doc: Document) -> None:
    heading(doc, "10. Source attribution")
    body(
        doc,
        "Answers are grounded in retrieved excerpts only. The answer body does not name policies or "
        "section numbers. Those live in a separate sources list (show_answer) and in retrieved_chunks "
        "(generation JSON): policy_id, version, section, rerank_Score.",
    )
    add_code_block(
        doc,
        'python -m utility.show_answer "How many gym sessions per week am I expected to complete, and how long is each session?"',
        caption="Command",
    )

    heading(doc, "Answer with cited sources", 2)
    add_callout(
        doc,
        "Answer",
        "You are expected to complete a minimum of three structured training sessions per week, with "
        "each session lasting at least 45 minutes. These sessions should include a mix of resistance "
        "training and cardiovascular conditioning. A suggested schedule is two days for resistance "
        "training, one day for cardio or conditioning, and at least one full rest day.",
    )
    add_code_block(
        doc,
        "Sources\n"
        "- Health & Wellness Policy v1.0 - 3. Gym Routine Requirements > 3.1 Minimum Requirement (in force) "
        "[rerank=0.8256 cosine=- bm25=- dense=1 sparse=1]\n"
        "- Health & Wellness Policy v1.0 - 3. Gym Routine Requirements > 3.2 Suggested Weekly Split (in force) "
        "[rerank=0.3352 dense=2 sparse=-]\n"
        "- Time and Usage Policy v2.0 - 4. Foosball Time and the Winner-Takes-Tokens Rule > 4.1 Daily Allowance (in force) "
        "[rerank=0.0935 dense=8 sparse=4]\n"
        "- Health & Wellness Policy v1.0 - 4. Protein Intake Guidelines > 4.3 Adjusting for Training Intensity (in force) "
        "[rerank=0.0905 dense=3 sparse=-]\n"
        "- Health & Wellness Policy v1.0 - 4. Protein Intake Guidelines > 4.2 Recommended Intake by Body Weight and Height (in force) "
        "[rerank=0.0846 dense=5 sparse=-]",
        caption="Citation block from python -m utility.show_answer (ranks from the live eval run)",
    )
    add_code_block(
        doc,
        read_excerpt("src/generation/generate.py", 104, 134),
        caption="src/generation/generate.py — _citation() display string",
    )
    add_placeholder(
        doc,
        "screenshots/10-source-attribution.png",
        "Terminal of python -m utility.show_answer (or python -m generation) showing the answer "
        "immediately followed by Sources / retrieved_chunks with policy, version, and section.",
        extra="Gym-minimum is a clean example. Foosball or nuclear-shelter also work.",
    )


def add_section_passing(doc: Document) -> None:
    heading(doc, "11. Passing pipeline run")
    body(
        doc,
        "The submission is confirmed by the live gold-set eval (Section 8) plus the CI gate that "
        "requires retrieval recall 1.0, answer accuracy 1.0, and at least eight questions.",
    )
    add_code_block(
        doc,
        "python -m pytest tests/test_eval.py -v --tb=short\n"
        "python -m pytest tests/test_ingestion.py tests/test_retrieval.py tests/test_generation.py "
        "tests/test_schema.py tests/test_gold_set.py tests/test_eval_support.py -v\n"
        "python -m pytest tests/test_hybrid_outperform.py -v",
        caption="Commands that confirm the full stack",
    )
    add_table(
        doc,
        ["Check", "Result"],
        [
            ["Union recall", "11/11 (100%)"],
            ["Rerank@5 recall", "11/11 (100%)"],
            ["Answer accuracy", "11/11 (100%)"],
            ["Router accuracy", "11/11 (100%)"],
            ["Gold set size", "11 (≥ 8 required)"],
            ["CI evaluate gate", "recall=1.000 accuracy=1.000 questions=11"],
        ],
        [2.8, 4.3],
    )
    add_code_block(
        doc,
        read_excerpt(".github/workflows/ci.yml", 55, 69),
        caption=".github/workflows/ci.yml — Evaluate step",
    )
    add_placeholder(
        doc,
        "screenshots/11-passing-pipeline.png",
        "Terminal showing pytest tests/test_eval.py all PASSED, with the harness summary "
        "recall=11/11 and accuracy=11/11. A green CI Evaluate log is also acceptable.",
        extra="If the terminal is long, crop to the final PASSED summary plus the eval score line.",
    )


def add_close(doc: Document) -> None:
    heading(doc, "Appendix — how to finish the PDF")
    bullets(
        doc,
        [
            "Create screenshots/ at the repo root and save captures using the names in the screenshot index.",
            "Paste each image over the matching gray placeholder (or insert the image under the path line and delete the box).",
            "Add Section 2 when ready: terminal of the minimal two-text embed-store-retrieve loop. Place it between Sections 1 and 3.",
            "Export this document to a single PDF. Keep section order. Do not omit the diagnosis in Section 9.",
        ],
    )
    italic_note(
        doc,
        "Supporting write-ups already in the repo: results/data_quality.md, results/hybrid_vs_dense.md, "
        "results/eval_report.md, results/eval_results.json.",
    )


def build() -> Path:
    doc = Document()
    configure_styles(doc)
    add_cover(doc)
    add_overview(doc)
    add_section_source_docs(doc)
    add_section_deferred_loop(doc)
    add_section_pipeline_code(doc)
    add_section_rag_e2e(doc)
    add_section_hybrid(doc)
    add_section_rerank(doc)
    add_section_eval_code(doc)
    add_section_eval_terminal(doc)
    add_section_diagnosis(doc)
    add_section_attribution(doc)
    add_section_passing(doc)
    add_close(doc)
    doc.save(OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
