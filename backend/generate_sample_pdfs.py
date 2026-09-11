"""
Script to generate realistic pharmaceutical complaint PDFs using ReportLab.
1. complaint_pdf_metformin.pdf (Active Pharmaceutical Ingredient - API)
2. complaint_pdf_tablet_variant.pdf (Finished Dosage Form - FDF)
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "sample_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_metformin_pdf():
    pdf_path = OUTPUT_DIR / "complaint_pdf_metformin.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#4A5568"),
    )
    section_head = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#2D3748"),
    )
    cell_val = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # Letterhead
    story.append(Paragraph("MedCore Pharmaceuticals Pvt. Ltd.", title_style))
    story.append(Paragraph("Quality Assurance & Vendor Quality Oversight Cell", subtitle_style))
    story.append(Paragraph("Plot 42-45, Phase II, Genome Valley, Hyderabad - 500078 | ISO 9001 / cGMP Certified", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2B6CB0"), spaceAfter=14))

    # Document Header Badge
    story.append(Paragraph("OFFICIAL CUSTOMER COMPLAINT REPORT", ParagraphStyle(
        "ReportBadge",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#C53030"),
        alignment=1,
        spaceAfter=12,
    )))

    # Metadata Table
    table_data = [
        [
            Paragraph("Reporting Company:", cell_bold),
            Paragraph("MedCore Pharmaceuticals Pvt. Ltd.", cell_val),
            Paragraph("Complaint Date:", cell_bold),
            Paragraph("2026-09-10", cell_val),
        ],
        [
            Paragraph("Product Name:", cell_bold),
            Paragraph("Metformin Hydrochloride API", cell_val),
            Paragraph("Complaint Type:", cell_bold),
            Paragraph("Particulate Contamination", cell_val),
        ],
        [
            Paragraph("Product Strength/Grade:", cell_bold),
            Paragraph("IP/BP", cell_val),
            Paragraph("Batch/Lot Number:", cell_bold),
            Paragraph("MFH260712A", cell_val),
        ],
        [
            Paragraph("Manufacturing Date:", cell_bold),
            Paragraph("2026-07-12", cell_val),
            Paragraph("Expiry Date:", cell_bold),
            Paragraph("2028-07-11", cell_val),
        ],
    ]

    t = Table(table_data, colWidths=[130, 160, 110, 130])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Defect Description Section
    story.append(Paragraph("Detailed Observation & Problem Narrative", section_head))
    desc_p = Paragraph(
        "Visible black particulate matter observed in three sample containers during incoming QC inspection. "
        "Batch quarantined pending investigation.",
        ParagraphStyle("DescBody", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#2D3748"))
    )
    story.append(desc_p)
    story.append(Spacer(1, 10))

    # Additional Findings & Immediate Containment
    story.append(Paragraph("Incoming Inspection & Containment Log", section_head))
    log_text = Paragraph(
        "Upon receipt of active pharmaceutical ingredient consignment (Lot: MFH260712A), standard analytical sampling "
        "was executed at receiving bay 2. During macroscopic visual inspection in the laminar air flow booth, discrete "
        "dark foreign particulates (100–300 µm) were detected suspended within three unopened primary packaging sample jars. "
        "Immediate quarantine tag #Q-2026-881 applied to all 25 fiber drums (500 kg total lot weight). "
        "Vendor CAPA initiated. Retain samples sealed under chain of custody.",
        ParagraphStyle("LogBody", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#4A5568"))
    )
    story.append(log_text)
    story.append(Spacer(1, 20))

    # Signatures Table
    sig_data = [
        [
            Paragraph("<b>Reported By:</b><br/>Dr. S. K. Nambiar<br/>Head - Incoming QC & Vendor QA", cell_val),
            Paragraph("<b>Approved By:</b><br/>Dr. Aruna Varma, Ph.D.<br/>VP - Quality Management & Regulatory Compliance", cell_val),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[265, 265])
    sig_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sig_table)

    doc.build(story)
    print(f"Generated: {pdf_path}")


def build_tablet_variant_pdf():
    pdf_path = OUTPUT_DIR / "complaint_pdf_tablet_variant.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#718096"),
    )
    section_head = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#3182CE"),
        spaceBefore=10,
        spaceAfter=6,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#2D3748"),
    )
    cell_val = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # Letterhead
    story.append(Paragraph("MetroHealth Multi-Speciality Hospital & Research Centre", title_style))
    story.append(Paragraph("Department of Pharmacy Services & Patient Safety Committee", subtitle_style))
    story.append(Paragraph("Plot 12/B, Healthcare City, Bannerghatta Road, Bengaluru - 560076 | JCI & NABH Accredited", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3182CE"), spaceAfter=14))

    # Badge
    story.append(Paragraph("FINISHED DOSAGE FORM (FDF) PRODUCT DEFECT ALERT", ParagraphStyle(
        "AlertBadge",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#DD6B20"),
        alignment=1,
        spaceAfter=12,
    )))

    # Metadata Grid
    table_data = [
        [
            Paragraph("Reporting Entity:", cell_bold),
            Paragraph("MetroHealth Multi-Speciality Hospital", cell_val),
            Paragraph("Complaint Date:", cell_bold),
            Paragraph("2026-09-11", cell_val),
        ],
        [
            Paragraph("Product Name:", cell_bold),
            Paragraph("Ciprofloxacin Tablets 500mg", cell_val),
            Paragraph("Complaint Type:", cell_bold),
            Paragraph("Tablet Friability and Capping Defect", cell_val),
        ],
        [
            Paragraph("Product Strength/Grade:", cell_bold),
            Paragraph("USP 500mg (Film-Coated)", cell_val),
            Paragraph("Batch/Lot Number:", cell_bold),
            Paragraph("CIP260814C", cell_val),
        ],
        [
            Paragraph("Manufacturing Date:", cell_bold),
            Paragraph("2026-08-14", cell_val),
            Paragraph("Expiry Date:", cell_bold),
            Paragraph("2029-08-13", cell_val),
        ],
        [
            Paragraph("Quantity Affected:", cell_bold),
            Paragraph("250.0", cell_val),
            Paragraph("Quantity Unit:", cell_bold),
            Paragraph("blister strips (2500 tablets)", cell_val),
        ],
    ]

    t = Table(table_data, colWidths=[130, 160, 110, 130])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Defect Narrative
    story.append(Paragraph("Clinical Occurrence & Quality Failure Description", section_head))
    story.append(Paragraph(
        "During inpatient drug administration in the Intensive Coronary Care Unit (ICCU) and General Medical Ward, "
        "clinical nurses observed widespread physical disintegration of tablets upon expelling from blister packaging. "
        "Over 250 blister strips (2,500 tablets total) across carton boxes from lot CIP260814C exhibited severe tablet capping, "
        "lamination, and excessive friability with crumbling of the core beneath the thin film coating. "
        "In-house hospital pharmacy laboratory friability re-check showed weight loss of 2.8% (USP tolerance < 1.0%). "
        "All dispensing has been halted immediately and the entire batch has been placed under quarantine.",
        ParagraphStyle("DescBody", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=colors.HexColor("#2D3748"))
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Action Requested from Manufacturer", section_head))
    story.append(Paragraph(
        "1. Immediate replacement consignment of compliant Ciprofloxacin 500mg tablets to prevent therapy disruption.<br/>"
        "2. Technical root cause report on compression pressure and binder ratio for batch CIP260814C.<br/>"
        "3. Nationwide hospital advisory / recall notification if friability failure extends across the commercial batch.",
        ParagraphStyle("ActionBody", parent=styles["Normal"], fontSize=9, leading=13.5, textColor=colors.HexColor("#4A5568"))
    ))
    story.append(Spacer(1, 20))

    # Signatures
    sig_data = [
        [
            Paragraph("<b>Reported By:</b><br/>Dr. Preeti Shenoy, Pharm.D<br/>Director of Pharmacy & Formulary Safety", cell_val),
            Paragraph("<b>Acknowledged By:</b><br/>Dr. Arvind Menon, MD<br/>Chairman - Patient Safety & Pharmacovigilance", cell_val),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[265, 265])
    sig_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sig_table)

    doc.build(story)
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    build_metformin_pdf()
    build_tablet_variant_pdf()
