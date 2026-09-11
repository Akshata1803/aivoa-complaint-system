"""
Test script for AIVOA LangGraph Complaint Extraction, Editing & Document Intake Agent.

Tests:
1. Text-based extraction from raw chat narrative (Apollo Pharmacy).
2. Surgical natural language edit via edit_complaint ("batch number BMX24602, 48 capsules").
3. Document-based extraction from raw parsed PDF text (MedCore Pharmaceuticals).
4. Strict schema verification and field accuracy assertions.

Run:
    uv run python test_agent.py
"""

import sys
import json

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, ".")

from app.agent import process_complaint, process_complaint_text


INITIAL_COMPLAINT_TEXT = (
    "Apollo Pharmacy reported discolored capsules in Amoxicillin capsules 500mg"
)

CORRECTION_TEXT = (
    "sorry, the batch number is BMX24602 and the affected quantity is 48 capsules"
)

DOCUMENT_SAMPLE_TEXT = """CUSTOMER COMPLAINT REPORT
Reporting Company: MedCore Pharmaceuticals Pvt. Ltd.
Product Name: Metformin Hydrochloride API
Product Strength/Grade: IP/BP
Batch/Lot Number: MFH260712A
Manufacturing Date: 2026-07-12
Expiry Date: 2028-07-11
Complaint Type: Particulate Contamination
Complaint Date: 2026-09-10
Description: Visible black particulate matter observed in three sample containers during incoming QC inspection. Batch quarantined pending investigation."""


def test_text_and_edit():
    print("\n" + "=" * 75)
    print("  TEST SUITE 1: TEXT EXTRACTION & EDIT ROUTING")
    print("=" * 75)

    # Step 1: Base text extraction
    print(f"\n--- 1.1: EXTRACT BASE COMPLAINT (source='text') ---")
    print(f"Input: \"{INITIAL_COMPLAINT_TEXT}\"\n")
    base_complaint = process_complaint(INITIAL_COMPLAINT_TEXT, source="text")
    print("[Base Extraction Result]:")
    print(json.dumps(base_complaint, indent=2, ensure_ascii=False))

    assert base_complaint.get("customer_name") == "Apollo Pharmacy"
    assert "Amoxicillin" in str(base_complaint.get("product_name"))
    assert base_complaint.get("batch_lot_number") is None

    # Step 2: Edit complaint
    print(f"\n--- 1.2: EDIT COMPLAINT WITH CORRECTION (source='edit') ---")
    print(f"Correction: \"{CORRECTION_TEXT}\"\n")
    updated_complaint = process_complaint(
        CORRECTION_TEXT,
        source="edit",
        current_complaint=base_complaint,
    )
    print("[Updated Complaint Result]:")
    print(json.dumps(updated_complaint, indent=2, ensure_ascii=False))

    assert updated_complaint.get("batch_lot_number") == "BMX24602"
    assert updated_complaint.get("quantity_affected") in [48, 48.0]
    assert updated_complaint.get("customer_name") == "Apollo Pharmacy"
    print("\n✓ Text & Edit tests passed.")


def test_document_extraction():
    print("\n" + "=" * 75)
    print("  TEST SUITE 2: DOCUMENT EXTRACTION (node: 'extract_from_document')")
    print("=" * 75)
    print("\n[INPUT PARSED DOCUMENT TEXT]:\n")
    print(DOCUMENT_SAMPLE_TEXT)
    print("\n" + "-" * 75)

    print("[Agent Routing] Invoking LangGraph agent with source='document'...")
    doc_result = process_complaint(DOCUMENT_SAMPLE_TEXT, source="document")

    print("\n[DOCUMENT EXTRACTION & TRIAGE RESULT]:")
    print("-" * 75)
    print(json.dumps(doc_result, indent=2, ensure_ascii=False))
    print("-" * 75)

    print("\n[VERIFICATION CHECKS — DOCUMENT EXTRACTION ACCURACY]:")
    checks = [
        (
            "Customer Name",
            doc_result.get("customer_name") == "MedCore Pharmaceuticals Pvt. Ltd.",
            f"Expected 'MedCore Pharmaceuticals Pvt. Ltd.', got '{doc_result.get('customer_name')}'"
        ),
        (
            "Product Name",
            doc_result.get("product_name") == "Metformin Hydrochloride API",
            f"Expected 'Metformin Hydrochloride API', got '{doc_result.get('product_name')}'"
        ),
        (
            "Product Strength/Grade",
            doc_result.get("product_strength_grade") == "IP/BP",
            f"Expected 'IP/BP', got '{doc_result.get('product_strength_grade')}'"
        ),
        (
            "Batch/Lot Number",
            doc_result.get("batch_lot_number") == "MFH260712A",
            f"Expected 'MFH260712A', got '{doc_result.get('batch_lot_number')}'"
        ),
        (
            "Manufacturing Date",
            doc_result.get("manufacturing_date") == "2026-07-12",
            f"Expected '2026-07-12', got '{doc_result.get('manufacturing_date')}'"
        ),
        (
            "Expiry Date",
            doc_result.get("expiry_date") == "2028-07-11",
            f"Expected '2028-07-11', got '{doc_result.get('expiry_date')}'"
        ),
        (
            "Complaint Type",
            doc_result.get("complaint_type") == "Particulate Contamination",
            f"Expected 'Particulate Contamination', got '{doc_result.get('complaint_type')}'"
        ),
        (
            "Complaint Date",
            doc_result.get("complaint_date") == "2026-09-10",
            f"Expected '2026-09-10', got '{doc_result.get('complaint_date')}'"
        ),
        (
            "Detailed Description captured",
            "particulate matter" in str(doc_result.get("detailed_description")).lower(),
            f"Got: '{doc_result.get('detailed_description')}'"
        ),
        (
            "Initial Severity assigned",
            doc_result.get("initial_severity") in ["Minor", "Major", "Critical"],
            f"Got: {doc_result.get('initial_severity')}"
        ),
        (
            "Priority assigned",
            doc_result.get("priority") in ["Low", "Medium", "High", "Urgent"],
            f"Got: {doc_result.get('priority')}"
        ),
        (
            "Risk Classification assigned",
            doc_result.get("risk_classification") in ["Class I", "Class II", "Class III"],
            f"Got: {doc_result.get('risk_classification')}"
        ),
        (
            "Recommended Action provided",
            bool(doc_result.get("recommended_action")),
            "Missing"
        ),
        (
            "AI Reasoning Notes provided",
            bool(doc_result.get("ai_reasoning_notes")),
            "Missing"
        ),
    ]

    all_passed = True
    for name, passed, err in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
            print(f"  [{status}] {name} — {err}")
        else:
            print(f"  [{status}] {name}")

    print("\n" + "=" * 75)
    if all_passed:
        print("  DOCUMENT EXTRACTION: ALL CHECKS PASSED (EXACT MATCH ON ALL SCHEMA FIELDS)")
    else:
        print("  DOCUMENT EXTRACTION: SOME CHECKS FAILED")
    print("=" * 75 + "\n")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    test_text_and_edit()
    test_document_extraction()
