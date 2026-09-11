"""
Complaints API Router.

Endpoints:
- POST /complaints/from-text       (Intake new complaint or edit existing via text)
- POST /complaints/from-document   (Intake complaint from uploaded PDF / EML)
- GET  /complaints/{id}            (Get single complaint by ID)
- GET  /complaints                 (List all complaints, most recent first)
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complaint import Complaint
from app.schemas import TextComplaintRequest, ComplaintResponse
from app.agent import process_complaint
from app.document_parser import extract_text_from_file

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _parse_date(val: Optional[str]) -> Optional[date]:
    """Safely parse an ISO date string to a Python date object."""
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val).strip())
    except Exception:
        return None


def _parse_float(val) -> Optional[float]:
    """Safely cast numeric value to float."""
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None


def _complaint_to_dict(complaint: Complaint) -> dict:
    """Convert a Complaint SQLAlchemy model instance to a clean dictionary for agent editing."""
    return {
        "complaint_source": complaint.complaint_source,
        "customer_name": complaint.customer_name,
        "product_name": complaint.product_name,
        "product_strength_grade": complaint.product_strength_grade,
        "batch_lot_number": complaint.batch_lot_number,
        "manufacturing_date": complaint.manufacturing_date.isoformat() if complaint.manufacturing_date else None,
        "expiry_date": complaint.expiry_date.isoformat() if complaint.expiry_date else None,
        "quantity_affected": float(complaint.quantity_affected) if complaint.quantity_affected is not None else None,
        "quantity_unit": complaint.quantity_unit,
        "complaint_type": complaint.complaint_type,
        "complaint_date": complaint.complaint_date.isoformat() if complaint.complaint_date else None,
        "detailed_description": complaint.detailed_description,
        "initial_severity": complaint.initial_severity,
        "priority": complaint.priority,
        "risk_classification": complaint.risk_classification,
        "recommended_action": complaint.recommended_action,
        "ai_reasoning_notes": complaint.ai_reasoning_notes,
    }


def _populate_complaint(complaint: Complaint, data: dict) -> None:
    """Populate or update Complaint model attributes from an agent result dictionary."""
    for key, val in data.items():
        if key in ["manufacturing_date", "expiry_date", "complaint_date"]:
            setattr(complaint, key, _parse_date(val))
        elif key == "quantity_affected":
            setattr(complaint, key, _parse_float(val))
        elif hasattr(complaint, key):
            setattr(complaint, key, val)


@router.post("/from-text", response_model=ComplaintResponse)
async def intake_or_edit_from_text(
    payload: TextComplaintRequest,
    db: Session = Depends(get_db),
):
    """
    Intake a new complaint from natural language text, or edit an existing complaint.
    - If complaint_id is null: extracts new complaint, inserts row in DB, returns full row.
    - If complaint_id is provided: fetches row, merges natural language correction, updates row.
    """
    if payload.complaint_id is not None:
        # Edit existing complaint
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint with ID {payload.complaint_id} not found",
            )

        existing_dict = _complaint_to_dict(complaint)
        merged_result = process_complaint(
            complaint_text=payload.text,
            source="edit",
            current_complaint=existing_dict,
        )

        _populate_complaint(complaint, merged_result)
        db.commit()
        db.refresh(complaint)
        return complaint
    else:
        # Create new complaint
        extracted_result = process_complaint(
            complaint_text=payload.text,
            source="text",
            current_complaint=None,
        )

        new_complaint = Complaint()
        _populate_complaint(new_complaint, extracted_result)
        db.add(new_complaint)
        db.commit()
        db.refresh(new_complaint)
        return new_complaint


@router.post("/from-document", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def intake_from_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Intake a complaint from an uploaded document (PDF or EML).
    Extracts plain text via document_parser, runs document intake agent, and saves to database.
    """
    filename = file.filename or ""
    try:
        extracted_text = extract_text_from_file(file.file, filename=filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document '{filename}': {str(exc)}",
        )

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document '{filename}' appears empty or no readable text could be extracted.",
        )

    extracted_result = process_complaint(
        complaint_text=extracted_text,
        source="document",
        current_complaint=None,
    )

    new_complaint = Complaint()
    _populate_complaint(new_complaint, extracted_result)
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return new_complaint


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    """Fetch a single complaint record by its primary key ID."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found",
        )
    return complaint


@router.get("", response_model=List[ComplaintResponse])
async def list_complaints(
    db: Session = Depends(get_db),
):
    """Retrieve all complaints in descending order of creation (most recent first)."""
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()
