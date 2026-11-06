import csv
import io

from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ============================================================
# REPORT CONFIGURATION
# ============================================================

HISTORY_COLUMNS = [
    "id",
    "username",
    "authentication",
    "similarity_score",
    "threshold",
    "confidence",
    "processing_time",
    "timestamp"
]


def safe_csv_value(value):
    """Prevent spreadsheet formula injection."""

    if value is None:
        return ""

    value = str(value)

    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value

    return value


def format_value(value):
    """Format values consistently for reports."""

    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.4f}"

    return str(value)


# ============================================================
# AUTHENTICATION HISTORY CSV
# ============================================================

def generate_history_csv(records):

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(HISTORY_COLUMNS)

    for record in records:

        writer.writerow([
            safe_csv_value(record.get(column))
            for column in HISTORY_COLUMNS
        ])

    return output.getvalue().encode("utf-8-sig")


# ============================================================
# AUTHENTICATION HISTORY PDF
# ============================================================

def generate_history_pdf(records):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18
    )

    elements = []

    elements.append(
        Paragraph("SecureVoiceAI - Authentication History", title_style)
    )

    elements.append(Spacer(1, 8 * mm))

    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(f"Total Records: {len(records)}", styles["Normal"])
    )

    elements.append(Spacer(1, 6 * mm))

    headers = [
        "ID",
        "Username",
        "Status",
        "Similarity",
        "Threshold",
        "Confidence",
        "Time (s)",
        "Timestamp"
    ]

    table_data = [headers]

    for record in records:

        row = [
            record.get("id"),
            record.get("username"),
            record.get("authentication"),
            format_value(record.get("similarity_score")),
            format_value(record.get("threshold")),
            record.get("confidence") or "N/A",
            format_value(record.get("processing_time")),
            record.get("timestamp")
        ]

        table_data.append([
            Paragraph(escape(str(value)), styles["Normal"])
            for value in row
        ])

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            12 * mm,
            25 * mm,
            22 * mm,
            23 * mm,
            20 * mm,
            23 * mm,
            20 * mm,
            55 * mm
        ]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6)
    ]))

    elements.append(table)

    document.build(elements)

    return buffer.getvalue()


# ============================================================
# ANALYTICS CSV
# ============================================================

def generate_analytics_csv(analytics):

    output = io.StringIO()

    writer = csv.writer(output)

    summary = analytics.get("summary", {})

    writer.writerow(["SecureVoiceAI - Analytics Report"])
    writer.writerow(["Generated", datetime.now().isoformat(timespec="seconds")])
    writer.writerow([])

    writer.writerow(["Metric", "Value"])

    for key, value in summary.items():

        writer.writerow([
            safe_csv_value(key),
            safe_csv_value(value)
        ])

    writer.writerow([])
    writer.writerow(["Daily Activity"])
    writer.writerow(["Date", "Successful", "Failed"])

    for item in analytics.get("daily_activity", []):

        writer.writerow([
            safe_csv_value(item.get("activity_date")),
            safe_csv_value(item.get("successful")),
            safe_csv_value(item.get("failed"))
        ])

    writer.writerow([])
    writer.writerow(["Similarity Score Distribution"])
    writer.writerow(["Score Range", "Total"])

    for item in analytics.get("score_distribution", []):

        writer.writerow([
            safe_csv_value(item.get("score_range")),
            safe_csv_value(item.get("total"))
        ])

    return output.getvalue().encode("utf-8-sig")


# ============================================================
# ANALYTICS PDF
# ============================================================

def generate_analytics_pdf(analytics):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AnalyticsTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18
    )

    elements = []

    elements.append(
        Paragraph("SecureVoiceAI - Analytics Report", title_style)
    )

    elements.append(Spacer(1, 8 * mm))

    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 8 * mm))

    # Summary

    elements.append(
        Paragraph("Analytics Summary", styles["Heading2"])
    )

    summary = analytics.get("summary", {})

    summary_data = [["Metric", "Value"]]

    for key, value in summary.items():

        summary_data.append([
            Paragraph(escape(str(key)), styles["Normal"]),
            Paragraph(escape(format_value(value)), styles["Normal"])
        ])

    summary_table = Table(
        summary_data,
        colWidths=[85 * mm, 85 * mm],
        repeatRows=1
    )

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    elements.append(summary_table)

    elements.append(Spacer(1, 8 * mm))

    # Daily activity

    elements.append(
        Paragraph("Daily Authentication Activity", styles["Heading2"])
    )

    daily_data = [["Date", "Successful", "Failed"]]

    for item in analytics.get("daily_activity", []):

        daily_data.append([
            item.get("activity_date") or "N/A",
            item.get("successful", 0),
            item.get("failed", 0)
        ])

    daily_table = Table(
        daily_data,
        colWidths=[65 * mm, 55 * mm, 55 * mm],
        repeatRows=1
    )

    daily_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    elements.append(daily_table)

    elements.append(Spacer(1, 8 * mm))

    # Score distribution

    elements.append(
        Paragraph("Similarity Score Distribution", styles["Heading2"])
    )

    score_data = [["Score Range", "Total"]]

    for item in analytics.get("score_distribution", []):

        score_data.append([
            item.get("score_range") or "N/A",
            item.get("total", 0)
        ])

    score_table = Table(
        score_data,
        colWidths=[85 * mm, 85 * mm],
        repeatRows=1
    )

    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    elements.append(score_table)

    document.build(elements)

    return buffer.getvalue()