"""
Integration Test Suite for AIVOA FastAPI Complaints API.
Uses FastAPI TestClient to test:
1. POST /complaints/from-text (New intake)
2. POST /complaints/from-text (Edit existing via complaint_id)
3. POST /complaints/from-document (PDF upload intake)
4. GET /complaints/{id} and GET /complaints (List & retrieve)

Run:
    uv run python test_api.py
"""

import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

APOLLO_TEXT = "Apollo Pharmacy reported discolored capsules in Amoxicillin capsules 500mg"
CORRECTION_TEXT = "sorry, the batch number is BMX24602 and the affected quantity is 48 capsules"
PDF_SAMPLE_PATH = Path("sample_data/complaint_pdf_metformin.pdf")


def main():
    print("\n" + "=" * 80)
    print("  AIVOA FastAPI Complaints API — Integration Test Suite")
    print("=" * 80)

    # -----------------------------------------------------------------------
    # TEST 1: POST /complaints/from-text (New Complaint)
    # -----------------------------------------------------------------------
    print("\n[TEST 1] Calling POST /complaints/from-text (New Intake)...")
    resp1 = client.post("/complaints/from-text", json={"text": APOLLO_TEXT})
    print(f"  HTTP Status Code: {resp1.status_code}")
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}: {resp1.text}"
    
    data1 = resp1.json()
    complaint_id = data1.get("id")
    print(f"  Created Complaint ID: {complaint_id}")
    print(f"  Customer Name: {data1.get('customer_name')}")
    print(f"  Product Name: {data1.get('product_name')}")
    print(f"  Strength/Grade: {data1.get('product_strength_grade')}")
    print(f"  Complaint Type: {data1.get('complaint_type')}")
    print(f"  Batch Number (should be null): {data1.get('batch_lot_number')}")
    print(f"  Quantity Affected (should be null): {data1.get('quantity_affected')}")

    assert complaint_id is not None and complaint_id > 0
    assert data1.get("customer_name") == "Apollo Pharmacy"
    assert "Amoxicillin" in str(data1.get("product_name"))
    assert data1.get("product_strength_grade") == "500mg"
    assert data1.get("complaint_type") == "Discoloration"
    assert data1.get("batch_lot_number") is None
    assert data1.get("quantity_affected") is None
    print("✓ TEST 1 PASSED: New text complaint successfully created and saved in PostgreSQL.")

    # -----------------------------------------------------------------------
    # TEST 2: POST /complaints/from-text (Edit with complaint_id)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"[TEST 2] Calling POST /complaints/from-text (Editing Complaint #{complaint_id})...")
    resp2 = client.post(
        "/complaints/from-text",
        json={"text": CORRECTION_TEXT, "complaint_id": complaint_id},
    )
    print(f"  HTTP Status Code: {resp2.status_code}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text}"

    data2 = resp2.json()
    print(f"  Updated Complaint ID: {data2.get('id')}")
    print(f"  Batch Number (updated): {data2.get('batch_lot_number')}")
    print(f"  Quantity Affected (updated): {data2.get('quantity_affected')} {data2.get('quantity_unit')}")
    print(f"  Customer Name (preserved): {data2.get('customer_name')}")
    print(f"  Product Name (preserved): {data2.get('product_name')}")
    print(f"  Complaint Type (preserved): {data2.get('complaint_type')}")

    assert data2.get("id") == complaint_id
    assert data2.get("batch_lot_number") == "BMX24602"
    assert data2.get("quantity_affected") in [48, 48.0]
    assert data2.get("quantity_unit") == "capsules"
    # Verify untouched fields are 100% preserved
    assert data2.get("customer_name") == data1.get("customer_name")
    assert data2.get("product_name") == data1.get("product_name")
    assert data2.get("product_strength_grade") == data1.get("product_strength_grade")
    assert data2.get("complaint_type") == data1.get("complaint_type")
    assert data2.get("complaint_date") == data1.get("complaint_date")
    print("✓ TEST 2 PASSED: Complaint updated with surgical accuracy; untouched fields preserved.")

    # -----------------------------------------------------------------------
    # TEST 3: POST /complaints/from-document (PDF Upload)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"[TEST 3] Calling POST /complaints/from-document ({PDF_SAMPLE_PATH})...")
    assert PDF_SAMPLE_PATH.exists(), f"Sample PDF not found: {PDF_SAMPLE_PATH}"

    with open(PDF_SAMPLE_PATH, "rb") as pdf_file:
        resp3 = client.post(
            "/complaints/from-document",
            files={"file": ("complaint_pdf_metformin.pdf", pdf_file, "application/pdf")},
        )

    print(f"  HTTP Status Code: {resp3.status_code}")
    assert resp3.status_code == 201, f"Expected 201, got {resp3.status_code}: {resp3.text}"

    data3 = resp3.json()
    doc_complaint_id = data3.get("id")
    print(f"  Created Document Complaint ID: {doc_complaint_id}")
    print(f"  Customer Name: {data3.get('customer_name')}")
    print(f"  Product Name: {data3.get('product_name')}")
    print(f"  Strength/Grade: {data3.get('product_strength_grade')}")
    print(f"  Batch/Lot Number: {data3.get('batch_lot_number')}")
    print(f"  Manufacturing Date: {data3.get('manufacturing_date')}")
    print(f"  Expiry Date: {data3.get('expiry_date')}")
    print(f"  Complaint Type: {data3.get('complaint_type')}")
    print(f"  Initial Severity: {data3.get('initial_severity')}")
    print(f"  Priority: {data3.get('priority')}")
    print(f"  Risk Classification: {data3.get('risk_classification')}")

    assert doc_complaint_id is not None and doc_complaint_id > 0
    assert data3.get("customer_name") == "MedCore Pharmaceuticals Pvt. Ltd."
    assert data3.get("product_name") == "Metformin Hydrochloride API"
    assert data3.get("product_strength_grade") == "IP/BP"
    assert data3.get("batch_lot_number") == "MFH260712A"
    assert str(data3.get("manufacturing_date")) == "2026-07-12"
    assert str(data3.get("expiry_date")) == "2028-07-11"
    assert data3.get("complaint_type") == "Particulate Contamination"
    assert data3.get("initial_severity") in ["Major", "Critical"]
    print("✓ TEST 3 PASSED: Document PDF parsed, extracted, triaged, and saved to DB.")

    # -----------------------------------------------------------------------
    # TEST 4: GET /complaints/{id} and GET /complaints
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"[TEST 4.1] Calling GET /complaints/{complaint_id}...")
    get_single = client.get(f"/complaints/{complaint_id}")
    print(f"  HTTP Status Code: {get_single.status_code}")
    assert get_single.status_code == 200
    assert get_single.json().get("id") == complaint_id
    assert get_single.json().get("batch_lot_number") == "BMX24602"
    print(f"✓ GET /complaints/{complaint_id} verified.")

    print(f"\n[TEST 4.2] Calling GET /complaints/{doc_complaint_id}...")
    get_doc = client.get(f"/complaints/{doc_complaint_id}")
    assert get_doc.status_code == 200
    assert get_doc.json().get("id") == doc_complaint_id
    print(f"✓ GET /complaints/{doc_complaint_id} verified.")

    print(f"\n[TEST 4.3] Calling GET /complaints (list all)...")
    get_all = client.get("/complaints")
    print(f"  HTTP Status Code: {get_all.status_code}")
    assert get_all.status_code == 200
    all_complaints = get_all.json()
    print(f"  Total Complaints Retrieved: {len(all_complaints)}")
    assert len(all_complaints) >= 2

    # Verify descending ordering by created_at
    ids_in_order = [c["id"] for c in all_complaints]
    print(f"  Top Complaint IDs: {ids_in_order[:5]}")
    # Document complaint was created after text complaint, so it should appear first
    assert ids_in_order[0] == doc_complaint_id
    print("✓ GET /complaints list and descending order verified.")

    # Test 404 for non-existent ID
    print(f"\n[TEST 4.4] Calling GET /complaints/999999 (Non-existent ID check)...")
    get_404 = client.get("/complaints/999999")
    print(f"  HTTP Status Code: {get_404.status_code}")
    assert get_404.status_code == 404
    print("✓ 404 Not Found handling verified.")

    print("\n" + "=" * 80)
    print("  ALL API INTEGRATION TESTS PASSED (100% SUCCESS)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
