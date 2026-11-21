
from backend.llm import extract_visit, VISIT_FIELDS
from backend.danger import check_danger
from backend.phrases import get_referral_phrase
from backend.db import save_confirmed_visit

REQUIRED_FIELDS = VISIT_FIELDS

QUESTIONS = {
    "visit_date": {
        "en": "What is the visit date?",
        "hi": "आज की तारीख क्या है?",
    },
    "village": {
        "en": "Which village is this visit in?",
        "hi": "यह दौरा किस गांव में है?",
    },
    "household_id": {
        "en": "What is the household ID?",
        "hi": "परिवार की पहचान संख्या क्या है?",
    },
    "person_name": {
        "en": "What is the person's name?",
        "hi": "व्यक्ति का नाम क्या है?",
    },
    "age": {
        "en": "What is the person's age?",
        "hi": "व्यक्ति की उम्र क्या है?",
    },
    "main_concern": {
        "en": "What is the main concern reported?",
        "hi": "मुख्य स्वास्थ्य समस्या क्या है?",
    },
    "notes": {
        "en": "Are there any additional notes? If not, say no additional notes.",
        "hi": "क्या कोई और जानकारी है? अगर नहीं, तो कहें कि कोई अतिरिक्त जानकारी नहीं है।",
    },
}


def create_session(language="en"):
    return {
        "language": language if language in ("en", "hi") else "en",
        "state": "LISTENING",
        "form": {field: "" for field in VISIT_FIELDS},
        "transcript": [],
        "confirmed": False,
        "saved_id": None,
        "danger_flags": [],
    }


def handle_turn(session, text, llm_fn=None, danger_fn=None):
    if not isinstance(session, dict):
        raise ValueError("Invalid session.")

    text = str(text or "").strip()
    language = session.get("language", "en")

    if not text:
        return [{
            "type": "say",
            "text": "Please speak or enter your response."
            if language == "en"
            else "कृपया बोलें या अपना जवाब बताएं।"
        }]

    session.setdefault("transcript", []).append(text)

    if session.get("state") == "AWAITING_CONFIRMATION":
        answer = " ".join(text.casefold().replace(",", " ").replace(".", " ").replace("!", " ").replace("?", " ").split())

        if answer in ("yes", "yes i confirm", "i confirm", "हाँ", "हां", "जी हाँ", "जी हां"):
            session["confirmed"] = True
            session["state"] = "CONFIRMED"

            try:
                record_id = save_confirmed_visit(
                    session,
                    "\n".join(session.get("transcript", [])),
                )
                session["saved_id"] = record_id
                return [{
                    "type": "say",
                    "text": "The confirmed visit has been saved."
                    if language == "en"
                    else "पुष्टि की गई विज़िट सफलतापूर्वक सेव हो गई है।",
                }]
            except Exception:
                session["confirmed"] = False
                session["state"] = "AWAITING_CONFIRMATION"
                return [{
                    "type": "say",
                    "text": "I could not save the visit. Please check the secure database settings."
                    if language == "en"
                    else "विज़िट सेव नहीं हो सकी। कृपया डेटाबेस सेटिंग जांचें।",
                }]

        if answer in ("no", "no i don't", "नहीं", "जी नहीं"):
            session["state"] = "LISTENING"
            session["confirmed"] = False
            return [{
                "type": "say",
                "text": "Okay. Please tell me what needs to be corrected."
                if language == "en"
                else "ठीक है। कृपया बताएं कि क्या सुधार करना है।",
            }]

        return [{
            "type": "say",
            "text": "Please answer yes to confirm or no to make corrections."
            if language == "en"
            else "पुष्टि करने के लिए हाँ या सुधार करने के लिए नहीं कहें।",
        }]

    if session.get("state") == "CONFIRMED":
        return [{
            "type": "say",
            "text": "This visit is already saved. Start a new visit for another record."
            if language == "en"
            else "यह विज़िट पहले ही सेव हो चुकी है। नया रिकॉर्ड बनाने के लिए नई विज़िट शुरू करें।",
        }]

    extractor = llm_fn or extract_visit
    result = extractor(
        text,
        state=session.get("state"),
        form=session.get("form", {}),
    )

    if not isinstance(result, dict):
        result = {"form": session.get("form", {})}

    session["form"] = result.get("form", session.get("form", {}))

    detector = danger_fn or check_danger
    flags = detector(session["form"], text, None)
    session["danger_flags"] = flags

    referral = None
    if "emergency" in flags:
        referral = get_referral_phrase(language, "emergency")
    elif "urgent" in flags:
        referral = get_referral_phrase(language, "urgent")

    missing = [
        field for field in REQUIRED_FIELDS
        if not session["form"].get(field)
    ]

    if missing:
        session["state"] = "LISTENING"
        messages = []

        if referral:
            messages.append({"type": "say", "text": referral})

        field = missing[0]
        messages.append({
            "type": "say",
            "text": QUESTIONS[field][language],
        })
        return messages

    session["state"] = "AWAITING_CONFIRMATION"

    summary = "\n".join(
        f"{field.replace('_', ' ')}: {value or 'Not provided'}"
        for field, value in session["form"].items()
    )

    messages = []
    if referral:
        messages.append({"type": "say", "text": referral})

    messages.append({
        "type": "say",
        "text": (
            "Please review these details:\n" + summary
            + "\nDo you confirm? Please say yes or no."
            if language == "en"
            else "कृपया इन जानकारियों की जांच करें:\n" + summary
            + "\nक्या आप इसकी पुष्टि करते हैं? कृपया हाँ या नहीं कहें।"
        ),
    })

    return messages
