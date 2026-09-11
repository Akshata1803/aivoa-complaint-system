"""
Smoke-test for the Groq LLM connection.
Run from the backend directory:
    uv run python test_groq.py
"""

import sys
import io

# Ensure UTF-8 output even on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, ".")

from app.llm import (
    get_llm,
    get_resilient_llm,
    PRIMARY_MODEL,
    FALLBACK_MODEL,
)


def test_model(model_name: str) -> bool:
    print(f"\n{'='*60}")
    print(f"  Testing model: {model_name}")
    print(f"{'='*60}")

    try:
        llm = get_llm(model=model_name, temperature=0, max_tokens=256)
        response = llm.invoke(
            f"Say hello and state your model name: {model_name}. Keep it to 1 sentence."
        )
        print("  Status: SUCCESS")
        print(f"  Response: {response.content.strip()}")
        tokens = response.response_metadata.get("token_usage", {})
        if tokens:
            print(f"  Total tokens: {tokens.get('total_tokens')}")
        return True
    except Exception as e:
        print("  Status: FAILED")
        print(f"  Details: {e}")
        return False


def test_resilient_chain() -> bool:
    print(f"\n{'='*60}")
    print(f"  Testing Resilient Chain (Primary -> Fallback)")
    print(f"{'='*60}")

    try:
        resilient_llm = get_resilient_llm(temperature=0, max_tokens=256)
        response = resilient_llm.invoke("Say hello in one short sentence.")
        print("  Status: SUCCESS (Fallback engaged seamlessly)")
        print(f"  Response: {response.content.strip()}")
        return True
    except Exception as e:
        print("  Status: FAILED")
        print(f"  Details: {e}")
        return False


if __name__ == "__main__":
    print("\n  AIVOA — Groq LLM Connection Test")
    print("  " + "-" * 36)

    primary_ok = test_model(PRIMARY_MODEL)
    fallback_ok = test_model(FALLBACK_MODEL)
    resilient_ok = test_resilient_chain()

    print(f"\n{'='*60}")
    print("  Summary:")
    print(f"    Primary  ({PRIMARY_MODEL}):  {'PASS' if primary_ok else 'UNAVAILABLE (404/Decommissioned)'}")
    print(f"    Fallback ({FALLBACK_MODEL}): {'PASS' if fallback_ok else 'FAIL'}")
    print(f"    Resilient Chain (Auto-Fallback): {'PASS' if resilient_ok else 'FAIL'}")
    print(f"{'='*60}\n")

    if not fallback_ok and not primary_ok:
        sys.exit(1)
