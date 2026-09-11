"""
AIVOA LangGraph Complaint Extraction & QA Triage Agent.

This module implements:
1. Pydantic models for structured intake extraction, QA triage, and corrections.
2. Tools:
   - 'extract_new_complaint': Two-step extraction & QA reasoning from raw text.
   - 'extract_from_document': Two-step extraction & QA reasoning from parsed document text.
   - 'edit_complaint': Surgical field corrections merged into existing complaints,
     with conditional re-triage if risk-affecting fields are modified.
3. A LangGraph StateGraph routing via an explicit source flag ('text', 'document', 'edit').
"""

from datetime import date
from typing import Optional, Literal, TypedDict, Any, Dict, Set
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END

from app.llm import get_primary_llm, get_fallback_llm


# ---------------------------------------------------------------------------
# 1. Pydantic Models for Structured Output
# ---------------------------------------------------------------------------

class ComplaintExtractedFields(BaseModel):
    """Step 1: Raw factual fields extracted strictly from complaint narrative or document."""
    complaint_source: Optional[str] = Field(
        default=None,
        description="Source or entity type reporting the complaint based on context clues: 'Pharmacy' (retail/dispensary), 'Hospital' (hospital/clinic/ward), 'Internal QC' or 'Incoming QC' (discovered during in-house or incoming quality control inspection), 'Distributor', 'Patient', 'Regulatory', or null. Do not default to generic 'Customer'."
    )
    customer_name: Optional[str] = Field(
        default=None,
        description="Name of the reporting company, pharmacy, hospital, customer, or institution (e.g., 'MedCore Pharmaceuticals Pvt. Ltd.')"
    )
    product_name: Optional[str] = Field(
        default=None,
        description="Trade or generic pharmaceutical product name (e.g., 'Metformin Hydrochloride API')"
    )
    product_strength_grade: Optional[str] = Field(
        default=None,
        description="Dosage strength (e.g., '500mg') or pharmacopoeial grade (e.g., 'IP/BP', 'USP'), or null"
    )
    batch_lot_number: Optional[str] = Field(
        default=None,
        description="Batch or lot number if explicitly mentioned, otherwise null"
    )
    manufacturing_date: Optional[str] = Field(
        default=None,
        description="Manufacturing date in YYYY-MM-DD format if explicitly stated, otherwise null"
    )
    expiry_date: Optional[str] = Field(
        default=None,
        description="Expiry date in YYYY-MM-DD format if explicitly stated, otherwise null"
    )
    quantity_affected: Optional[float] = Field(
        default=None,
        description="Numeric quantity affected if explicitly mentioned, otherwise null"
    )
    quantity_unit: Optional[str] = Field(
        default=None,
        description="Unit of affected quantity (e.g., capsules, vials, bottles, containers, packs, kg), or null"
    )
    complaint_type: Optional[str] = Field(
        default=None,
        description="Classification of defect (e.g., Particulate Contamination, Discoloration, Packaging Defect, Sub-potency, Foreign Matter, Labeling Error)"
    )
    complaint_date: Optional[str] = Field(
        default=None,
        description="Date the complaint was reported in YYYY-MM-DD format, or today's date if implied, or null"
    )
    detailed_description: Optional[str] = Field(
        default=None,
        description="Comprehensive summary description of the reported complaint event"
    )


class ComplaintTriageFields(BaseModel):
    """Step 2: Pharmaceutical QA compliance evaluation and triage reasoning."""
    initial_severity: Literal["Minor", "Major", "Critical"] = Field(
        description="QA Initial Severity: Critical (life-threatening/contamination/safety risk), Major (potency/stability/quality failure), Minor (cosmetic/minor packaging)"
    )
    priority: Literal["Low", "Medium", "High", "Urgent"] = Field(
        description="Investigation priority: Urgent (immediate containment), High (rapid review 48h), Medium (standard QA), Low (trend tracking)"
    )
    risk_classification: Literal["Class I", "Class II", "Class III"] = Field(
        description="Regulatory Risk Class: Class I (Serious adverse health/death probability), Class II (Temporary/reversible health effects), Class III (Unlikely to cause adverse health consequences)"
    )
    recommended_action: str = Field(
        description="Concrete QA action plan: e.g., quarantine retain samples, request sample/photos, BMR review, CAPA, initiate recall evaluation"
    )
    ai_reasoning_notes: str = Field(
        description="Detailed QA root cause hypothesis, clinical hazard rationale, and regulatory triage justification"
    )


