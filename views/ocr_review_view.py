import streamlit as st
import json
from core.database import SessionLocal
from models.models import OCRDocument, HealthRecord, User
import ast

def render_ocr_review(user):
    st.title("🛡️ OCR Document Review Workflow")
    st.markdown("""
    **Clinical Safety Notice**: 
    > OCR-extracted data requires human verification. 
    > Review the extracted fields against the original document. Only confirmed data will be saved to the patient record.
    """)

    db = SessionLocal()
    try:
        # Get all documents needing review
        docs = db.query(OCRDocument).filter(OCRDocument.status == "NeedsReview").order_by(OCRDocument.created_at.asc()).all()
        
        if not docs:
            st.success("No documents currently need review.")
            return

        doc_options = {d.id: f"Doc #{d.id} - {d.document_type} (Patient ID: {d.patient_id}) - Conf: {d.overall_confidence*100:.1f}%" for d in docs}
        selected_doc_id = st.selectbox("Select document to review", options=list(doc_options.keys()), format_func=lambda x: doc_options[x])
        
        if selected_doc_id:
            doc = db.query(OCRDocument).filter(OCRDocument.id == selected_doc_id).first()
            _render_review_interface(doc, db, user)
            
    finally:
        db.close()

def _render_review_interface(doc, db, user):
    st.divider()
    cols = st.columns([1, 1])
    
    with cols[0]:
        st.subheader("Original Document")
        if doc.file_path.endswith('.pdf'):
            st.markdown("*(PDF preview requires external viewer, showing downloaded path)*")
            st.write(doc.file_path)
        else:
            st.image(doc.file_path, use_container_width=True)
            
    with cols[1]:
        st.subheader("Extracted Data (Edit to Fix)")
        try:
            data = json.loads(doc.extracted_data)
        except:
            data = {"error": "Invalid JSON data in database."}

        # Let the doctor edit the JSON or form fields
        # For simplicity, we expose the JSON directly to edit, but in a real UI, forms are better.
        # We will use text areas and inputs.
        
        doc_type = st.selectbox("Document Type", ["prescription", "lab_report", "discharge_summary", "insurance_card", "clinical_note", "unknown"], 
                                index=["prescription", "lab_report", "discharge_summary", "insurance_card", "clinical_note", "unknown"].index(data.get("documentType", "unknown")))
        
        # Display Patient info
        st.markdown("#### Patient Extracted Info")
        p_name = st.text_input("Patient Name", value=data.get("patient", {}).get("name", {}).get("value", ""))
        p_dob = st.text_input("DOB", value=data.get("patient", {}).get("dateOfBirth", {}).get("value", ""))
        
        # Display medications
        st.markdown("#### Medications")
        meds_text = json.dumps(data.get("medications", []), indent=2)
        edited_meds = st.text_area("Medications (JSON array)", value=meds_text, height=150)
        
        st.markdown("#### Diagnoses")
        diag_text = json.dumps(data.get("diagnoses", []), indent=2)
        edited_diags = st.text_area("Diagnoses (JSON array)", value=diag_text, height=100)
        
        st.markdown("#### Raw Extracted Text")
        with st.expander("View Raw Text"):
            st.text(data.get("fullExtractedText", ""))

        st.markdown("### Actions")
        action_cols = st.columns(3)
        if action_cols[0].button("✅ Approve & Save", type="primary", use_container_width=True):
            try:
                # Basic validation of JSONs
                meds_json = json.loads(edited_meds)
                diag_json = json.loads(edited_diags)
                
                # Save to patient chart (HealthRecord)
                diagnosis_str = ", ".join(diag_json) if isinstance(diag_json, list) else str(diag_json)
                notes_str = f"OCR Document Type: {doc_type}\nMedications:\n{json.dumps(meds_json, indent=2)}\n\nOriginal Text Reference available in Document #{doc.id}"
                
                hr = HealthRecord(
                    patient_id=doc.patient_id,
                    doctor_id=user["id"] if user["role"] == "Doctor" else None,
                    diagnosis=diagnosis_str,
                    notes=notes_str
                )
                db.add(hr)
                
                # Update doc status
                doc.status = "Approved"
                
                # Update extracted data with approved changes
                data["documentType"] = doc_type
                data["patient"]["name"]["value"] = p_name
                data["patient"]["dateOfBirth"]["value"] = p_dob
                data["medications"] = meds_json
                data["diagnoses"] = diag_json
                data["requiresHumanReview"] = False
                doc.extracted_data = json.dumps(data)
                
                db.commit()
                st.success("Document approved and Health Record created!")
                st.rerun()
                
            except json.JSONDecodeError:
                st.error("Invalid JSON format in Medications or Diagnoses. Please fix before approving.")
                
        if action_cols[1].button("❌ Reject Document", type="secondary", use_container_width=True):
            doc.status = "Rejected"
            db.commit()
            st.success("Document rejected.")
            st.rerun()
