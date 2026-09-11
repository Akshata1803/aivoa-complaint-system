from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Numeric,
    func,
)
from app.database import Base


class Complaint(Base):
    """
    SQLAlchemy model representing a Pharmaceutical QA Customer Complaint.
    Supports both Active Pharmaceutical Ingredients (API) and Finished Dosage Forms (FDF).
    """
    __tablename__ = "complaints"

    # Primary Identifier
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Complaint Origin & Customer
    complaint_source = Column(String(100), nullable=True, comment="Source of complaint: Hospital, Pharmacy, Distributor, Patient, Regulatory")
    customer_name = Column(String(255), nullable=True, comment="Customer or institution reporting the issue")

    # Pharmaceutical Product & Batch Details
    product_name = Column(String(255), nullable=True, index=True, comment="Trade or generic pharmaceutical product name")
    product_strength_grade = Column(String(100), nullable=True, comment="Dosage strength (e.g. 500mg) or chemical grade (e.g. USP/Ph. Eur)")
    batch_lot_number = Column(String(100), nullable=True, index=True, comment="Batch / Lot manufacturing identification number")
    manufacturing_date = Column(Date, nullable=True, comment="Batch manufacturing date")
    expiry_date = Column(Date, nullable=True, comment="Batch expiration or re-test date")

    # Affected Quantities
    quantity_affected = Column(Numeric(12, 2), nullable=True, comment="Quantity of units or mass affected")
    quantity_unit = Column(String(50), nullable=True, comment="Unit of measure (e.g., vials, tablets, kg, bottles)")

    # Complaint Details & Classification
    complaint_type = Column(String(100), nullable=True, index=True, comment="Categorization: Contamination, Packaging, Potency, Labeling, Dissolution, etc.")
    complaint_date = Column(Date, nullable=True, default=date.today, comment="Date the complaint was officially lodged")
    detailed_description = Column(Text, nullable=True, comment="Detailed narrative describing the observed issue or defect")

    # QA Triage & AI Evaluation Fields
    initial_severity = Column(String(50), nullable=True, comment="QA Initial Severity: Critical, Major, Minor")
    priority = Column(String(50), nullable=True, comment="Investigation priority: High, Medium, Low")
    risk_classification = Column(String(50), nullable=True, comment="Regulatory Risk: Class I (Life-threatening), Class II (Temporary), Class III (Minor)")
    recommended_action = Column(Text, nullable=True, comment="Recommended QA action (CAPA, Quarantine, Stability, Recall)")
    ai_reasoning_notes = Column(Text, nullable=True, comment="AI agent root cause hypothesis and QA triage rationale")

    # Audit Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when record was last updated"
    )

    def __repr__(self) -> str:
        return (
            f"<Complaint(id={self.id}, product='{self.product_name}', "
            f"batch='{self.batch_lot_number}', severity='{self.initial_severity}')>"
        )
