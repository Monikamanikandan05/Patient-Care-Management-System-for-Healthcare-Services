import json
import streamlit as st
import os
from core.database import SessionLocal
from models.models import OCRDocument
from services.ocr_service import process_document

UPLOAD_DIR = "assets/uploads/ocr"

# ── Icons for document types ──────────────────────────────────────────────────
DOC_TYPE_ICONS = {
    "prescription":       "💊",
    "lab_report":         "🧪",
    "discharge_summary":  "🏥",
    "insurance_card":     "🪪",
    "clinical_note":      "📋",
    "unknown":            "📄",
}

def render_ocr_upload(user):
    st.title("📄 Upload Medical Documents")
    st.markdown(
        "Upload a photo or file of any medical document — prescription, lab report, "
        "insurance card, or discharge summary. **AI will instantly read and extract the data** "
        "and save it to your health record automatically."
    )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 1. Camera capture
    with st.expander("📸 Capture with Camera", expanded=False):
        camera_file = st.camera_input("Take a clear picture of the document")
        if camera_file is not None:
            _handle_upload(camera_file, user)

    # 2. File upload
    st.markdown("### Or Upload a File")
    uploaded_file = st.file_uploader(
        "Upload an image or PDF",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
    )
    if uploaded_file is not None:
        is_pdf = uploaded_file.name.lower().endswith(".pdf")

        # Check pdf2image availability for PDF files
        _pdf_ok = True
        if is_pdf:
            try:
                from pdf2image import convert_from_path  # noqa: F401
            except ImportError:
                _pdf_ok = False

        if is_pdf and not _pdf_ok:
            st.warning(
                "⚠️ **PDF rendering is not available** on this system.\n\n"
                "To analyse your document please:\n"
                "- 📸 **Take a photo** of the document using the Camera option above, **or**\n"
                "- 🖼️ **Convert the PDF to an image** (PNG/JPG) and re-upload it.\n\n"
                "_Tip: on Windows you can open the PDF and press **Windows + Shift + S** "
                "to take a screenshot, then save it as a PNG._"
            )
        else:
            if st.button("📤 Process Document with AI", type="primary"):
                _handle_upload(uploaded_file, user)

    # 3. Document history
    st.markdown("---")
    st.markdown("### 📂 Your Uploaded Documents")
    db = SessionLocal()
    try:
        docs = (
            db.query(OCRDocument)
            .filter(OCRDocument.patient_id == user["id"])
            .order_by(OCRDocument.created_at.desc())
            .all()
        )

        if not docs:
            st.info("You haven't uploaded any documents yet.")
        else:
            for doc in docs:
                _render_doc_card(doc, db)
    finally:
        db.close()


def _render_doc_card(doc, db):
    """Render a single document result card."""
    doc_type = doc.document_type or "unknown"
    icon = DOC_TYPE_ICONS.get(doc_type, "📄")
    label = doc_type.replace("_", " ").title()
    confirm_key = f"confirm_delete_{doc.id}"

    with st.container(border=True):
        header_cols = st.columns([0.07, 0.53, 0.26, 0.14])

        with header_cols[0]:
            st.markdown(f"## {icon}")

        with header_cols[1]:
            st.markdown(f"**{label}**  •  `{doc.created_at.strftime('%Y-%m-%d %H:%M')}`")
            if doc.overall_confidence:
                conf = float(doc.overall_confidence)
                st.progress(conf, text=f"AI Confidence: {conf*100:.0f}%")

        with header_cols[2]:
            if doc.status == "Approved":
                st.success("✅ AI Verified & Saved")
            elif doc.status == "Processing":
                st.info("⏳ Processing…")
            elif doc.status == "Error":
                st.error("❌ Error")
            else:
                st.warning(f"⚠️ {doc.status}")

        with header_cols[3]:
            st.markdown("")
            if st.button("🗑️ Delete", key=f"del_btn_{doc.id}",
                         use_container_width=True, type="secondary"):
                st.session_state[confirm_key] = True

        # ── Inline delete confirmation ──────────────────────────────────────
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure you want to delete this document? This cannot be undone.")
            yes_col, no_col = st.columns(2)
            if yes_col.button("✅ Yes, Delete", key=f"yes_{doc.id}",
                              type="primary", use_container_width=True):
                _delete_document(doc, db)
                st.rerun()
            if no_col.button("↩️ Cancel", key=f"no_{doc.id}",
                             use_container_width=True):
                st.session_state[confirm_key] = False
                st.rerun()
            return  # Don't render the rest while confirming

        # Error detail
        if doc.status == "Error" and doc.error_message:
            st.error(f"Error details: {doc.error_message}")
            return

        # Extracted data panel
        if doc.extracted_data:
            try:
                data = json.loads(doc.extracted_data)
            except Exception:
                data = {}

            if data:
                # Show AI description prominently
                description = data.get("description", "")
                if description:
                    st.info(f"🤖 **AI Analysis:** {description}")

                with st.expander("📋 View Full Extracted Details", expanded=True):
                    _render_extracted_data(data, doc)


