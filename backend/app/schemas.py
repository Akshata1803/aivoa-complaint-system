"""
Pydantic Schemas for API Request and Response serialization.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TextComplaintRequest(BaseModel):
    """Request payload for text-based complaint intake and follow-up edits."""
    text: str = Field(..., description="Free-text complaint narrative or correction")
    complaint_id: Optional[int] = Field(
        default=None,
        description="Optional ID of existing complaint to edit. If null, a new complaint is created."
    )


class ComplaintResponse(BaseModel):
    """Full serialized Complaint database record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[float] = None
    quantity_unit: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None
    risk_classification: Optional[str] = None
    recommended_action: Optional[str] = None
    ai_reasoning_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
