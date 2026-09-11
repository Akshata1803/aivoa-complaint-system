"""
AIVOA Document Parser Utility.

Extracts plain text from pharmaceutical customer complaint documents:
- PDF files (.pdf) using pdfplumber
- Email files (.eml) using Python's standard email module

Ready for direct integration into FastAPI upload endpoints and agent workflows.
"""

import io
import email
from email import policy
from pathlib import Path
from typing import Union, BinaryIO, Optional

import pdfplumber


def extract_text_from_pdf(file_input: Union[str, Path, bytes, BinaryIO]) -> str:
    """
    Extract readable text from a PDF document using pdfplumber.

    Args:
        file_input: File path (str/Path), bytes, or a file-like binary stream.

    Returns:
        Extracted plain text across all pages.
    """
    if isinstance(file_input, (str, Path)):
        stream_or_path = str(file_input)
    elif isinstance(file_input, bytes):
        stream_or_path = io.BytesIO(file_input)
    else:
        # File-like object (e.g. UploadFile.file from FastAPI)
        if hasattr(file_input, "read"):
            content = file_input.read()
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            stream_or_path = io.BytesIO(content)
        else:
            stream_or_path = file_input

    text_parts = []
    with pdfplumber.open(stream_or_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

    return "\n\n".join(text_parts)


def extract_text_from_eml(file_input: Union[str, Path, bytes, BinaryIO]) -> str:
    """
    Extract email headers (From, To, Subject, Date) and plain text body from an .eml file.

    Args:
        file_input: File path (str/Path), raw bytes, or a file-like stream.

    Returns:
        Formatted email text representation including headers and decoded body.
    """
    if isinstance(file_input, (str, Path)):
        with open(file_input, "rb") as f:
            raw_bytes = f.read()
    elif isinstance(file_input, bytes):
        raw_bytes = file_input
    else:
        # Binary stream
        raw_bytes = file_input.read()
        if hasattr(file_input, "seek"):
            file_input.seek(0)

    # Parse message with default email policy
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)

    headers = []
    for h in ["From", "To", "Date", "Subject"]:
        val = msg.get(h)
        if val:
            headers.append(f"{h}: {val}")

    header_block = "\n".join(headers)

    # Extract body parts
    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_text += payload.decode(charset, errors="replace") + "\n"
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body_text = payload.decode(charset, errors="replace")

    if header_block:
        return f"{header_block}\n\n{body_text.strip()}"
    return body_text.strip()


def extract_text_from_file(
    file_input: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
) -> str:
    """
    Unified entry point to extract text from an uploaded document.
    Dispatches based on file extension (.pdf or .eml).

    Args:
        file_input: File path, bytes, or open binary stream.
        filename: Optional filename hint (e.g. upload.filename from FastAPI).

    Returns:
        Extracted plain text.

    Raises:
        ValueError: If file format is unsupported.
    """
    name_to_check = ""
    if filename:
        name_to_check = filename.lower()
    elif isinstance(file_input, (str, Path)):
        name_to_check = Path(file_input).name.lower()

    if name_to_check.endswith(".pdf"):
        return extract_text_from_pdf(file_input)
    elif name_to_check.endswith(".eml") or name_to_check.endswith(".msg"):
        return extract_text_from_eml(file_input)

    # Fallback attempt by trying PDF first, then EML
    try:
        pdf_text = extract_text_from_pdf(file_input)
        if pdf_text.strip():
            return pdf_text
    except Exception:
        pass

    try:
        eml_text = extract_text_from_eml(file_input)
        if eml_text.strip():
            return eml_text
    except Exception:
        pass

    raise ValueError(
        f"Unsupported document format for '{filename or file_input}'. "
        "Supported formats: .pdf, .eml"
    )
