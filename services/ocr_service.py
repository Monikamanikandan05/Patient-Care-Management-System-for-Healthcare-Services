"""
ocr_service.py
--------------
Uses Groq's vision-capable LLM to directly analyse uploaded images/PDFs and return:
  1. A human-readable description of the document/image.
  2. Structured medical data (medications, diagnoses, vitals, etc.) as JSON.

No Tesseract or OpenCV required — the AI sees the image directly.
"""

import os
import json
import base64
import logging
import io

from core.database import SessionLocal
from core.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

# ── Optional pdf2image (for PDF → image conversion) ──────────────────────────
try:
    from pdf2image import convert_from_path
    _pdf_available = True
except ImportError:
    convert_from_path = None
    _pdf_available = False

# ── Optional PaddleOCR Engine ────────────────────────────────────────────────
try:
    from paddleocr import PaddleOCR
    _paddle_available = True
except Exception:
    PaddleOCR = None
    _paddle_available = False

_paddle_engine = None

def get_paddle_ocr():
    global _paddle_engine
    if not _paddle_available:
        return None
    if _paddle_engine is None:
        try:
            # show_log was removed in newer PaddleOCR versions
            try:
                _paddle_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            except TypeError:
                _paddle_engine = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception as e:
            logger.warning(f"PaddleOCR init failed: {e}")
            return None
    return _paddle_engine

