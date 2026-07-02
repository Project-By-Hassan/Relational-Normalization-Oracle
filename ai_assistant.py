"""
AI helper module for the Relational Normalization Oracle.

Handles:
- Calling Groq's chat completion endpoint (text + vision) with sane error handling
- Extracting a normalization problem (attributes, FDs, MVDs, JDs) from a PDF
- Extracting a normalization problem from an uploaded image (photo / screenshot of
  a textbook question, handwritten notes, whiteboard, etc.)

NOTE ON MODELS: Groq deprecated `llama-3.3-70b-versatile` and
`meta-llama/llama-4-scout-17b-16e-instruct` on 2026-06-17. This module uses their
recommended replacements:
    - Text chat / JSON extraction from PDF text -> "openai/gpt-oss-120b"
    - Image (vision) understanding          -> "meta-llama/llama-4-maverick-17b-128e-instruct"
If Groq deprecates these in the future, only the MODEL_* constants below need updating.
"""

import base64
import io
import json
import re

import requests

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_TEXT = "openai/gpt-oss-120b"
MODEL_VISION = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Groq's base64-inlined image requests are capped well below the 20MB URL limit.
MAX_IMAGE_BYTES = 4 * 1024 * 1024

EXTRACTION_INSTRUCTIONS = """You are a database-normalization problem parser.

You will be given the content of an academic problem (a photo, scanned page, or PDF
text) that describes a relational schema, possibly with functional dependencies (FDs),
multi-valued dependencies (MVDs), and/or join dependencies (JDs).

Read it carefully and return ONLY a single JSON object (no markdown, no commentary,
no code fences) with this exact shape:

{
  "attributes": "A, B, C",
  "fds": "A -> B\\nB, C -> D",
  "mvds": "",
  "jds": "",
  "summary": "One short sentence describing what you found."
}

Rules:
- "attributes": comma-separated list of ALL attribute names in the relation.
- "fds": one functional dependency per line, formatted exactly as "LHS -> RHS",
  using commas to separate multiple attributes on either side, e.g. "A, B -> C".
- "mvds": one multi-valued dependency per line, formatted as "LHS ->-> RHS". Leave
  as an empty string "" if none are described.
- "jds": one join dependency per line, formatted as "Join(A B, B C, A C)". Leave as
  an empty string "" if none are described.
- If the source uses full words for attributes (e.g. "StudentID"), keep them as-is;
  do not abbreviate to single letters.
- If nothing resembling a normalization problem is found, return all fields as
  empty strings and explain briefly in "summary".
- Output must be valid JSON and nothing else.
"""


class ExtractionError(Exception):
    pass


def _call_groq(messages, api_key, model, want_json=True, timeout=45):
    if not api_key:
        raise ExtractionError("Groq API key is missing. Check your .env file.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    if want_json:
        payload["response_format"] = {"type": "json_object"}

    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise ExtractionError(f"Could not reach Groq API: {e}")

    if resp.status_code != 200:
        # Some vision models don't support response_format=json_object; retry plain.
        if want_json and resp.status_code in (400, 422):
            payload.pop("response_format", None)
            try:
                resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=timeout)
            except requests.exceptions.RequestException as e:
                raise ExtractionError(f"Could not reach Groq API: {e}")
        if resp.status_code != 200:
            raise ExtractionError(f"Groq API error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ExtractionError("Unexpected response shape from Groq API.")


def _parse_extraction_json(raw_text):
    # Strip ```json ... ``` fences if the model added them despite instructions.
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: grab the first {...} block.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ExtractionError("AI response was not valid JSON.")
        try:
            result = json.loads(match.group(0))
        except json.JSONDecodeError:
            raise ExtractionError("AI response was not valid JSON.")

    for field in ("attributes", "fds", "mvds", "jds", "summary"):
        result.setdefault(field, "")
    return result


def extract_schema_from_pdf_bytes(pdf_bytes, api_key, max_chars=12000):
    """Extracts text from a PDF and asks the AI to identify the normalization problem."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ExtractionError("pypdf is not installed. Run: pip install pypdf")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        full_text = "\n".join(text_parts).strip()
    except Exception as e:
        raise ExtractionError(f"Could not read PDF: {e}")

    if not full_text:
        raise ExtractionError(
            "No extractable text found in this PDF (it may be a scanned image). "
            "Try uploading it as an image instead."
        )

    full_text = full_text[:max_chars]

    messages = [
        {"role": "system", "content": EXTRACTION_INSTRUCTIONS},
        {"role": "user", "content": f"Here is the problem text extracted from a PDF:\n\n{full_text}"},
    ]
    raw = _call_groq(messages, api_key, MODEL_TEXT, want_json=True)
    return _parse_extraction_json(raw)


def extract_schema_from_image_bytes(image_bytes, mime_type, api_key):
    """Sends an image to a Groq vision model and asks it to identify the normalization problem."""
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ExtractionError(
            f"Image is too large ({len(image_bytes) / 1_000_000:.1f}MB). "
            f"Please upload an image under {MAX_IMAGE_BYTES // 1_000_000}MB."
        )

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    messages = [
        {"role": "system", "content": EXTRACTION_INSTRUCTIONS},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract the normalization problem from this image."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    raw = _call_groq(messages, api_key, MODEL_VISION, want_json=True)
    return _parse_extraction_json(raw)


def chat_completion(messages, api_key, model=MODEL_TEXT, timeout=20):
    """Shared helper for the freeform AI Normalization Guide chat (text-only)."""
    return _call_groq(messages, api_key, model, want_json=False, timeout=timeout)
