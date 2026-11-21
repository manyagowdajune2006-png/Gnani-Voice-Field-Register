"""Visit information extraction with Gemini and a local fallback."""

import json
import os
import re
from datetime import date

from dotenv import load_dotenv

load_dotenv()

VISIT_FIELDS = [
    "visit_date",
    "village",
    "household_id",
    "person_name",
    "age",
    "main_concern",
    "notes",
]


def _empty_result(form=None):
    result = {field: "" for field in VISIT_FIELDS}
    if isinstance(form, dict):
        for field in VISIT_FIELDS:
            if form.get(field) is not None:
                result[field] = str(form[field])
    return result


def _local_extract(text, form):
    """Extract simple, clearly spoken English field values."""
    text = str(text or "").strip()
    lower = text.lower()
    result = dict(form)

    # Recognise dates such as 21 November 2026 or 21/11/2026.
    date_match = re.search(
        r"\b(\d{1,2})\s+(January|February|March|April|May|June|"
        r"July|August|September|October|November|December)\s+(\d{4})\b",
        text,
        re.IGNORECASE,
    )

    if date_match:
        try:
            from datetime import datetime
            parsed = datetime.strptime(
                date_match.group(0), "%d %B %Y"
            ).date()
            result["visit_date"] = parsed.isoformat()
        except ValueError:
            pass
    else:
        numeric_date = re.search(
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
            text,
        )
        if numeric_date:
            try:
                parsed = date(
                    int(numeric_date.group(3)),
                    int(numeric_date.group(2)),
                    int(numeric_date.group(1)),
                )
                result["visit_date"] = parsed.isoformat()
            except ValueError:
                pass

    patterns = {
        "village": r"\bvillage\s+(?:is\s+)?([A-Za-z][A-Za-z -]{1,40})",
        "household_id": r"\bhousehold\s+(?:id|number|no\.?)\s+(?:is\s+)?([A-Za-z0-9-]+)",
        "person_name": r"\b(?:the\s+)?(?:person'?s|patient'?s|beneficiary'?s|person|patient|beneficiary)\s+name\s+(?:is\s+)?([A-Za-z][A-Za-z ]{0,40})",
        "age": r"\bage\s+(?:is\s+)?(\d{1,3})\b",
        "main_concern": r"\bmain concern\s+(?:is\s+)?(.+)",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip(" .,")

    notes_text = lower

    if any(phrase in notes_text for phrase in (
        "no additional notes",
        "no notes",
        "nothing else",
        "no further notes",
        "none"
    )):
        result["notes"] = "None"
    else:
        notes_match = re.search(
            r"\\b(?:additional notes|notes)\\s+(?:are|is|:)?\\s*(.+)",
            text,
            re.IGNORECASE,
        )
        if notes_match:
            result["notes"] = notes_match.group(1).strip(" .,")

    return result


def extract_visit(text, state=None, form=None, today=None):
    """Extract factual visit fields. Never diagnose or recommend treatment."""
    result = _local_extract(text, _empty_result(form))

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            "form": result,
            "missing_fields": [
                field for field in VISIT_FIELDS if not result[field]
            ],
            "used_ai": False,
        }

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = f"""
Extract factual information from this field visit conversation.
Return ONLY a JSON object with these keys:
{", ".join(VISIT_FIELDS)}

Use only facts clearly stated. Preserve existing values unless corrected.
Use empty strings for unknown values. Do not guess, diagnose, or recommend treatment.

Today's date: {today or "not provided"}
Existing form: {json.dumps(result, ensure_ascii=False)}
Conversation: {text}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw = response.text or ""
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        extracted = json.loads(raw)

        if isinstance(extracted, dict):
            for field in VISIT_FIELDS:
                value = extracted.get(field)
                if isinstance(value, (str, int, float)) and str(value).strip():
                    result[field] = str(value).strip()

        used_ai = True

    except Exception:
        used_ai = False

    return {
        "form": result,
        "missing_fields": [
            field for field in VISIT_FIELDS if not result[field]
        ],
        "used_ai": used_ai,
    }