class ComplaintFieldUpdates(BaseModel):
    """Surgical updates extracted from user correction text."""
    complaint_source: Optional[str] = Field(default=None, description="New complaint source if explicitly corrected, else null")
    customer_name: Optional[str] = Field(default=None, description="New customer name if explicitly corrected, else null")
    product_name: Optional[str] = Field(default=None, description="New product name if explicitly corrected, else null")
    product_strength_grade: Optional[str] = Field(default=None, description="New strength/grade if explicitly corrected, else null")
    batch_lot_number: Optional[str] = Field(default=None, description="New batch or lot number if explicitly provided, else null")
    manufacturing_date: Optional[str] = Field(default=None, description="New manufacturing date (YYYY-MM-DD) if explicitly provided, else null")
    expiry_date: Optional[str] = Field(default=None, description="New expiry date (YYYY-MM-DD) if explicitly provided, else null")
    quantity_affected: Optional[float] = Field(default=None, description="New numeric quantity affected if explicitly corrected, else null")
    quantity_unit: Optional[str] = Field(default=None, description="New quantity unit (e.g. capsules, bottles, vials) if explicitly corrected, else null")
    complaint_type: Optional[str] = Field(default=None, description="New complaint type if explicitly corrected, else null")
    complaint_date: Optional[str] = Field(default=None, description="New complaint date (YYYY-MM-DD) if explicitly corrected, else null")
    detailed_description: Optional[str] = Field(default=None, description="New/supplemental detailed description if explicitly corrected, else null")


class ComplaintExtractionResult(BaseModel):
    """Unified validated schema matching all content fields of the database Complaint model."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[float] = None
    quantity_unit: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None
    risk_classification: Optional[str] = None
    recommended_action: Optional[str] = None
    ai_reasoning_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# 2. Resilient Structured Output Chains & Prompts
# ---------------------------------------------------------------------------

def _get_resilient_structured_chain(pydantic_class):
    """Build a resilient structured output chain (primary model with fallback)."""
    primary_chain = get_primary_llm(temperature=0).with_structured_output(pydantic_class)
    fallback_chain = get_fallback_llm(temperature=0).with_structured_output(pydantic_class)
    return primary_chain.with_fallbacks([fallback_chain])


STEP1_PROMPT = """You are an expert Pharmaceutical Quality Assurance (QA) data intake specialist.
Analyze the following free-text complaint description and extract all factual details.

CRITICAL INSTRUCTIONS:
- ONLY extract information explicitly stated or directly inferred from the text.
- complaint_source: Classify the reporting entity type based on context clues. Do NOT default to a generic 'Customer'.
  * If reported by a pharmacy or dispensary (e.g., "Apollo Pharmacy reported..."), set complaint_source="Pharmacy".
  * If reported by a hospital, ward, or clinical staff, set complaint_source="Hospital".
  * If discovered during incoming or in-house quality control testing, set complaint_source="Internal QC".
  * If reported by a wholesale distributor, set complaint_source="Distributor".
  * If reported by an individual end-user or patient, set complaint_source="Patient".
- If a reporting entity name is identified (e.g., "Apollo Pharmacy reported..."), set customer_name="Apollo Pharmacy".
- complaint_type: Categorize the type of defect described (e.g., 'Discoloration', 'Packaging Defect', 'Contamination', 'Sub-potent', 'Foreign Matter', 'Labeling Error'). If discolored capsules are mentioned, set complaint_type="Discoloration".
- If a field is NOT mentioned in the text (like batch number, dates, quantity), leave it strictly as null / None.
- DO NOT invent, hallucinate, or fabricate batch numbers, manufacturing/expiry dates, or quantities.
- For detailed_description, summarize the complete problem as reported.
- If complaint_date is not explicitly stated in text, use today's date ({today}).

Complaint Narrative:
{complaint_text}
"""

DOCUMENT_PROMPT = """You are an expert Pharmaceutical Quality Assurance (QA) data intake specialist.
Analyze the following raw text extracted from an official pharmaceutical customer complaint document or report.
Extract all structured fields strictly according to the schema.

CRITICAL INSTRUCTIONS:
- complaint_source: Classify the specific reporting entity/origin type based on context clues in the report. Do NOT default to a generic 'Customer'.
  * If the defect was observed during incoming QC inspection, receiving bay checks, or in-house testing (e.g., "during incoming QC inspection", "Incoming QC & Vendor QA", "receiving bay"), set complaint_source="Incoming QC" (or "Internal QC").
  * If reported by a hospital, medical center, healthcare system, or ward staff (e.g., "MetroHealth Multi-Speciality Hospital", "ward nurses", "Department of Pharmacy Services"), set complaint_source="Hospital".
  * If reported by a retail or community pharmacy/dispensary (e.g., "Apollo Pharmacy"), set complaint_source="Pharmacy".
  * If reported by a supply chain distributor or wholesale depot, set complaint_source="Distributor".
  * If reported by an individual consumer or patient, set complaint_source="Patient".