def _render_extracted_data(data: dict, doc):
    """Render structured extracted data in a readable format."""

    # ── AI description (full) ─────────────────────────────────────────────────
    description = data.get("description", "")
    if description:
        st.markdown("### 🤖 What AI Sees")
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#1e3a5f,#0f2027);padding:16px;"
            f"border-radius:10px;color:#e8f4f8;font-size:15px;line-height:1.6;border-left:"
            f"4px solid #38bdf8;'>{description}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        # Patient info
        patient = data.get("patient", {})
        p_name = patient.get("name", {}).get("value", "—")
        p_dob  = patient.get("dateOfBirth", {}).get("value", "—")
        st.markdown("**👤 Patient**")
        st.markdown(f"- Name: **{p_name}**")
        st.markdown(f"- DOB: **{p_dob}**")

        # Provider info
        provider = data.get("provider", {})
        prov_name     = provider.get("name", {}).get("value", "—")
        prov_facility = provider.get("facility", {}).get("value", "—")
        st.markdown("**🏥 Provider**")
        st.markdown(f"- Name: **{prov_name}**")
        st.markdown(f"- Facility: **{prov_facility}**")

    with col2:
        # Diagnoses
        diagnoses = data.get("diagnoses", [])
        if diagnoses:
            st.markdown("**🩺 Diagnoses**")
            for d in diagnoses:
                st.markdown(f"- {d}")

        # Vitals
        vitals = data.get("vitals", {})
        if vitals:
            st.markdown("**📊 Vitals**")
            for k, v in vitals.items():
                if v:
                    st.markdown(f"- {k}: **{v}**")

    # Medications table
    meds = data.get("medications", [])
    if meds:
        st.markdown("**💊 Medications**")
        med_rows = []
        for m in meds:
            if isinstance(m, dict):
                med_rows.append({
                    "Name":      m.get("name", "—"),
                    "Dose":      m.get("dose", "—"),
                    "Route":     m.get("route", "—"),
                    "Frequency": m.get("frequency", "—"),
                })
        if med_rows:
            st.table(med_rows)

    # Lab results
    labs = data.get("labResults", [])
    if labs:
        st.markdown("**🧪 Lab Results**")
        lab_rows = []
        for l in labs:
            if isinstance(l, dict):
                lab_rows.append({
                    "Test":   l.get("test", "—"),
                    "Value":  l.get("value", "—"),
                    "Unit":   l.get("unit", "—"),
                    "Normal": l.get("normalRange", "—"),
                })
        if lab_rows:
            st.table(lab_rows)

    # Follow-up
    follow_up = data.get("followUp", [])
    if follow_up:
        st.markdown("**📅 Follow-up**")
        if isinstance(follow_up, list):
            for f in follow_up:
                st.markdown(f"- {f}")
        else:
            st.markdown(f"- {follow_up}")

    # Original image preview
    if not doc.file_path.endswith(".pdf"):
        with st.expander("🖼️ Original Document Image"):
            st.image(doc.file_path, use_container_width=True)

    # Raw text
    raw_text = data.get("fullExtractedText", "")
    if raw_text:
        with st.expander("📝 Raw Extracted Text"):
            st.code(raw_text, language="text")

    st.caption("✨ Data extracted and saved automatically by AI — no manual review required.")


def _handle_upload(file_obj, user):
    """Save file, run OCR pipeline, and show results."""
    file_path = os.path.join(UPLOAD_DIR, f"{user['id']}_{file_obj.name}")

    with open(file_path, "wb") as f:
        f.write(file_obj.getbuffer())

    db = SessionLocal()
    try:
        new_doc = OCRDocument(
            patient_id=user["id"],
            uploaded_by_id=user["id"],
            file_path=file_path,
            file_type=file_obj.type,
            status="Pending",
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        doc_id = new_doc.id

        with st.spinner("🤖 AI is reading your document…"):
            process_document(doc_id)

        # Refresh doc
        db.expire_all()
        doc = db.query(OCRDocument).filter(OCRDocument.id == doc_id).first()

        if doc and doc.status == "Approved":
            st.success("✅ Document processed and saved to your health record!")
            st.balloons()
        elif doc and doc.status == "Error":
            st.error(f"❌ Processing failed: {doc.error_message}")
        else:
            st.warning("Processing completed with an unexpected status.")

    except Exception as e:
        st.error(f"Failed to upload or process: {str(e)}")
    finally:
        db.close()

    st.rerun()


def _delete_document(doc, db):
    """Delete an OCR document record and its physical file."""
    try:
        # Remove the physical file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            # Also remove the temporary .jpg if PDF was converted
            pdf_jpg = doc.file_path + ".jpg"
            if os.path.exists(pdf_jpg):
                os.remove(pdf_jpg)

        # Delete the DB record
        db.delete(doc)
        db.commit()
        st.success("🗑️ Document deleted successfully.")
    except Exception as e:
        db.rollback()
        st.error(f"Failed to delete document: {str(e)}")
