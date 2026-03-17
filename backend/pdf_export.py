"""
Generate a styled PDF of the itinerary using ReportLab.
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER

PURPLE = colors.HexColor("#7c3aed")
PINK   = colors.HexColor("#db2777")
LIGHT  = colors.HexColor("#f3f4f6")
MUTED  = colors.HexColor("#6b7280")
AMBER  = colors.HexColor("#f59e0b")

SLOT_BG = {
    "morning":   colors.HexColor("#fffbeb"),
    "afternoon": colors.HexColor("#eff6ff"),
    "evening":   colors.HexColor("#f5f3ff"),
}
SLOT_ICON = {"morning": "Morning", "afternoon": "Afternoon", "evening": "Evening"}


def build_pdf(itinerary: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm)

    story = []

    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=24,
        textColor=PURPLE, alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle("sub",   fontName="Helvetica", fontSize=12,
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=2)
    body_style  = ParagraphStyle("body",  fontName="Helvetica", fontSize=10,
        textColor=colors.black, spaceAfter=2)
    tip_style   = ParagraphStyle("tip",   fontName="Helvetica-Oblique", fontSize=9,
        textColor=AMBER)

    story.append(Paragraph("PlanMyTrip", title_style))
    story.append(Paragraph(
        f"AI-Generated Itinerary for <b>{itinerary.get('destination','')}</b>", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=10))

    # Summary
    summary_data = [
        ["Destination", itinerary.get("destination","—"),
         "Duration", f"{itinerary.get('total_days','—')} days"],
        ["Budget", f"Rs.{int(itinerary.get('total_budget',0)):,}",
         "Estimated Cost", f"Rs.{int(itinerary.get('total_estimated_cost',0)):,}"],
        ["Travel Type", itinerary.get("travel_type","—"),
         "Weather", itinerary.get("weather",{}).get("description","—").capitalize()],
    ]
    st = Table(summary_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f9f5ff")),
        ("TEXTCOLOR",  (0,0), (0,-1), PURPLE), ("TEXTCOLOR", (2,0), (2,-1), PURPLE),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 9),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#e9d5ff")),
        ("PADDING",    (0,0), (-1,-1), 6),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.3*cm))

    if itinerary.get("weather_note"):
        story.append(Paragraph(f"Weather Advisory: {itinerary['weather_note']}", tip_style))
    story.append(Spacer(1, 0.4*cm))

    # Budget breakdown
    bd = itinerary.get("budget_breakdown", {})
    if bd:
        story.append(Paragraph("Budget Breakdown", ParagraphStyle("h2",
            fontName="Helvetica-Bold", fontSize=13, textColor=PURPLE, spaceAfter=6)))
        bd_data = [["Category", "Amount"]] + [[k.capitalize(), f"Rs.{int(v):,}"] for k, v in bd.items()]
        bt = Table(bd_data, colWidths=[8*cm, 5*cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), PURPLE), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, colors.HexColor("#fdf4ff")]),
            ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#e9d5ff")),
            ("PADDING",    (0,0), (-1,-1), 6),
        ]))
        story.append(bt)
        story.append(Spacer(1, 0.4*cm))

    # Day-wise
    story.append(Paragraph("Day-wise Itinerary", ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=13, textColor=PURPLE, spaceAfter=6)))

    for day in itinerary.get("days", []):
        dh = Table([[f"Day {day['day']}  -  {day.get('theme','')}",
                     f"Total: Rs.{int(day.get('day_total_cost',0)):,}"]],
                   colWidths=[12*cm, 5*cm])
        dh.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), PURPLE), ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
            ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 10),
            ("PADDING",    (0,0), (-1,-1), 8), ("ALIGN", (1,0), (1,0), "RIGHT"),
        ]))
        story.append(dh)

        for slot_key in ["morning", "afternoon", "evening"]:
            slot = day.get(slot_key, {})
            if not slot:
                continue
            sd = [[SLOT_ICON[slot_key], slot.get("place",""),
                   slot.get("activity",""), slot.get("duration",""),
                   f"Rs.{int(slot.get('cost',0)):,}"]]
            slot_tbl = Table(sd, colWidths=[2.5*cm, 3.5*cm, 6*cm, 2.5*cm, 2.5*cm])
            slot_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), SLOT_BG[slot_key]),
                ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 8),
                ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
                ("PADDING",    (0,0), (-1,-1), 5),
                ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
            ]))
            story.append(slot_tbl)

        if day.get("tip"):
            story.append(Paragraph(f"Tip: {day['tip']}", tip_style))
        story.append(Spacer(1, 0.3*cm))

    packing = itinerary.get("packing_tips", [])
    if packing:
        story.append(HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=8))
        story.append(Paragraph("Packing Tips", ParagraphStyle("h2",
            fontName="Helvetica-Bold", fontSize=13, textColor=PURPLE, spaceAfter=6)))
        for tip in packing:
            story.append(Paragraph(f"->  {tip}", body_style))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Generated by PlanMyTrip - AI-Based Personalized Travel Planner",
        ParagraphStyle("footer", fontName="Helvetica", fontSize=8,
                       textColor=MUTED, alignment=TA_CENTER)))

    doc.build(story)
    return buf.getvalue()