- "Reporting Company" or reporting entity -> customer_name (e.g. "MedCore Pharmaceuticals Pvt. Ltd.").
- "Product Name" -> product_name (e.g. "Metformin Hydrochloride API").
- "Product Strength/Grade" -> product_strength_grade (e.g. "IP/BP").
- "Batch/Lot Number" -> batch_lot_number (e.g. "MFH260712A").
- "Manufacturing Date" -> manufacturing_date (YYYY-MM-DD format, e.g. "2026-07-12").
- "Expiry Date" -> expiry_date (YYYY-MM-DD format, e.g. "2028-07-11").
- "Complaint Type" -> complaint_type (e.g. "Particulate Contamination").
- "Complaint Date" -> complaint_date (YYYY-MM-DD format, e.g. "2026-09-10").
- "Description" -> detailed_description.
- For quantity: extract quantity_affected and quantity_unit if mentioned (e.g., "three sample containers" -> quantity_affected=3.0, quantity_unit="sample containers"), otherwise null.
- If a field is NOT mentioned in the text, leave it strictly as null / None.
- DO NOT invent or fabricate missing values.

Document Content:
{document_text}
"""

STEP2_PROMPT = """You are a Senior Pharmaceutical Quality Assurance & Regulatory Compliance Manager (cGMP / FDA / WHO compliant).
Evaluate the following extracted complaint details and perform formal QA risk evaluation and classification.

Triage Criteria:
1. initial_severity:
   - 'Critical': Direct threat to patient safety/life (e.g. toxic contamination, foreign matter, microbial growth, mix-up of active drug, particulate contamination in parenteral or sterile APIs).
   - 'Major': Quality, stability, or potency failure not immediately life-threatening (e.g. discoloration, dissolution failure, wrong strength, degraded packaging impacting sterility).
   - 'Minor': Cosmetic packaging/labeling issue not impacting safety, efficacy, or stability.

2. priority:
   - 'Urgent': Immediate containment needed within 24 hours (e.g., particulate contamination, batch quarantine).
   - 'High': Significant issue needing rapid investigation within 48-72 hours.
   - 'Medium': Standard QA investigation (5-10 business days).
   - 'Low': Low risk minor observation.

3. risk_classification:
   - 'Class I': Probability of serious adverse health consequences or death.
   - 'Class II': May cause temporary or medically reversible adverse health consequences, or remote probability of serious adverse consequences.
   - 'Class III': Unlikely to cause adverse health consequences.

4. recommended_action:
   - Provide concrete, immediate QA containment and investigation steps (e.g., quarantine batch, inspect retain samples, review Batch Manufacturing Record (BMR), check filtration records, initiate CAPA).

5. ai_reasoning_notes:
   - Provide a professional clinical and QA rationale explaining the potential root cause (e.g., equipment shedding, filter failure, environmental contamination) and the justification for the assigned severity and risk classification.

Extracted Complaint Details:
{extracted_json}
"""

CORRECTION_PROMPT = """You are an expert Pharmaceutical QA data intake specialist.
A user is providing a correction or follow-up addition to an existing complaint record.
Analyze the user's correction text and extract ONLY the specific fields that are explicitly corrected or newly provided.

CRITICAL RULES:
- Identify ONLY the fields explicitly mentioned in the correction text.
- For all other fields NOT mentioned in the correction text, you MUST set them strictly to null / None.
- Do NOT repeat, rewrite, or assume fields that the user did not explicitly alter.
- For quantities and units: if the user says "the batch number is BMX24602 and the affected quantity is 48 capsules", set:
  batch_lot_number="BMX24602"
  quantity_affected=48.0
  quantity_unit="capsules"
- All unmentioned fields (customer_name, product_name, complaint_type, etc.) MUST be null.

