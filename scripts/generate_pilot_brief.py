#!/usr/bin/env python3
"""Generate team-share pilot status brief (Word + PDF) for Zstate WIP."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark_v0.1"
EXPORT = ROOT / "docs" / "export"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def task_summaries() -> list[dict]:
    manifest = load_json(BENCH / "manifest.json") or {}
    rows: list[dict] = []
    for entry in manifest.get("pilot_tasks", []):
        if entry.get("status") != "published":
            continue
        task_path = BENCH / entry["paths"]["task"]
        task = load_json(task_path) or {}
        prompt = (task.get("prompt") or {}).get("text", "")
        first_line = prompt.split("\n", 1)[0].strip() if prompt else entry["task_id"]
        rows.append({
            "task_id": entry["task_id"],
            "ticker": task.get("ticker", "—"),
            "type": entry.get("task_type", task.get("task_type", "—")),
            "tier": task.get("difficulty_tier", "—"),
            "summary": first_line,
        })
    return rows


def full_campaign_summary() -> dict | None:
    report_path = BENCH / "runs" / "pilot_eval_5task_v1" / "pilot_eval_5task_v1.json"
    report = load_json(report_path)
    if not isinstance(report, dict):
        return None
    summary = report.get("summary") or {}
    return {
        "campaign_id": report.get("campaign_id", "pilot_eval_5task_v1"),
        "weighted": summary.get("weighted_composite_by_model") or {},
        "by_model_task": summary.get("by_model_task_composite_median") or {},
        "fractures": summary.get("fracture_counts") or {},
        "runs_scored": summary.get("scored", 0),
    }


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def add_para(doc: Document, text: str, *, bold: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(11)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def build_pilot_brief() -> Document:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    commit = git_head()
    tasks = task_summaries()
    eval_full = full_campaign_summary()

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)

    title = doc.add_heading("Zstate Pilot Status Brief", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(f"Work in progress — {today} · git {commit}").italic = True

    add_para(
        doc,
        "Internal team share. Covers architecture, pilot tasks, reward design, PM simulator, "
        "and early model findings. Not for external publication.",
    )

    add_heading(doc, "1. What we are building", 1)
    add_para(
        doc,
        "Zstate is an equity-research benchmark with two complementary tracks in one repo: "
        "Track A (public leaderboard, single-turn forensics/modeling tasks) and Track B "
        "(RL training env with a skeptical Portfolio Manager). Both share fixed EDGAR corpora, "
        "expert ground truth, and a fracture taxonomy.",
    )

    add_heading(doc, "Architecture (high level)", 2)
    diagram = (
        "Shared foundation: Corpus (fixed doc bundles) + Expert pipeline (CFA draft/review) "
        "+ Trajectory schema v1\n"
        "    |\n"
        "    +-- Track A (benchmark_v0.1/) -- single-turn Type F/M tasks\n"
        "    |       -> 3-layer reward (L1 accuracy / L2 gold path / L3 citations)\n"
        "    |       -> Leaderboard + fracture codes\n"
        "    |\n"
        "    +-- Track B (env_v1/) -- dual-control episodes\n"
        "            -> PM policy FSM (pushback, follow-ups, pushover trap)\n"
        "            -> 4-component reward (Outcome / Grounding / Defense / Hallucination)\n"
        "    |\n"
        "    +-- Track C (future export/) -- curated JSONL + reward vectors for training product"
    )
    add_para(doc, diagram)

    add_heading(doc, "2. Reward systems", 1)

    add_heading(doc, "Track A — 3-layer benchmark score", 2)
    table = doc.add_table(rows=4, cols=3)
    table.style = "Table Grid"
    hdr = ("Layer", "What it measures", "Typical weight (Type F)")
    for i, label in enumerate(hdr):
        table.rows[0].cells[i].text = label
    rows = [
        ("L1 Hard accuracy", "Python verify vs expert ground truth (metrics, arithmetic)", "55%"),
        ("L2 Gold path", "Section recall, tool order, workflow fidelity", "25%"),
        ("L3 Trust / citations", "Verbatim snippets, policy acks, anti-hallucination", "20%"),
    ]
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            table.rows[i].cells[j].text = val
    add_para(doc, "Composite = weighted sum. Fracture codes tag failure modes (e.g. CITE_BROAD).")

    add_heading(doc, "Track B — 4-component env reward", 2)
    add_para(
        doc,
        "Reward = 0.45·Outcome + 0.25·Grounding + 0.20·Defense − 0.10·Hallucination. "
        "Defense is env-only: rewards substantive engagement when the PM pushes back. "
        "Capitulation without retrieval triggers pushover penalties.",
    )

    add_heading(doc, "PM simulator (Track B)", 2)
    add_bullets(doc, [
        "Scripted FSM (pm_v1_1): opening skepticism -> follow-up A/B/C branches -> pushover trap.",
        "Agent tools: fixed corpus search + send_message_to_pm + submit_recommendation.",
        "Sample episode: Solaris earnings-quality dispute (env_v1/episodes/).",
        "Defense is the new discriminator vs single-turn QA — see frontier runs in env_v1/runs/.",
    ])

    add_heading(doc, "3. Published pilot tasks (5/15 MVD)", 1)
    ttable = doc.add_table(rows=len(tasks) + 1, cols=5)
    ttable.style = "Table Grid"
    for i, label in enumerate(("Task ID", "Ticker", "Type", "Tier", "Objective")):
        ttable.rows[0].cells[i].text = label
    for i, t in enumerate(tasks, start=1):
        ttable.rows[i].cells[0].text = t["task_id"]
        ttable.rows[i].cells[1].text = t["ticker"]
        ttable.rows[i].cells[2].text = t["type"]
        ttable.rows[i].cells[3].text = t["tier"]
        summary = t["summary"]
        if len(summary) > 120:
            summary = summary[:117] + "..."
        ttable.rows[i].cells[4].text = summary

    add_heading(doc, "Task highlights", 2)
    add_bullets(doc, [
        "GOOGL (F): Q1 2026 segment sum + hedging reconciling item — ceiling task for frontier models.",
        "PEP (M): FY2025 FX / organic growth decomposition from MD&A tables.",
        "AMZN (F): FY2025 segment operating income bridge with stock-based comp decoy.",
        "NFLX (F): FY2025 cash content guidance vs nine-month YTD actuals (guidance drift).",
        "KO (F, new): FY2025 five-segment Total net revenues + Corporate + Eliminations bridge "
        "to $47,941M consolidated; LatAm (2)% total vs (12)% FX from MD&A.",
    ])

    add_heading(doc, "4. Eval methodology", 1)
    add_bullets(doc, [
        "Campaign runner: benchmark_v0.1/scripts/run_benchmark_campaign.py",
        "Eval mode ON: generic citation rules only (no task-specific cheat-sheets).",
        "Path roles: canonical slugs (segment_financials, narrative_fx) — not issuer note numbers.",
        "Headline composite excludes GOOGL (ceiling); PEP + AMZN + NFLX (+ KO in 5-task campaigns).",
        "Models routed: OpenAI (gpt-*), Anthropic (claude-*), Gemini (gemini-* via OpenAI-compatible API).",
        "3 runs per task (median) for all models in pilot_eval_5task_v1.",
    ])

    add_heading(doc, "5. Findings (July 2026 pilot)", 1)

    add_heading(doc, "Full 5-task eval (pilot_eval_5task_v1)", 2)
    if eval_full and eval_full.get("runs_scored"):
        add_para(
            doc,
            f"Campaign {eval_full['campaign_id']}: {eval_full['runs_scored']} runs scored "
            "(5 tasks x 3 models x 3 runs). Headline = PEP + AMZN + NFLX + KO (excl. GOOGL).",
        )
        ranked = sorted(
            eval_full["weighted"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        rtable = doc.add_table(rows=len(ranked) + 1, cols=2)
        rtable.style = "Table Grid"
        rtable.rows[0].cells[0].text = "Model"
        rtable.rows[0].cells[1].text = "Headline weighted composite"
        for i, (model, score) in enumerate(ranked, start=1):
            rtable.rows[i].cells[0].text = model
            rtable.rows[i].cells[1].text = f"{score:.3f}"
        if eval_full.get("by_model_task"):
            add_para(doc, "Per-task medians by model:", bold=True)
            tasks = sorted(next(iter(eval_full["by_model_task"].values())).keys())
            mtable = doc.add_table(
                rows=len(tasks) + 1,
                cols=len(eval_full["by_model_task"]) + 1,
            )
            mtable.style = "Table Grid"
            mtable.rows[0].cells[0].text = "Task"
            for j, model in enumerate(sorted(eval_full["by_model_task"]), start=1):
                mtable.rows[0].cells[j].text = model.replace("-", " ")
            for i, tid in enumerate(tasks, start=1):
                mtable.rows[i].cells[0].text = tid.replace("_", " ")
                for j, model in enumerate(sorted(eval_full["by_model_task"]), start=1):
                    val = eval_full["by_model_task"][model].get(tid)
                    mtable.rows[i].cells[j].text = f"{val:.3f}" if val is not None else "-"
        if eval_full.get("fractures"):
            add_para(doc, f"Fractures (all runs): {eval_full['fractures']}")
    else:
        add_para(doc, "Full 5-task eval not yet scored.")

    add_para(doc, "Interpretation:", bold=True)
    add_bullets(doc, [
        "KO_footnote_reconciliation is the universal gap — all three models median 0.0 on headline.",
        "Claude leads headline (0.744); Gemini close second (0.732); GPT-4o third (0.675).",
        "GOOGL ceiling task: all models median 1.0 on 3 runs.",
        "L3 citation fractures (CITE_BROAD, CITE_HALLUC) dominate; KO adds HALLUC_FILL on L1.",
    ])

    add_heading(doc, "6. WIP / next steps", 1)
    add_bullets(doc, [
        "Scale to 15-task MVD (5 companies x 3 task types) with expert sign-off pipeline.",
        "Investigate KO metric schema confusion (wrong submit keys observed on Gemini).",
        "Track B: more frontier trajectories + PM branch coverage.",
        "Expert Workbench (spec) for CFA draft -> review -> publish workflow.",
        "LATER-06: full corpus ingest with excerpt SHA pins (P3-10 mitigation on KO bundle).",
    ])

    add_para(doc, "References: docs/ARCHITECTURE.md · benchmark_v0.1/docs/PILOT_EVAL_JUL2026.md · env_v1/docs/METHODOLOGY_RL_ENV.md")
    return doc


class PDFReport(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def sanitize_for_pdf(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2192": "->",
        "\u00b7": " ",
        "\u2265": ">=",
        "\u2264": "<=",
        "\u2212": "-",
        "\u00d7": "x",
        "\u00b1": "+/-",
        "\u2022": "-",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("ascii", "replace").decode("ascii")


def pdf_multiline(pdf: FPDF, height: int, text: str) -> None:
    if not text:
        return
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def docx_to_pdf(doc_path: Path, pdf_path: Path, title: str) -> None:
    from docx import Document as DocxDocument
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    def iter_block_items(document: DocxDocument):
        parent = document.element.body
        for child in parent.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, document)
            elif isinstance(child, CT_Tbl):
                yield Table(child, document)

    d = DocxDocument(str(doc_path))
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf_multiline(pdf, 10, sanitize_for_pdf(title))
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)

    for block in iter_block_items(d):
        if isinstance(block, Paragraph):
            text = sanitize_for_pdf(block.text.strip())
            if not text:
                pdf.ln(3)
                continue
            style = block.style.name if block.style else ""
            if "Heading 1" in style:
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 14)
                pdf_multiline(pdf, 8, text)
                pdf.set_font("Helvetica", "", 10)
            elif "Heading 2" in style:
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 12)
                pdf_multiline(pdf, 7, text)
                pdf.set_font("Helvetica", "", 10)
            elif "Heading 3" in style:
                pdf.set_font("Helvetica", "B", 11)
                pdf_multiline(pdf, 6, text)
                pdf.set_font("Helvetica", "", 10)
            else:
                pdf_multiline(pdf, 5, text)
        else:
            pdf.ln(2)
            for row in block.rows:
                line = sanitize_for_pdf(" | ".join(c.text.strip().replace("\n", " ") for c in row.cells))
                if len(line) > 500:
                    line = line[:497] + "..."
                pdf.set_font("Helvetica", "", 8)
                pdf_multiline(pdf, 4, line)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)

    pdf.output(str(pdf_path))


def main() -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    doc = build_pilot_brief()
    docx_path = EXPORT / "ZSTATE_Pilot_Status_Brief_Jul2026.docx"
    pdf_path = EXPORT / "ZSTATE_Pilot_Status_Brief_Jul2026.pdf"
    doc.save(docx_path)
    docx_to_pdf(docx_path, pdf_path, "Zstate Pilot Status Brief — July 2026 (WIP)")
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