def extract_text_with_paddle(image_path: str) -> tuple:
    """Uses PaddleOCR to extract text lines and confidence scores."""
    engine = get_paddle_ocr()
    if not engine:
        return "", 0.0

    try:
        results = engine.ocr(image_path, cls=True)
        if not results or not results[0]:
            return "", 0.0

        lines = []
        confidences = []
        for line in results[0]:
            if line and len(line) >= 2:
                text, score = line[1]
                lines.append(text)
                confidences.append(float(score))

        full_text = "\n".join(lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.85
        return full_text, avg_conf
    except Exception as e:
        logger.warning(f"PaddleOCR extraction failed on {image_path}: {e}")
        return "", 0.0

# ── Groq vision models ────────────────────────────────────────────────────────
GROQ_VISION_MODELS = [
    "qwen/qwen3.6-27b",
]

# ── JSON schema the AI must return ───────────────────────────────────────────
_SYSTEM_PROMPT = (
    "You are a medical vision AI assistant. "
    "The user will provide an image of a medication, tablet, prescription, lab report, or medical document.\n\n"
    "Your job is to examine the image and return ONLY a JSON object in this exact format:\n"
    "{\n"
    '  "description": "Comprehensive description of what is in the image, including any text, tablet name, strength, appearance, or document contents.",\n'
    '  "documentType": "tablet_image | prescription | lab_report | discharge_summary | medical_image | unknown",\n'
    '  "overallConfidence": 0.95,\n'
    '  "tabletInfo": {\n'
    '    "name": "Tablet or Medicine Name if visible",\n'
    '    "strength": "Dosage/Strength if visible (e.g. 20mg, 500mg)",\n'
    '    "uses": "Primary medical uses and indications of this medication",\n'
    '    "howToUse": "Dosage instructions and how to take it",\n'
    '    "sideEffects": "Common side effects",\n'
    '    "purpose": "Therapeutic purpose or condition managed"\n'
    '  },\n'
    '  "reportInfo": {\n'
    '    "reportSummary": "Detailed summary of what is written in this document or report",\n'
    '    "keyFindings": ["Key finding or metric 1", "Key finding or metric 2"]\n'
    '  },\n'
    '  "fullExtractedText": "All visible text extracted from the image verbatim."\n'
    "}\n"
    "Focus strictly on describing what is in the image and its medical uses."
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: encode image file to base64
# ─────────────────────────────────────────────────────────────────────────────
def _image_to_base64(image_path: str) -> tuple:
    """Return (mime_type, base64_string) for an image file.
    Resizes large images to max 1280px and fixes EXIF orientation.
    """
    from PIL import Image as PILImage, ImageOps

    try:
        with PILImage.open(image_path) as img:
            # Auto-rotate based on EXIF camera orientation tags
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")

            # Downscale if image is very large (> 1280px in any dimension)
            max_dim = 1280
            if max(img.width, img.height) > max_dim:
                img.thumbnail((max_dim, max_dim), PILImage.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return "image/jpeg", b64
    except Exception as e:
        logger.warning(f"PIL processing failed ({e}), reading raw bytes…")
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/jpeg")
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return mime, b64


# ─────────────────────────────────────────────────────────────────────────────
# Helper: convert PDF first page to JPEG base64
# ─────────────────────────────────────────────────────────────────────────────
def _pdf_first_page_to_base64(pdf_path: str) -> tuple:
    """Convert the first page of a PDF to a base64 JPEG.
    Tries pdf2image first, falls back to Pillow, then raises friendly error.
    """
    from PIL import Image as PILImage

    # Option 1: pdf2image (requires poppler)
    if _pdf_available:
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
            if images:
                img = images[0].convert("RGB")
                if max(img.width, img.height) > 1280:
                    img.thumbnail((1280, 1280), PILImage.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                return "image/jpeg", b64
        except Exception as e:
            logger.warning(f"pdf2image failed ({e}), trying Pillow fallback…")

    # Option 2: Pillow direct PDF open
    try:
        img = PILImage.open(pdf_path)
        img.load()
        img = img.convert("RGB")
        if max(img.width, img.height) > 1280:
            img.thumbnail((1280, 1280), PILImage.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return "image/jpeg", b64
    except Exception as e:
        logger.warning(f"Pillow PDF open failed ({e}).")

    raise RuntimeError(
        "Cannot render PDF: please install poppler (for pdf2image) or "
        "upload the document as a JPG/PNG image instead."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Mock result (when no API key is configured)
# ─────────────────────────────────────────────────────────────────────────────
def _mock_vision_result() -> dict:
    return {
        "description": (
            "This appears to be a prescription document from Dr. Sarah Jenkins "
            "(Cardiology Clinic). It contains patient details, two prescribed medications "
            "(Lisinopril 10mg and Atorvastatin 20mg), and a diagnosis of Hypertension "
            "and Hyperlipidemia with a 3-month follow-up."
        ),
        "documentType": "prescription",
        "overallConfidence": 0.92,
        "patient": {
            "name": {"value": "John Doe", "confidence": 0.95},
            "dateOfBirth": {"value": "05/14/1980", "confidence": 0.90},
            "medicalRecordId": {"value": "", "confidence": 0.0},
        },
        "provider": {
            "name": {"value": "Dr. Sarah Jenkins", "confidence": 0.97},
            "facility": {"value": "Cardiology Clinic", "confidence": 0.95},
        },
        "medications": [
            {"name": "Lisinopril", "dose": "10mg", "route": "Oral", "frequency": "Once daily"},
            {"name": "Atorvastatin", "dose": "20mg", "route": "Oral", "frequency": "At bedtime"},
        ],
        "diagnoses": ["Hypertension", "Hyperlipidemia"],
        "labResults": [],
        "vitals": {},
        "allergies": [],
        "followUp": ["3 months"],
        "warnings": [],
        "fullExtractedText": (
            "DR. SARAH JENKINS\nCardiology Clinic\n123 Health Ave, MedCity\n"
            "Patient Name: John Doe\nDOB: 05/14/1980\nDate: 2026-08-13\n"
            "Rx:\n1. Lisinopril 10mg - Take 1 tablet daily\n"
            "2. Atorvastatin 20mg - Take 1 tablet at bedtime\n"
            "Diagnosis: Hypertension, Hyperlipidemia\nFollow up: 3 months"
        ),
        "aiReviewed": True,
        "requiresHumanReview": False,
    }


def _parse_json_safely(raw_text: str) -> dict:
    """Robustly parse LLM JSON responses, handling reasoning tags, markdown fences,
    trailing commas, truncated JSON output, and formatting quirks.
    """
    import re
    import ast

    # 1. Remove <think>...</think> reasoning blocks if model emitted them
    content = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

    # 2. Strip markdown fences ```json ... ```
    content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE).strip()

    # 3. Extract JSON object substring starting from {
    json_match = re.search(r'\{.*', content, flags=re.DOTALL)
    json_str = json_match.group(0) if json_match else content

    # Attempt 1: Standard JSON parse
    try:
        return json.loads(json_str)
    except Exception:
        pass

    # Attempt 2: Clean trailing commas before } or ]
    try:
        cleaned = re.sub(r',\s*([\}\]])', r'\1', json_str)
        return json.loads(cleaned)
    except Exception:
        pass

    # Attempt 3: Try repairing truncated JSON by closing open quotes and braces
    try:
        patched = json_str.rstrip()
        if not patched.endswith('}'):
            if patched.count('"') % 2 != 0:
                patched += '"'
            open_braces = patched.count('{') - patched.count('}')
            open_brackets = patched.count('[') - patched.count(']')
            patched += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
            cleaned = re.sub(r',\s*([\}\]])', r'\1', patched)
            return json.loads(cleaned)
    except Exception:
        pass

    # Attempt 4: ast.literal_eval fallback
    try:
        res = ast.literal_eval(json_str)
        if isinstance(res, dict):
            return res
    except Exception:
        pass

    # Attempt 5: Extract "description" field via regex if present
    extracted_desc = ""
    desc_match = re.search(r'"description"\s*:\s*"(.*?)"', json_str, flags=re.DOTALL)
    if desc_match:
        extracted_desc = desc_match.group(1).replace('\\n', '\n').strip()

    clean_desc = extracted_desc or re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
    clean_desc = re.sub(r'^```(?:json)?\s*\{?', '', clean_desc).strip()

    return {
        "description": clean_desc if clean_desc else "AI vision analysis complete.",
        "documentType": "prescription",
        "overallConfidence": 0.95,
        "fullExtractedText": clean_desc,
        "patient": {},
        "provider": {},
        "medications": [],
        "diagnoses": [],
        "labResults": [],
        "vitals": {},
        "allergies": [],
        "followUp": [],
        "warnings": ["JSON truncation auto-recovered."],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core Vision Analysis — tries each model until one succeeds
# ─────────────────────────────────────────────────────────────────────────────
def analyse_image_with_groq(image_path: str) -> dict:
    """
    Send the image to a Groq vision model and return a description + structured data.
    Tries GROQ_VISION_MODELS in order, skipping any that return 404.
    """
    import requests

    api_key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY

    # Prepare image as base64
    if image_path.lower().endswith(".pdf"):
        mime, b64 = _pdf_first_page_to_base64(image_path)
    else:
        mime, b64 = _image_to_base64(image_path)

    # No API key → use mock
    if not api_key or api_key.strip() in ("", "your_groq_api_key_here"):
        logger.warning("No Groq API key – returning mock vision result.")
        return _mock_vision_result()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    user_content = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        },
        {
            "type": "text",
            "text": (
                "Please analyse this medical document/image thoroughly. "
                "Describe what you see and extract all medical information. "
                "Return ONLY the JSON object as instructed in the system message."
            ),
        },
    ]

    last_error = None
    for model_name in GROQ_VISION_MODELS:
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
                "max_tokens": 3500,
            }

            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if not resp.ok:
                err_detail = resp.text[:300]
                logger.warning(f"Vision model '{model_name}' returned status {resp.status_code}: {err_detail}")
                last_error = f"Status {resp.status_code}: {err_detail}"
                continue

            raw_text = resp.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"Vision analysis succeeded with model: {model_name}")

            result = _parse_json_safely(raw_text)
            result.setdefault("description", "AI analysis complete.")
            result["aiReviewed"] = True
            result["requiresHumanReview"] = False
            result["_modelUsed"] = model_name
            return result

        except Exception as e:
            err_str = str(e)
            logger.warning(f"Groq vision attempt with '{model_name}' failed: {err_str}")
            last_error = err_str
            continue

    # All models exhausted
    logger.error(f"All vision models failed. Last error: {last_error}")
    return {
        "description": (
            f"AI vision could not analyse this image. "
            f"No working vision model found. Last error: {last_error}"
        ),
        "documentType": "unknown",
        "overallConfidence": 0.0,
        "patient": {},
        "provider": {},
        "medications": [],
        "diagnoses": [],
        "labResults": [],
        "vitals": {},
        "allergies": [],
        "followUp": [],
        "warnings": [last_error or "Unknown error"],
        "fullExtractedText": "",
        "aiReviewed": True,
        "requiresHumanReview": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline entry point
# ─────────────────────────────────────────────────────────────────────────────
def process_document(document_id: int):
    """Main OCR pipeline — Uses PaddleOCR (if available) + Groq AI Vision to review and save."""
    db = SessionLocal()
    doc = None
    try:
        from models.models import OCRDocument
        doc = db.query(OCRDocument).filter(OCRDocument.id == document_id).first()
        if not doc:
            return

        doc.status = "Processing"
        db.commit()

        # ── Step 1: PaddleOCR text extraction ────────────────────────────────
        paddle_text, paddle_conf = extract_text_with_paddle(doc.file_path)

        # ── Step 2: Groq AI Vision / LLM analysis ────────────────────────────
        structured_data = analyse_image_with_groq(doc.file_path)

        # ── Step 3: Merge PaddleOCR text if available ────────────────────────
        if paddle_text.strip():
            logger.info("PaddleOCR successfully extracted text lines.")
            structured_data["_paddleOcrUsed"] = True
            if not structured_data.get("fullExtractedText"):
                structured_data["fullExtractedText"] = paddle_text
            if paddle_conf > 0:
                structured_data["overallConfidence"] = round(paddle_conf, 2)

        # Persist results in OCRDocument table
        doc.extracted_data = json.dumps(structured_data)
        doc.overall_confidence = structured_data.get("overallConfidence", 0.85)
        doc.document_type = structured_data.get("documentType", "unknown")
        doc.status = "Approved"

    except Exception as e:
        logger.error(f"OCR Pipeline Error: {e}")
        if doc:
            doc.status = "Error"
            doc.error_message = str(e)
    finally:
        db.commit()
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Auto-save to HealthRecord
# ─────────────────────────────────────────────────────────────────────────────
def _save_to_health_record(doc, structured_data: dict, db):
    """Automatically saves AI-extracted data into the patient's HealthRecord."""
    try:
        from models.models import HealthRecord

        meds = structured_data.get("medications", [])
        diagnoses = structured_data.get("diagnoses", [])
        vitals = structured_data.get("vitals", {}) or {}
        doc_type = structured_data.get("documentType", "unknown")
        description = structured_data.get("description", "")

        # Diagnosis string
        if isinstance(diagnoses, list):
            diagnosis_str = ", ".join(
                [d if isinstance(d, str) else str(d) for d in diagnoses]
            ) or None
        else:
            diagnosis_str = str(diagnoses) or None

        # Notes summary
        med_lines = []
        for m in meds:
            if isinstance(m, dict):
                med_lines.append(
                    f"• {m.get('name','?')} {m.get('dose','')} {m.get('frequency','')}".strip()
                )
            else:
                med_lines.append(str(m))

        notes_parts = [f"[AI Vision OCR — {doc_type.replace('_', ' ').title()}]"]
        if description:
            notes_parts.append(f"AI Description:\n{description}")
        if med_lines:
            notes_parts.append("Medications:\n" + "\n".join(med_lines))
        provider_name = (
            structured_data.get("provider", {}).get("name", {}).get("value", "")
        )
        if provider_name:
            notes_parts.append(f"Provider: {provider_name}")
        follow_up = structured_data.get("followUp", [])
        if follow_up:
            notes_parts.append(
                f"Follow-up: {', '.join(follow_up) if isinstance(follow_up, list) else follow_up}"
            )
        raw_text = structured_data.get("fullExtractedText", "")
        if raw_text:
            notes_parts.append(f"Extracted Text:\n{raw_text[:1000]}")

        notes_str = "\n\n".join(notes_parts)

        hr = HealthRecord(
            patient_id=doc.patient_id,
            doctor_id=None,
            diagnosis=diagnosis_str,
            notes=notes_str,
            heart_rate=_safe_int(vitals.get("heartRate")),
            blood_pressure=vitals.get("bloodPressure") or None,
            oxygen_saturation=_safe_int(vitals.get("oxygenSaturation")),
            blood_sugar=_safe_int(vitals.get("bloodSugar")),
        )
        db.add(hr)
        logger.info(
            f"HealthRecord auto-created for patient {doc.patient_id} "
            f"from OCR document {doc.id}"
        )
    except Exception as e:
        logger.error(f"Failed to save HealthRecord from OCR: {e}")


def _safe_int(val):
    """Safely convert a value to int, returning None on failure."""
    try:
        return int(float(str(val))) if val is not None else None
    except (ValueError, TypeError):
        return None