Correction Text:
{correction_text}
"""

# Fields whose modification triggers a re-run of QA risk triage
RISK_AFFECTING_FIELDS: Set[str] = {
    "quantity_affected",
    "quantity_unit",
    "product_name",
    "product_strength_grade",
    "complaint_type",
    "batch_lot_number",
}


# ---------------------------------------------------------------------------
# 3. Tool Implementations
# ---------------------------------------------------------------------------

@tool("extract_new_complaint")
def extract_new_complaint(complaint_text: str) -> Dict[str, Any]:
    """
    Extract structured fields from a free-text pharmaceutical customer complaint
    and perform formal QA severity classification and triage reasoning.

    Args:
        complaint_text: Free-text natural language complaint description.

    Returns:
        A validated dictionary matching the Complaint database schema.
    """
    today_str = date.today().isoformat()

    # Step 1: Structured Factual Extraction
    step1_chain = _get_resilient_structured_chain(ComplaintExtractedFields)
    extracted: ComplaintExtractedFields = step1_chain.invoke(
        STEP1_PROMPT.format(complaint_text=complaint_text, today=today_str)
    )

    # Step 2: QA Triage and Risk Evaluation
    step2_chain = _get_resilient_structured_chain(ComplaintTriageFields)
    triage: ComplaintTriageFields = step2_chain.invoke(
        STEP2_PROMPT.format(extracted_json=extracted.model_dump_json(indent=2))
    )

    # Step 3: Merge and Validate against Unified Pydantic Schema
    merged_data = {
        **extracted.model_dump(),
        **triage.model_dump(),
    }

    validated_result = ComplaintExtractionResult.model_validate(merged_data)
    return validated_result.model_dump()


@tool("extract_from_document")
def extract_from_document(document_text: str) -> Dict[str, Any]:
    """
    Extract structured fields from raw text of an uploaded pharmaceutical complaint document
    (e.g., PDF, DOCX, scan export) and perform formal QA severity classification and triage reasoning.

    Args:
        document_text: Raw text extracted upstream from an uploaded complaint document.

    Returns:
        A validated dictionary matching the Complaint database schema.
    """
    today_str = date.today().isoformat()

    # Step 1: Structured Factual Extraction from Document Text
    step1_chain = _get_resilient_structured_chain(ComplaintExtractedFields)
    extracted: ComplaintExtractedFields = step1_chain.invoke(
        DOCUMENT_PROMPT.format(document_text=document_text, today=today_str)
    )

    # Step 2: QA Triage and Risk Evaluation (same criteria as extract_new_complaint)
    step2_chain = _get_resilient_structured_chain(ComplaintTriageFields)
    triage: ComplaintTriageFields = step2_chain.invoke(
        STEP2_PROMPT.format(extracted_json=extracted.model_dump_json(indent=2))
    )

    # Step 3: Merge and Validate against Unified Pydantic Schema
    merged_data = {
        **extracted.model_dump(),
        **triage.model_dump(),
    }

    validated_result = ComplaintExtractionResult.model_validate(merged_data)
    return validated_result.model_dump()


@tool("edit_complaint")
def edit_complaint(current_complaint: Dict[str, Any], correction_text: str) -> Dict[str, Any]:
    """
    Surgically edit an existing complaint using natural language corrections.
    Merges updates while preserving all unmentioned fields, and conditionally
    refreshes QA risk triage if risk-affecting fields are modified.

    Args:
        current_complaint: The existing complaint dictionary/JSON.
        correction_text: Natural language correction or addition.

    Returns:
        The merged and validated updated complaint dictionary.
    """
    # Step 1: Extract ONLY fields explicitly mentioned in the correction text
    correction_chain = _get_resilient_structured_chain(ComplaintFieldUpdates)
    updates_model: ComplaintFieldUpdates = correction_chain.invoke(
        CORRECTION_PROMPT.format(correction_text=correction_text)
    )

    # Filter out None values to keep only explicit updates
    raw_updates = updates_model.model_dump()
    applied_updates = {k: v for k, v in raw_updates.items() if v is not None}

    # Step 2: Merge updates into existing complaint (untouched fields remain bit-for-bit identical)
    updated_complaint = dict(current_complaint)
    updated_complaint.update(applied_updates)

    # Step 3: Check if any risk-affecting fields were modified
    has_risk_impact = any(k in applied_updates for k in RISK_AFFECTING_FIELDS)

    if has_risk_impact:
        # Re-run QA triage reasoning with the updated complaint details
        triage_payload = {
            k: updated_complaint.get(k)
            for k in ComplaintExtractedFields.model_fields.keys()
        }
        extracted_subset = ComplaintExtractedFields.model_validate(triage_payload)
        step2_chain = _get_resilient_structured_chain(ComplaintTriageFields)
        refreshed_triage: ComplaintTriageFields = step2_chain.invoke(
            STEP2_PROMPT.format(extracted_json=extracted_subset.model_dump_json(indent=2))
        )
        # Update triage fields
        updated_complaint.update(refreshed_triage.model_dump())

    # Step 4: Validate and return final merged dictionary
    validated_result = ComplaintExtractionResult.model_validate(updated_complaint)
    return validated_result.model_dump()


# ---------------------------------------------------------------------------
# 4. LangGraph State & Agent Workflow Construction
# ---------------------------------------------------------------------------

class ComplaintAgentState(TypedDict):
    """State passed through the LangGraph complaint processing workflow."""
    complaint_text: str
    source: Optional[Literal["text", "document", "edit"]]
    current_complaint: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[str]


def extract_node(state: ComplaintAgentState) -> Dict[str, Any]:
    """LangGraph node executing the extract_new_complaint tool."""
    text = state.get("complaint_text", "")
    try:
        data = extract_new_complaint.invoke(text)
        return {"result": data, "error": None}
    except Exception as exc:
        return {"result": None, "error": str(exc)}


def document_node(state: ComplaintAgentState) -> Dict[str, Any]:
    """LangGraph node executing the extract_from_document tool."""
    text = state.get("complaint_text", "")
    try:
        data = extract_from_document.invoke(text)
        return {"result": data, "error": None}
    except Exception as exc:
        return {"result": None, "error": str(exc)}


def edit_node(state: ComplaintAgentState) -> Dict[str, Any]:
    """LangGraph node executing the edit_complaint tool."""
    current = state.get("current_complaint") or {}
    text = state.get("complaint_text", "")
    try:
        data = edit_complaint.invoke({
            "current_complaint": current,
            "correction_text": text,
        })
        return {"result": data, "error": None}
    except Exception as exc:
        return {"result": None, "error": str(exc)}


def route_complaint_action(state: ComplaintAgentState) -> str:
    """
    Conditional router using explicit source flag:
    - "document" -> 'extract_from_document'
    - "edit" -> 'edit_complaint'
    - "text" -> 'extract_new_complaint'

    Fallback when source is not explicitly specified:
    - current_complaint present -> 'edit_complaint'
    - otherwise -> 'extract_new_complaint'
    """
    source = state.get("source")
    if source == "document":
        return "extract_from_document"
    elif source == "edit":
        return "edit_complaint"
    elif source == "text":
        return "extract_new_complaint"

    # Backward-compatible inference:
    if state.get("current_complaint"):
        return "edit_complaint"
    return "extract_new_complaint"


# Build the StateGraph
workflow = StateGraph(ComplaintAgentState)
workflow.add_node("extract_new_complaint", extract_node)
workflow.add_node("extract_from_document", document_node)
workflow.add_node("edit_complaint", edit_node)

# Conditional start routing based on explicit source flag
workflow.add_conditional_edges(
    START,
    route_complaint_action,
    {
        "extract_new_complaint": "extract_new_complaint",
        "extract_from_document": "extract_from_document",
        "edit_complaint": "edit_complaint",
    }
)

workflow.add_edge("extract_new_complaint", END)
workflow.add_edge("extract_from_document", END)
workflow.add_edge("edit_complaint", END)

# Compile the LangGraph agent
complaint_agent = workflow.compile()


# ---------------------------------------------------------------------------
# 5. Public Helper Functions
# ---------------------------------------------------------------------------

def process_complaint(
    complaint_text: str,
    source: Literal["text", "document", "edit"] = "text",
    current_complaint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Unified entry point to invoke the LangGraph complaint agent.

    Args:
        complaint_text: Natural language text, document content, or correction text.
        source: Explicit routing mode: 'text' (default), 'document', or 'edit'.
        current_complaint: Existing complaint JSON/dict (required if source='edit').

    Returns:
        Structured complaint dictionary matching the database schema.
    """
    payload = {
        "complaint_text": complaint_text,
        "source": source,
        "current_complaint": current_complaint,
    }
    final_state = complaint_agent.invoke(payload)
    if final_state.get("error"):
        raise RuntimeError(f"Complaint processing failed: {final_state['error']}")
    return final_state["result"]


def process_complaint_text(
    complaint_text: str,
    current_complaint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Backward-compatible convenience helper for text chat and edits.
    Automatically infers source='edit' if current_complaint is provided.
    """
    source = "edit" if current_complaint else "text"
    return process_complaint(
        complaint_text=complaint_text,
        source=source,
        current_complaint=current_complaint,
    )
