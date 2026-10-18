"""Compile the complete continuing PED, preserving historical sources and approvals.

Run from any directory. Install requirements-docs.txt first. Wide registers render
as labelled records so that all fields remain legible in a portrait PDF.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import markdown
import pypdfium2 as pdfium
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import Font
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
PED = ROOT / "docs/PED"
INK = colors.HexColor("#183d4a")
MUTED = colors.HexColor("#52636b")
RULE = colors.HexColor("#ccd7dc")
PALE = colors.HexColor("#f0f5f6")
PAGE_WIDTH, PAGE_HEIGHT = A4
WIDTH = PAGE_WIDTH - 88


class StrikeExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"(~~)(.+?)~~", "strike"), "ped-strike", 175,
        )


def normalize(text: str) -> str:
    return (text.replace("\u2013", "-").replace("\u2014", "-")
            .replace("\u2011", "-").replace("\u2192", " -> ")
            .replace("\u2264", "<=").replace("\u2265", ">="))


def setup_styles():
    fonts = Path("C:/Windows/Fonts")
    if (fonts / "arial.ttf").exists():
        for name, filename in [("Body", "arial.ttf"), ("Body-Bold", "arialbd.ttf"),
                               ("Body-Italic", "ariali.ttf"),
                               ("Body-BoldItalic", "arialbi.ttf")]:
            pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    else:
        for name, base in [("Body", "Helvetica"), ("Body-Bold", "Helvetica-Bold"),
                           ("Body-Italic", "Helvetica-Oblique"),
                           ("Body-BoldItalic", "Helvetica-BoldOblique")]:
            pdfmetrics.registerFont(Font(name, base, "WinAnsiEncoding"))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic", boldItalic="Body-BoldItalic")
    symbol_fonts = [fonts / "seguisym.ttf",
                    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for symbol_font in symbol_fonts:
        if symbol_font.exists():
            pdfmetrics.registerFont(TTFont("Symbols", str(symbol_font)))
            break
    styles = getSampleStyleSheet()
    for name in ["Normal", "BodyText", "Heading1", "Heading2", "Heading3", "Title"]:
        styles[name].fontName = "Body-Bold" if name.startswith("Heading") or name == "Title" else "Body"
    styles["Title"].fontSize, styles["Title"].leading = 28, 34
    styles["Title"].alignment = 0
    styles["BodyText"].fontSize, styles["BodyText"].leading = 9.5, 13
    styles["BodyText"].spaceAfter = 6
    for name, size, leading in [("Heading1", 18, 23), ("Heading2", 12.5, 17),
                                ("Heading3", 10.5, 14)]:
        styles[name].fontSize, styles[name].leading = size, leading
        styles[name].textColor = INK
        styles[name].spaceBefore, styles[name].spaceAfter = 10, 6
        styles[name].keepWithNext = True
    styles.add(ParagraphStyle("Cell", fontName="Body", fontSize=8.5, leading=11.3,
                              splitLongWords=True, spaceAfter=0))
    styles.add(ParagraphStyle("CellHead", parent=styles["Cell"], fontName="Body-Bold",
                              textColor=colors.white))
    styles.add(ParagraphStyle("Source", parent=styles["BodyText"], fontSize=8,
                              leading=11, textColor=MUTED, spaceAfter=12))
    styles.add(ParagraphStyle("Quote", parent=styles["Source"], leftIndent=11,
                              borderColor=RULE, borderWidth=.5, borderPadding=7))
    styles.add(ParagraphStyle("CodeBlock", fontName="Courier", fontSize=7.8,
                              leading=10.5, spaceAfter=10, leftIndent=8,
                              backColor=PALE, borderPadding=7))
    styles.add(ParagraphStyle("TOC", fontName="Body", fontSize=10, leading=20,
                              leftIndent=0, firstLineIndent=0, textColor=INK))
    return styles


def parse_source(text: str):
    rendered = markdown.markdown(text, extensions=["tables", "fenced_code", StrikeExtension()])
    return ET.fromstring("<root>" + rendered + "</root>")


def section_title(path: Path, root: ET.Element) -> str:
    first = next((el for el in root if el.tag == "h1"), None)
    title = "".join(first.itertext()) if first is not None else path.stem
    number = str(int(path.name[:2]))
    title = re.sub(r"^PED\s*\u00a7\s*\d+\s*[-\u2013\u2014]?\s*", "", title)
    title = re.sub(r"^\d+\.\s*", "", title)
    return normalize((number + ". " if number != "0" else "") + title)


class Renderer:
    def __init__(self, styles, source_ref):
        self.styles = styles
        self.source_ref = source_ref
        self.source_path = PED / "00-document-control.md"
        self.table_records = 0

    def link(self, target):
        if target.startswith(("https://", "http://", "mailto:", "#")):
            return target
        path = ((ROOT / target) if target.startswith(("docs/", "src/", "tests/", "scripts/", "tools/"))
                else self.source_path.parent / target)
        try:
            rel = path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return "https://github.com/DonLukus/Civic-connect"
        return f"https://github.com/DonLukus/Civic-connect/blob/{self.source_ref}/{rel}"

    def inline(self, element):
        output = self.escape(element.text or "")
        for child in element:
            content = self.inline(child)
            if child.tag in ("strong", "b"):
                content = f"<b>{content}</b>"
            elif child.tag in ("em", "i"):
                content = f"<i>{content}</i>"
            elif child.tag in ("strike", "del", "s"):
                content = f"<strike>{content}</strike>"
            elif child.tag == "code":
                content = f'<font face="Courier" size="8">{content}</font>'
            elif child.tag == "a":
                url = html.escape(self.link(child.get("href", "")), quote=True)
                content = f'<a href="{url}" color="#125f78">{content}</a>'
            elif child.tag == "br":
                content = "<br/>"
            output += content + self.escape(child.tail or "")
        return output

    @staticmethod
    def escape(text):
        escaped = html.escape(normalize(text))
        if "\u2713" in escaped:
            if "Symbols" not in pdfmetrics.getRegisteredFontNames():
                raise RuntimeError("A Unicode symbol font is required to preserve historical sign-off checkmarks")
            escaped = escaped.replace("\u2713", '<font name="Symbols">\u2713</font>')
        return escaped

    def table(self, element):
        rows = element.findall(".//tr")
        if not rows:
            return []
        heads = ["".join(cell.itertext()) for cell in rows[0]]
        count = len(heads)
        if count >= 6:
            result = []
            for index, row in enumerate(rows[1:], 1):
                cells = list(row)
                if len(cells) != count:
                    raise ValueError(f"Malformed table in {self.source_path}: row {index}")
                self.table_records += 1
                key = self.inline(cells[0]) or str(index)
                values = [[Paragraph(key, self.styles["CellHead"]), ""]]
                values.extend([
                    [Paragraph(html.escape(normalize(label)), self.styles["Cell"]),
                     Paragraph(self.inline(cell) or " ", self.styles["Cell"])]
                    for label, cell in zip(heads, cells)
                ])
                table = LongTable(values, colWidths=[110, WIDTH - 110], repeatRows=1,
                                  hAlign="LEFT", splitInRow=0)
                self.style_table(table, header=True)
                table.setStyle(TableStyle([("SPAN", (0, 0), (-1, 0))]))
                result.extend([table, Spacer(1, 9)])
            return result
        values = [[Paragraph(self.inline(cell) or " ", self.styles["CellHead"] if i == 0 and any(heads)
                             else self.styles["Cell"]) for cell in row]
                  for i, row in enumerate(rows)]
        if count == 2:
            fractions = [.27, .73]
        elif count == 3:
            fractions = [.26, .31, .43]
        else:
            scores = [max(12, min(180, sum(len("".join(list(row)[c].itertext()))
                                          for row in rows) / len(rows))) ** .65
                      for c in range(count)]
            minimum = 36
            widths = [minimum + (WIDTH - minimum * count) * s / sum(scores) for s in scores]
            fractions = [w / WIDTH for w in widths]
        table = LongTable(values, colWidths=[WIDTH * f for f in fractions],
                          repeatRows=1 if any(heads) else 0, hAlign="LEFT", splitInRow=0)
        self.style_table(table, header=any(heads),
                         padding=2.5 if self.source_path.name.startswith("22-") else 4)
        return [table, Spacer(1, 10)]

    @staticmethod
    def style_table(table, header, padding=4):
        commands = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), padding),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
                    ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [PALE, colors.white]),
                    ("LINEBELOW", (0, 0), (-1, -1), .3, RULE)]
        if header:
            commands.append(("BACKGROUND", (0, 0), (-1, 0), INK))
        table.setStyle(TableStyle(commands))

    def blocks(self, elements):
        result = []
        for element in elements:
            if element.tag in ("h1", "h2", "h3", "h4"):
                style = "Heading2" if element.tag in ("h1", "h2") else "Heading3"
                result.append(Paragraph(self.inline(element), self.styles[style]))
            elif element.tag == "p":
                result.append(Paragraph(self.inline(element), self.styles["BodyText"]))
            elif element.tag == "blockquote":
                text = "<br/>".join(self.inline(child) for child in element)
                result.append(Paragraph(text, self.styles["Quote"]))
            elif element.tag in ("ol", "ul"):
                for index, item in enumerate(element, int(element.get("start", "1"))):
                    prefix = f"{index}. " if element.tag == "ol" else "- "
                    direct = ET.Element("p")
                    direct.text = item.text
                    for child in item:
                        if child.tag not in ("p", "ol", "ul"):
                            direct.append(child)
                    if (direct.text or "").strip() or len(direct):
                        result.append(Paragraph(prefix + self.inline(direct), self.styles["BodyText"]))
                    for child in item:
                        if child.tag == "p":
                            result.append(Paragraph(prefix + self.inline(child), self.styles["BodyText"]))
                        elif child.tag in ("ol", "ul"):
                            result.extend(self.blocks([child]))
            elif element.tag == "table":
                result.extend(self.table(element))
            elif element.tag == "pre":
                code = normalize("".join(element.itertext())).expandtabs(4)
                result.append(Preformatted(code, self.styles["CodeBlock"], maxLineLength=96))
            elif element.tag == "hr":
                result.append(Spacer(1, 8))
            else:
                raise ValueError(f"Unsupported block {element.tag} in {self.source_path}")
        return result


class PEDDocument(BaseDocTemplate):
    def __init__(self, path, built_date, version="3.0"):
        super().__init__(str(path), pagesize=A4, rightMargin=44, leftMargin=44,
                         topMargin=49, bottomMargin=49,
                         title=f"CivicConnect Project Engineering Document v{version} - Review continuation",
                         author="CivicConnect team")
        self.built_date = built_date
        self.version = version
        frame = Frame(44, 49, WIDTH, PAGE_HEIGHT - 98,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="PED", frames=frame, onPage=self.page_chrome))

    def page_chrome(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Body", 7.6)
        canvas.setFillColor(MUTED)
        canvas.drawString(44, PAGE_HEIGHT - 29, "CivicConnect - SEN381 - Continuing Project Engineering Document")
        canvas.setStrokeColor(RULE)
        canvas.line(44, 36, PAGE_WIDTH - 44, 36)
        canvas.drawString(44, 24, f"PED v{self.version} - full export - {self.built_date}")
        canvas.drawRightString(PAGE_WIDTH - 44, 24, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(flowable, "ped_section"):
            title, key = flowable.ped_section
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, 0, False)
            self.notify("TOCEntry", (0, title, self.page, key))


def verify_pdf(output, sections):
    pdf = pdfium.PdfDocument(str(output))
    text_pages = []
    for page in pdf:
        text_page = page.get_textpage()
        try:
            text_pages.append(text_page.get_text_range())
        finally:
            text_page.close()
            page.close()
    lines = [line for text in text_pages for line in text.splitlines()
             if not line.startswith(("CivicConnect - SEN381 - Continuing", "PED v3.0 - full export", "PED v4.0 - full export"))
             and not re.fullmatch(r"\s*\d+\s*", line)]
    # PDFium marks a visible line-final hyphen as U+FFFE in some embedded fonts.
    # Normalize that extraction marker only; the PDF still displays the hyphen.
    all_text = re.sub(r"\s+", "", normalize("\n".join(lines)).replace("\ufffe", "-"))
    missing = []
    checked = 0
    for path, root, title in sections:
        for element in root.iter():
            if element.tag not in ("p", "td", "th", "pre"):
                continue
            sample = normalize("".join(element.itertext())).strip()
            if len(sample) < 4:
                continue
            checked += 1
            if re.sub(r"\s+", "", sample) not in all_text:
                missing.append(f"{path.name}: {sample[:75]}")
    if missing:
        raise RuntimeError("PDF is missing source content: " + ", ".join(missing))
    if "~~" in all_text:
        raise RuntimeError("Literal Markdown strikethrough leaked into the PDF")
    return pdf, len(text_pages), checked


def build(output, render_dir, built_date, version="3.0"):
    output.parent.mkdir(parents=True, exist_ok=True)
    if version == "4.0":
        # Refuse an export whose scope headline no longer reconciles to the live RTM.
        with (ROOT / "docs/requirements/RTM.csv").open(encoding="utf8", newline="") as handle:
            scope_rows = list(csv.DictReader(handle))
        values = [float(row["M4 proposed AC value"]) for row in scope_rows]
        if len(scope_rows) != 40 or len({row["Acceptance criteria"] for row in scope_rows}) != 40:
            raise ValueError("M4 review requires the preserved 40-criterion baseline")
        if any(value not in (0, .5, 1) for value in values):
            raise ValueError("M4 scores must be 0, 0.5 or 1")
        summary = json.loads((ROOT / "docs/release/evidence/2026-10-18/scope-assessment.json").read_text())
        percentage = sum(values) / len(values) * 100
        if summary["proposed_points"] != sum(values) or summary["proposed_percentage"] != percentage:
            raise ValueError("M4 scope summary does not reconcile to the RTM")
        closure = (PED / "23-final-scope-and-project-conclusion.md").read_text(encoding="utf8")
        if f"{percentage:.2f}%" not in closure:
            raise ValueError("M4 PED headline does not reconcile to the RTM")
    styles = setup_styles()
    source_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    last_section = 23 if version == "4.0" else 22
    paths = [p for p in sorted(PED.glob("[0-9][0-9]-*.md")) if int(p.name[:2]) <= last_section]
    if not paths or paths[0].name != "00-document-control.md" or not paths[-1].name.startswith(f"{last_section}-"):
        raise ValueError(f"Expected document control through section {last_section}")
    required = {f"{number:02}" for number in range(last_section + 1) if number != 18}
    missing = required - {path.name[:2] for path in paths}
    if missing:
        raise ValueError("Missing required PED source sections: " + ", ".join(sorted(missing)))
    sections = [(path, parse_source(path.read_text(encoding="utf8"))) for path in paths]
    sections = [(path, root, section_title(path, root)) for path, root in sections]
    m3_text = next(p for p in paths if p.name.startswith("22-")).read_text(encoding="utf8")
    match = re.search(r"Merged into `main` at commit `([a-f0-9]{40})` via PR #(\d+)", m3_text)
    if not match:
        raise ValueError("Section 22 must identify the actual implementation baseline")
    implementation_sha, implementation_pr = match.groups()
    status_match = re.search(r"\*\*Public production release: (READY|CONDITIONALLY READY|NOT READY)\.\*\*", m3_text)
    if not status_match:
        raise ValueError("Section 22 must state the production release classification")
    production_status = status_match.group(1)
    gap_note = ("The repository has no section 18 source. Existing numbering is preserved; "
                "this export does not invent the missing technology narrative or promote any baseline/ADR status."
                if "18" not in {path.name[:2] for path in paths} else
                f"All numbered sections 00 through {last_section} have source files. Historical baseline and ADR statuses retain their scope.")
    renderer = Renderer(styles, source_ref)
    story = [Spacer(1, 38), Paragraph("CivicConnect", styles["Title"]),
             Paragraph(f"Project Engineering Document v{version} - review candidate", styles["Heading1"]),
             Paragraph("Engineering foundation, architecture, construction and verification", styles["BodyText"]),
             Spacer(1, 17)]
    cover = [
        f"<b>Full continuing PED - {built_date}</b><br/>SEN381 Software Engineering 381<br/>Belgium Campus ITversity",
        "<b>Team:</b> Group U - Emile, Don and Masego" if version == "4.0" else "<b>Team:</b> Emile, Don and Masego",
        (f"<b>M3 implementation baseline:</b> {implementation_sha}<br/>Merged through PR #{implementation_pr}. "
        "The recorded approvals concern that implementation slice. Check the associated documentation PR for this export's review status."),
        ('<b>Repository:</b> <a href="https://github.com/DonLukus/Civic-connect" color="#125f78">'
        'github.com/DonLukus/Civic-connect</a>'),
        ("<b>Continuity:</b> This export includes every numbered Markdown source currently present in docs/PED, "
        f"starting with document control, preserving M1/M2/M3, and continuing through section {last_section}. "
        "Earlier statements and signatures retain their dated scope. Read the latest dated closure section for current status."),
        "<b>Source boundary:</b> " + gap_note,
        ("<b>Assessment access:</b> RTM: docs/requirements/RTM.csv. CI/test evidence and local staging instructions "
        f"are indexed in section 22. Public production readiness: {production_status}. No new signatures appear in this export."),
    ]
    if version == "4.0":
        cover.append("<b>Submission boundary:</b> Deadline 18 October 2026, supplied by Emile. "
                     "Final team approval, deployment decision, assessed documentation reference and actual Moodle submission remain pending. "
                     "This review export is not a signed Final submission; section 23 contains the proposed original-AC scope result and unresolved obligations.")
    story.extend(Paragraph(item, styles["BodyText"]) for item in cover)
    story.extend([PageBreak(), Paragraph("Contents", styles["Heading1"])])
    toc = TableOfContents()
    toc.levelStyles = [styles["TOC"]]
    toc.dotsMinLevel = 0
    story.append(toc)
    for path, root, title in sections:
        story.append(PageBreak())
        heading = Paragraph(html.escape(title), styles["Heading1"])
        heading.ped_section = (title, "section-" + path.name[:2])
        story.append(heading)
        source = path.relative_to(ROOT).as_posix()
        story.append(Paragraph(f"Source: {source}", styles["Source"]))
        renderer.source_path = path
        if path.name.startswith("22-"):
            renderer.styles = {**styles.byName, "BodyText": ParagraphStyle(
                "M3Body", parent=styles["BodyText"], leading=12, spaceAfter=4,
            )}
        blocks = list(root)
        first_heading = next((i for i, el in enumerate(blocks) if el.tag == "h1"), None)
        if first_heading is not None:
            del blocks[first_heading]
        story.extend(renderer.blocks(blocks))
    document = PEDDocument(output, built_date, version)
    document.multiBuild(story)
    pdf, pages, checked = verify_pdf(output, sections)
    if render_dir is not None:
        render_dir.mkdir(parents=True, exist_ok=True)
        for index, page in enumerate(pdf):
            page.render(scale=1.4).to_pil().save(render_dir / f"page-{index + 1:03}.png")
    manifest = {
        "export": output.relative_to(ROOT).as_posix() if output.is_relative_to(ROOT) else str(output),
        "build_date": built_date, "pages": pages, "implementation_baseline": implementation_sha,
        "ped_version": version, "review_status": "Review candidate; no new signatures or final acceptance",
        "source_base_commit": source_ref,
        "scope": "All numbered source files included; working-branch documentation fixes require review.",
        "sources": [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                    for p in paths],
        "missing_source_numbers": [n for n in range(last_section + 1) if f"{n:02}" not in {p.name[:2] for p in paths}],
        "wide_register_records": renderer.table_records,
        "source_blocks_verified": checked,
        "pdf_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    check_dir = ROOT / ".m3-local/pdf-review"
    check_dir.mkdir(parents=True, exist_ok=True)
    (check_dir / "full-export-check.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print(json.dumps({"pages": pages, "sources_included": len(paths),
                      "wide_register_records": renderer.table_records,
                      "missing_source_numbers": manifest["missing_source_numbers"], "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--ped-version", choices=["3.0", "4.0"], default="3.0")
    parser.add_argument("--render-dir", type=Path,
                        help="Optional ignored/private directory for page PNGs")
    parser.add_argument("--build-date", default=date.today().isoformat())
    args = parser.parse_args()
    output = args.output or PED / f"exports/PED_v{args.ped_version}-review.pdf"
    build(output.resolve(), args.render_dir, args.build_date, args.ped_version)
