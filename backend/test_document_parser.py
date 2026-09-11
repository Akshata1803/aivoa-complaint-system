"""
Test script for AIVOA Document Parser Utility (app/document_parser.py).

Validates text extraction from:
1. sample_data/complaint_email_amoxicillin.eml
2. sample_data/complaint_pdf_metformin.pdf
3. sample_data/complaint_pdf_tablet_variant.pdf

Run:
    uv run python test_document_parser.py
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, ".")

from app.document_parser import extract_text_from_file

SAMPLE_DIR = Path("sample_data")

FILES_TO_TEST = [
    ("complaint_email_amoxicillin.eml", [
        "Apollo Pharmacy",
        "Amoxicillin",
        "500mg",
        "BMX24602",
        "48 capsules",
    ]),
    ("complaint_pdf_metformin.pdf", [
        "MedCore Pharmaceuticals",
        "Metformin Hydrochloride API",
        "IP/BP",
        "MFH260712A",
        "Particulate Contamination",
    ]),
    ("complaint_pdf_tablet_variant.pdf", [
        "MetroHealth",
        "Ciprofloxacin Tablets 500mg",
        "CIP260814C",
        "Friability",
        "250",
    ]),
]


def main():
    print("\n" + "=" * 75)
    print("  AIVOA Document Parser Utility — Verification Test Suite")
    print("=" * 75)

    all_passed = True

    for filename, expected_substrings in FILES_TO_TEST:
        file_path = SAMPLE_DIR / filename
        print(f"\n" + "-" * 75)
        print(f"  FILE: {filename}")
        print(f"  PATH: {file_path}")
        print("-" * 75)

        if not file_path.exists():
            print(f"  [ERROR] File not found: {file_path}")
            all_passed = False
            continue

        try:
            extracted_text = extract_text_from_file(file_path)
            print("\n[EXTRACTED RAW TEXT]:\n")
            print(extracted_text)
            print("\n[CONTENT VERIFICATION]:")

            file_passed = True
            for substr in expected_substrings:
                found = substr.lower() in extracted_text.lower()
                status = "PASS" if found else "FAIL"
                if not found:
                    file_passed = False
                    all_passed = False
                print(f"  [{status}] Contains '{substr}'")

            if file_passed:
                print(f"\n✓ {filename} extracted and verified successfully!")
            else:
                print(f"\n✗ {filename} failed content checks.")

        except Exception as e:
            print(f"  [EXCEPTION] Failed to parse {filename}: {e}")
            all_passed = False

    print("\n" + "=" * 75)
    if all_passed:
        print("  ALL SAMPLE DOCUMENTS EXTRACTED CLEANLY & VERIFIED")
    else:
        print("  SOME DOCUMENT EXTRACTIONS FAILED")
    print("=" * 75 + "\n")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
