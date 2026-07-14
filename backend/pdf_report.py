"""
PDF report generator for compliance check results.
"""
from fpdf import FPDF
from datetime import datetime
from pathlib import Path


def _safe(text: str, max_len: int = 50) -> str:
    """Sanitize text: ASCII-only, truncate."""
    text = str(text or "Unnamed").encode("ascii", errors="replace").decode("ascii")
    text = text.replace("?", "")
    return text[:max_len]


def generate_pdf(report_data: dict) -> bytes:
    """Generate a PDF compliance report and return as bytes."""
    pdf = FPDF()
    pdf.add_page()

    # ── Header ──────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "BIM Compliance Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # ── Summary ─────────────────────────────────────
    total_pass = sum(r["passed"] for r in report_data.get("rules", []))
    total_fail = sum(r["failed"] for r in report_data.get("rules", []))
    total_warn = sum(r["warnings"] for r in report_data.get("rules", []))

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(30, 40, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "  Summary", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    col_w = 50
    pdf.cell(col_w, 7, f"Total Passed:  {total_pass}")
    pdf.set_text_color(0, 150, 0)
    pdf.cell(col_w, 7, f"Total Failed:  {total_fail}")
    pdf.set_text_color(200, 30, 30)
    pdf.cell(col_w, 7, f"Warnings:  {total_warn}")
    pdf.set_text_color(200, 150, 0)
    pdf.ln(12)

    # ── Rules ───────────────────────────────────────
    pdf.set_text_color(0, 0, 0)
    for rule in report_data.get("rules", []):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 245)
        pdf.cell(0, 9, f"  {_safe(rule['description'], 80)}", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Passed: {rule['passed']}    Failed: {rule['failed']}    Warnings: {rule['warnings']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Items table header
        pdf.set_fill_color(60, 70, 90)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(12, 7, "St", fill=True)
        pdf.cell(55, 7, "Element", fill=True)
        pdf.cell(55, 7, "Type", fill=True)
        pdf.cell(60, 7, "Message", fill=True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)
        for item in rule.get("items", []):
            if item["status"] == "pass":
                continue
            st = "FAIL" if item["status"] == "fail" else "WARN"
            color_map = {"fail": (200, 30, 30), "warning": (200, 150, 0)}
            pdf.set_text_color(*color_map.get(item["status"], (0, 0, 0)))

            name = _safe(item.get("name"), 28)
            etype = _safe(item.get("type"), 28)
            msg = _safe(item.get("message"), 30)

            pdf.cell(12, 7, st)
            pdf.cell(55, 7, name)
            pdf.cell(55, 7, etype)
            pdf.cell(60, 7, msg)
            pdf.ln()

            if pdf.get_y() > 260:
                pdf.add_page()

        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

    # ── Footer ──────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, "HKU AI+BIM Compliance Checker - Automated building model inspection", align="C")

    return bytes(pdf.output())


def save_pdf(report_data: dict, output_path: str):
    """Save PDF report to file."""
    data = generate_pdf(report_data)
    Path(output_path).write_bytes(data)
    return output_path
