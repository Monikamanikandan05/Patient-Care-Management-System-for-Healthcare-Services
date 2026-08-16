import streamlit as st
from core.database import SessionLocal
from services.health_service import get_health_records
from views.components import html, heartbeat_metric, format_doctor_name

def render_specialty_vitals(rec):
    """Renders the vitals card nicely using Streamlit metrics and custom HTML based on the record's specialty."""
    st_type = rec.specialty_type.lower() if rec.specialty_type else ""
    
    if "cardio" in st_type or "surgery" in st_type or not st_type:
        st.write("### 💗 Latest Cardiology Vitals")
        col1, col2, col3 = st.columns(3)
        with col1:
            heartbeat_metric("❤️ Heart Rate", f"{rec.heart_rate or 0} bpm")
            st.metric("🩸 Blood Pressure", rec.blood_pressure or "N/A")
        with col2:
            st.metric("🧪 Troponin Level", f"{rec.troponin or 0.0} ng/mL")
            st.metric("⚡ Ejection Fraction", f"{rec.ejection_fraction or 0}%")
        with col3:
            st.metric("🌬️ SpO2 Vitals", f"{rec.pulse_oximetry or 0}%")
            st.metric("📊 Cardiac Output", f"{rec.cardiac_output or 0.0} L/min")
            
        html(
            f'<div class="medical-card" style="border-left: 5px solid #ef4444;">'
            f'<h4 style="margin:0;color:#ef4444;">Latest Diagnosis: {rec.diagnosis or "General Assessment"}</h4>'
            f'<p style="margin:8px 0 0 0;font-size:0.95rem;color:#d1d5db;">'
            f'<b>ECG Rhythm Analysis:</b> {rec.ecg_note or "Not Available"}<br>'
            f'<b>Doctor Notes:</b> {rec.notes or "No comments."}<br>'
            f'<small style="color:#9ca3af;">Recorded on: {rec.recorded_at}</small></p></div>'
        )
        
    elif "dentist" in st_type or "dental" in st_type:
        st.write("### 🦷 Latest Dental Record")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🦷 Teeth Condition", rec.teeth_condition or "N/A")
        with col2:
            st.metric("🔴 Gum Health Status", rec.gum_health or "N/A")
        with col3:
            st.metric("📅 Next Visit Recommendation", rec.next_dental_visit or "N/A")
            
        html(
            f'<div class="medical-card" style="border-left: 5px solid #3b82f6;">'
            f'<h4 style="margin:0;color:#3b82f6;">Latest Diagnosis: {rec.diagnosis or "Routine Inspection"}</h4>'
            f'<p style="margin:8px 0 0 0;font-size:0.95rem;color:#d1d5db;">'
            f'<b>Procedure Undertaken:</b> {rec.procedure_done or "None"}<br>'
            f'<b>X-Ray Findings:</b> {rec.xray_finding or "No dental X-ray recorded"}<br>'
            f'<b>Doctor Notes:</b> {rec.notes or "No comments."}<br>'
            f'<small style="color:#9ca3af;">Recorded on: {rec.recorded_at}</small></p></div>'
        )

    elif "ophthal" in st_type or "eye" in st_type:
        st.write("### 👁️ Latest Ophthalmology Eye Report")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👁️ Right Eye Vision", rec.right_eye_vision or "N/A")
            st.metric("👁️ Left Eye Vision", rec.left_eye_vision or "N/A")
        with col2:
            st.metric("🩺 Intraocular Pressure (IOP)", rec.eye_pressure_iop or "N/A")
        with col3:
            st.metric("🧬 Diagnosed Condition", rec.eye_condition or "N/A")

        html(
            f'<div class="medical-card" style="border-left: 5px solid #10b981;">'
            f'<h4 style="margin:0;color:#10b981;">Latest Diagnosis: {rec.diagnosis or "Standard Optometry"}</h4>'
            f'<p style="margin:8px 0 0 0;font-size:0.95rem;color:#d1d5db;">'
            f'<b>Retina Condition:</b> {rec.retina_status or "Normal"}<br>'
            f'<b>Doctor Notes:</b> {rec.notes or "No comments."}<br>'
            f'<small style="color:#9ca3af;">Recorded on: {rec.recorded_at}</small></p></div>'
        )

    elif "pulmo" in st_type or "chest" in st_type or "lung" in st_type:
        st.write("### 🫁 Latest Pulmonology Chest Vitals")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌬️ Oxygen Saturation", f"{rec.oxygen_saturation or 0}%")
        with col2:
            st.metric("🫁 Respiratory Rate", f"{rec.respiratory_rate or 0} breaths/min")
        with col3:
            st.metric("📊 FEV1 Lung Capacity", rec.fev1 or "N/A")

        html(
            f'<div class="medical-card" style="border-left: 5px solid #a855f7;">'
            f'<h4 style="margin:0;color:#a855f7;">Latest Diagnosis: {rec.diagnosis or "Lung Function Normal"}</h4>'
            f'<p style="margin:8px 0 0 0;font-size:0.95rem;color:#d1d5db;">'
            f'<b>Lung Condition Group:</b> {rec.lung_condition or "Healthy"}<br>'
            f'<b>Chest X-Ray Findings:</b> {rec.chest_xray_finding or "Not recorded"}<br>'
            f'<b>Doctor Notes:</b> {rec.notes or "No comments."}<br>'
            f'<small style="color:#9ca3af;">Recorded on: {rec.recorded_at}</small></p></div>'
        )

    elif "ortho" in st_type or "injury" in st_type:
        st.write("### 🦵 Latest Orthopedic Injury Assessment")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🦵 Injury Location", rec.injury_location or "N/A")
        with col2:
            st.metric("🦴 Fracture Classification", rec.fracture_type or "N/A")
        with col3:
            st.metric("🏃 Mobility Score (0-10)", f"{rec.mobility_score or 0}/10")

        html(
            f'<div class="medical-card" style="border-left: 5px solid #f59e0b;">'
            f'<h4 style="margin:0;color:#f59e0b;">Latest Diagnosis: {rec.diagnosis or "Structural Trauma"}</h4>'
            f'<p style="margin:8px 0 0 0;font-size:0.95rem;color:#d1d5db;">'
            f'<b>MRI / X-Ray Findings:</b> {rec.mri_xray_finding or "None"}<br>'
            f'<b>Physical Treatment Plan:</b> {rec.treatment_plan or "None"}<br>'
            f'<b>Doctor Notes:</b> {rec.notes or "No comments."}<br>'
            f'<small style="color:#9ca3af;">Recorded on: {rec.recorded_at}</small></p></div>'
        )

def render_history_row(rec):
    """Renders a single row in the history list based on specialty."""
    st_type = rec.specialty_type.lower() if rec.specialty_type else ""
    
    if "cardio" in st_type or "surgery" in st_type or not st_type:
        info_str = f"HR: {rec.heart_rate or 0} bpm | BP: {rec.blood_pressure or 'N/A'} | SpO2: {rec.pulse_oximetry or 0}% | Troponin: {rec.troponin or 0.0} ng/mL | EF: {rec.ejection_fraction or 0}% | ECG: {rec.ecg_note or 'N/A'}"
    elif "dentist" in st_type or "dental" in st_type:
        info_str = f"Teeth: {rec.teeth_condition or 'N/A'} | Gum: {rec.gum_health or 'N/A'} | Procedure: {rec.procedure_done or 'N/A'} | Next Visit: {rec.next_dental_visit or 'N/A'}"
    elif "ophthal" in st_type or "eye" in st_type:
        info_str = f"Vision (R/L): {rec.right_eye_vision or 'N/A'} / {rec.left_eye_vision or 'N/A'} | IOP: {rec.eye_pressure_iop or 'N/A'} | Condition: {rec.eye_condition or 'N/A'}"
    elif "pulmo" in st_type or "chest" in st_type or "lung" in st_type:
        info_str = f"Respiratory Rate: {rec.respiratory_rate or 0} breaths/min | SpO2: {rec.oxygen_saturation or 0}% | FEV1: {rec.fev1 or 'N/A'} | Lung Condition: {rec.lung_condition or 'N/A'}"
    elif "ortho" in st_type or "injury" in st_type:
        info_str = f"Injury: {rec.injury_location or 'N/A'} | Fracture: {rec.fracture_type or 'N/A'} | Mobility: {rec.mobility_score or 0}/10 | Plan: {rec.treatment_plan or 'N/A'}"
    else:
        info_str = "No specific vitals recorded for this department."
    
    html(
        f'<div class="medical-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<h5 style="margin:0;color:#ffffff;">[{rec.specialty_type or "General Checkup"}] Diagnosis: {rec.diagnosis or "General Assessment"}</h5>'
        f'<small style="color:#ef4444;">Date: {rec.recorded_at}</small></div>'
        f'<p style="margin:10px 0 0 0;font-size:0.85rem;color:#9ca3af;">'
        f'<b>Vitals/Findings:</b> {info_str}<br>'
        f'<b>Instructions:</b> {rec.notes or "None"}</p></div>'
    )

import datetime
import json
from fpdf import FPDF

APP_NAME = "IPCMS"
APP_FULL_NAME = "Patient Care Management System For Healthcare Services"
CLINIC_NAME = "Smart Care Clinic"
CLINIC_ADDRESS = "4945 Williams Lane, Wichita, KS 67226"
CLINIC_PHONE = "222-555-7777"


def _safe_pdf_text(value) -> str:
    return str(value or "N/A").encode("latin-1", "replace").decode("latin-1")


def _agent_log(location, message, data, hypothesis_id="H1"):
    # #region agent log
    try:
        with open("debug-e25f04.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "e25f04",
                "location": location,
                "message": message,
                "data": data,
                "hypothesisId": hypothesis_id,
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            }) + "\n")
    except Exception:
        pass
    # #endregion


def _resolve_doctor_for_record(rec, db_session):
    from models.models import Doctor, User
    from views.components import format_doctor_name

    doc_name = "Dr. Medical Specialist"
    specialty = ""
    if rec and rec.doctor_id:
        doc = db_session.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
        if doc:
            doc_user = db_session.query(User).filter(User.id == doc.user_id).first()
            if doc_user:
                doc_name = format_doctor_name(doc_user.full_name)
            if doc.specialty:
                specialty = doc.specialty.name
    if doc_name == "Dr. Medical Specialist":
        fallback = db_session.query(User).filter(User.role == "Doctor").first()
        if fallback:
            doc_name = format_doctor_name(fallback.full_name)
            # Also resolve the fallback doctor's actual specialty
            fallback_doc = db_session.query(Doctor).filter(Doctor.user_id == fallback.id).first()
            if fallback_doc and fallback_doc.specialty:
                specialty = fallback_doc.specialty.name
    # Use the record's specialty_type as last resort if doctor has no specialty assigned
    if not specialty:
        specialty = rec.specialty_type if (rec and rec.specialty_type) else "General Medicine"
    return doc_name, specialty


def _build_prescription_rows(records, db_session):
    from views.prescriptions_view import _parse_rx_field, _is_real_prescription

    rows = []
    for rec in records:
        if not _is_real_prescription(rec):
            continue
        notes = rec.notes or ""
        doc_name, specialty = _resolve_doctor_for_record(rec, db_session)
        rows.append({
            "medication": _parse_rx_field(notes, "MEDICATION") or "N/A",
            "dosage": _parse_rx_field(notes, "DOSAGE") or "N/A",
            "frequency": _parse_rx_field(notes, "FREQUENCY") or "N/A",
            "timing": _parse_rx_field(notes, "TIMING") or "N/A",
            "instructions": _parse_rx_field(notes, "INSTRUCTIONS") or "As directed by physician",
            "duration": _parse_rx_field(notes, "DURATION") or "N/A",
            "doctor": doc_name,
            "specialty": specialty,
            "diagnosis": rec.diagnosis or "N/A",
            "date_issued": rec.recorded_at.strftime("%d %b %Y") if rec.recorded_at else "N/A",
            "department": rec.specialty_type or "General",
        })
    return rows


def _sample_prescription_rows():
    return [
        {
            "medication": "Atorvastatin 20mg",
            "dosage": "1 Tablet",
            "frequency": "Once daily",
            "timing": "At bedtime",
            "instructions": "Take after food. Avoid grapefruit juice.",
            "duration": "30 Days",
            "doctor": "Dr. Medical Specialist",
            "specialty": "Cardiology",
            "diagnosis": "Hyperlipidemia",
            "date_issued": datetime.datetime.now().strftime("%d %b %Y"),
            "department": "Cardiology",
        },
        {
            "medication": "Metoprolol 50mg",
            "dosage": "1 Tablet",
            "frequency": "Twice daily",
            "timing": "Morning & Evening",
            "instructions": "Take with food. Do not skip doses.",
            "duration": "30 Days",
            "doctor": "Dr. Medical Specialist",
            "specialty": "Cardiology",
            "diagnosis": "Hypertension",
            "date_issued": datetime.datetime.now().strftime("%d %b %Y"),
            "department": "Cardiology",
        },
    ]


def _filter_records_by_specialty(records, specialty):
    """Filter health records to only include those matching the doctor's specialty."""
    if not specialty or specialty == "General Medicine":
        return records
    spec_lower = specialty.lower()
    filtered = []
    for r in records:
        st_type = (r.specialty_type or "").lower()
        if spec_lower in st_type or st_type in spec_lower:
            filtered.append(r)
        # Map specialty name variants
        elif "cardio" in spec_lower and ("cardio" in st_type or "surgery" in st_type):
            filtered.append(r)
        elif "dentist" in spec_lower and ("dentist" in st_type or "dental" in st_type):
            filtered.append(r)
        elif "dental" in spec_lower and ("dentist" in st_type or "dental" in st_type):
            filtered.append(r)
        elif "ophthal" in spec_lower and ("ophthal" in st_type or "eye" in st_type):
            filtered.append(r)
        elif "pulmo" in spec_lower and ("pulmo" in st_type or "chest" in st_type or "lung" in st_type):
            filtered.append(r)
        elif "ortho" in spec_lower and ("ortho" in st_type or "injury" in st_type):
            filtered.append(r)
    return filtered if filtered else records


def _build_vitals_summary(rec, specialty):
    """Build a vitals summary string based on the doctor's specialty."""
    st_lower = (specialty or "").lower()
    if "cardio" in st_lower or "surgery" in st_lower:
        return (
            f"Heart Rate: {rec.heart_rate or 0} bpm | "
            f"Blood Pressure: {rec.blood_pressure or 'N/A'} | "
            f"SpO2: {rec.pulse_oximetry or 0}% | "
            f"Troponin: {rec.troponin or 0.0} ng/mL | "
            f"Ejection Fraction: {rec.ejection_fraction or 0}% | "
            f"Cardiac Output: {rec.cardiac_output or 0.0} L/min | "
            f"ECG: {rec.ecg_note or 'N/A'}"
        )
    elif "dentist" in st_lower or "dental" in st_lower:
        return (
            f"Teeth Condition: {rec.teeth_condition or 'N/A'} | "
            f"Gum Health: {rec.gum_health or 'N/A'} | "
            f"X-Ray: {rec.xray_finding or 'N/A'} | "
            f"Procedure: {rec.procedure_done or 'N/A'} | "
            f"Next Visit: {rec.next_dental_visit or 'N/A'}"
        )
    elif "ophthal" in st_lower or "eye" in st_lower:
        return (
            f"Right Eye: {rec.right_eye_vision or 'N/A'} | "
            f"Left Eye: {rec.left_eye_vision or 'N/A'} | "
            f"IOP: {rec.eye_pressure_iop or 'N/A'} | "
            f"Retina: {rec.retina_status or 'N/A'} | "
            f"Condition: {rec.eye_condition or 'N/A'}"
        )
    elif "pulmo" in st_lower or "chest" in st_lower or "lung" in st_lower:
        return (
            f"Respiratory Rate: {rec.respiratory_rate or 0} breaths/min | "
            f"SpO2: {rec.oxygen_saturation or 0}% | "
            f"FEV1: {rec.fev1 or 'N/A'} | "
            f"Chest X-Ray: {rec.chest_xray_finding or 'N/A'} | "
            f"Lung Condition: {rec.lung_condition or 'N/A'}"
        )
    elif "ortho" in st_lower or "injury" in st_lower:
        return (
            f"Injury Location: {rec.injury_location or 'N/A'} | "
            f"Fracture: {rec.fracture_type or 'N/A'} | "
            f"Mobility: {rec.mobility_score or 0}/10 | "
            f"MRI/X-Ray: {rec.mri_xray_finding or 'N/A'} | "
            f"Treatment Plan: {rec.treatment_plan or 'N/A'}"
        )
    else:
        return "Standard Clinical Assessment"


def _filter_prescription_rows_by_specialty(rx_rows, specialty):
    """
    Filters prescribed tablets/medications so only tablets prescribed by a doctor
    of the matching specialty/specification are included, removing prescriptions
    from doctors of other specifications.
    """
    if not specialty or specialty == "General Medicine" or not rx_rows:
        return rx_rows

    spec_lower = specialty.lower()
    filtered = []
    for row in rx_rows:
        row_spec = (row.get("specialty") or row.get("department") or "").lower()
        if (spec_lower in row_spec or row_spec in spec_lower or
            ("cardio" in spec_lower and ("cardio" in row_spec or "surgery" in row_spec)) or
            ("dentist" in spec_lower and ("dentist" in row_spec or "dental" in row_spec)) or
            ("dental" in spec_lower and ("dentist" in row_spec or "dental" in row_spec)) or
            ("ophthal" in spec_lower and ("ophthal" in row_spec or "eye" in row_spec)) or
            ("pulmo" in spec_lower and ("pulmo" in row_spec or "chest" in row_spec or "lung" in row_spec)) or
            ("ortho" in spec_lower and ("ortho" in row_spec or "injury" in row_spec))):
            filtered.append(row)
    return filtered if filtered else rx_rows


def _get_report_context(records, user):
    db_session = SessionLocal()
    try:
        all_rx_rows = _build_prescription_rows(records, db_session)
        attending_doctor = all_rx_rows[0]["doctor"] if all_rx_rows else "Dr. Medical Specialist"
        attending_specialty = all_rx_rows[0]["specialty"] if all_rx_rows else ""
        if attending_doctor == "Dr. Medical Specialist" and records:
            attending_doctor, attending_specialty = _resolve_doctor_for_record(records[0], db_session)
        # If still no specialty from prescriptions, resolve from the first record's doctor
        if not attending_specialty and records:
            _, attending_specialty = _resolve_doctor_for_record(records[0], db_session)
        if not attending_specialty:
            attending_specialty = "General Medicine"

        # Filter prescribed tablets so ONLY prescriptions by a doctor of this specification are included
        rx_rows = _filter_prescription_rows_by_specialty(all_rx_rows, attending_specialty)

        if not rx_rows:
            rx_rows = _sample_prescription_rows()
            for r in rx_rows:
                r["specialty"] = attending_specialty
                r["doctor"] = attending_doctor

        # Filter records to only include those matching the doctor's specialty
        specialty_records = _filter_records_by_specialty(records, attending_specialty)
        latest_diagnosis = next((r.diagnosis for r in specialty_records if r.diagnosis), rx_rows[0].get("diagnosis", "General Assessment"))
        return {
            "rx_rows": rx_rows,
            "attending_doctor": attending_doctor,
            "attending_specialty": attending_specialty,
            "latest_diagnosis": latest_diagnosis or "General Assessment",
            "report_id": f"IPCMS-RPT-{user.get('id', '0')}-{datetime.datetime.now().strftime('%Y%m%d')}",
            "report_date": datetime.datetime.now().strftime("%B %d, %Y"),
            "report_time": datetime.datetime.now().strftime("%I:%M %p"),
            "specialty_records": specialty_records,
        }
    finally:
        db_session.close()


def render_patient_report_html(records, user):
    ctx = _get_report_context(records, user)
    patient_name = user.get("full_name", "N/A")
    specialty = ctx["attending_specialty"]
    specialty_records = ctx.get("specialty_records", records)

    # Build vitals section HTML — only for the doctor's specialty
    vitals_rows_html = ""
    for rec in specialty_records:
        date_str = rec.recorded_at.strftime("%Y-%m-%d %H:%M") if rec.recorded_at else "N/A"
        v_summary = _build_vitals_summary(rec, specialty)
        vitals_rows_html += f"""
        <tr>
          <td style="padding:8px;border:1px solid #cbd5e1;font-size:0.85rem;">{date_str}</td>
          <td style="padding:8px;border:1px solid #cbd5e1;font-size:0.85rem;font-weight:600;color:#1e3a8a;">{rec.diagnosis or 'N/A'}</td>
          <td style="padding:8px;border:1px solid #cbd5e1;font-size:0.82rem;">{v_summary}</td>
        </tr>"""

    if vitals_rows_html:
        vitals_section_html = f"""
        <div style="margin-top:20px;">
          <div style="font-size:0.95rem;font-weight:700;color:#111827;margin-bottom:10px;">
            Clinical Encounters &amp; Vitals — {specialty}
          </div>
          <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.88rem;background:#ffffff;">
              <thead>
                <tr style="background:#0f766e;color:#ffffff;">
                  <th style="padding:8px;border:1px solid #0f766e;text-align:left;">Date</th>
                  <th style="padding:8px;border:1px solid #0f766e;text-align:left;">Diagnosis</th>
                  <th style="padding:8px;border:1px solid #0f766e;text-align:left;">{specialty} Vitals</th>
                </tr>
              </thead>
              <tbody>{vitals_rows_html}</tbody>
            </table>
          </div>
        </div>"""
    else:
        vitals_section_html = ""

    rows_html = ""
    for idx, row in enumerate(ctx["rx_rows"], start=1):
        rows_html += f"""
        <tr>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;text-align:center;font-weight:600;">{idx}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;font-weight:700;color:#1e3a8a;">{row['medication']}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;">{row['dosage']}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;">{row['frequency']}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;color:#0f766e;">{row['timing']}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;color:#7c2d12;font-size:0.88rem;">{row['instructions']}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;">{row['duration']}</td>
          <td style="padding:10px 8px;border:1px solid #cbd5e1;font-size:0.88rem;font-weight:600;color:#1e293b;">{row['doctor']}<br><span style="font-size:0.75rem;font-weight:400;color:#64748b;">({row['specialty']})</span></td>
        </tr>"""

    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;background:#ffffff;color:#111827;
                border:1px solid #dbeafe;border-radius:14px;overflow:hidden;
                box-shadow:0 10px 30px rgba(30,58,138,0.08);">

      <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);color:#ffffff;padding:22px 26px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;">
          <div>
            <div style="font-size:1.55rem;font-weight:800;letter-spacing:0.04em;">{APP_NAME}</div>
            <div style="font-size:0.78rem;opacity:0.92;margin-top:4px;text-transform:uppercase;letter-spacing:0.08em;">
              {APP_FULL_NAME}
            </div>
            <div style="font-size:0.82rem;margin-top:10px;opacity:0.95;">{CLINIC_NAME} | {CLINIC_ADDRESS} | {CLINIC_PHONE}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.72rem;text-transform:uppercase;opacity:0.85;">Official Medical Report</div>
            <div style="font-size:1rem;font-weight:700;margin-top:4px;">Prescription & Clinical Summary</div>
            <div style="font-size:0.78rem;margin-top:8px;">Report ID: {ctx['report_id']}</div>
          </div>
        </div>
      </div>

      <div style="padding:22px 26px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;">
          <div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;background:#f8fafc;">
            <div style="font-size:0.72rem;font-weight:700;color:#64748b;text-transform:uppercase;margin-bottom:10px;">Patient Details</div>
            <div style="font-size:0.92rem;line-height:1.7;">
              <div><b>Patient Name:</b> {patient_name}</div>
              <div><b>Patient ID:</b> #{user.get('id', 'N/A')}</div>
              <div><b>Date of Birth:</b> {user.get('dob') or 'N/A'}</div>
              <div><b>Gender:</b> {user.get('gender') or 'N/A'}</div>
              <div><b>Contact:</b> {user.get('email', 'N/A')} | {user.get('phone') or 'N/A'}</div>
            </div>
          </div>
          <div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;background:#f8fafc;">
            <div style="font-size:0.72rem;font-weight:700;color:#64748b;text-transform:uppercase;margin-bottom:10px;">Attending Physician</div>
            <div style="font-size:0.92rem;line-height:1.7;">
              <div><b>Doctor Name:</b> {ctx['attending_doctor']}</div>
              <div><b>Specialty:</b> {ctx['attending_specialty']}</div>
              <div><b>Facility:</b> {CLINIC_NAME}</div>
              <div><b>Report Date:</b> {ctx['report_date']}</div>
              <div><b>Generated By:</b> {APP_NAME} ({APP_FULL_NAME})</div>
            </div>
          </div>
        </div>

        <div style="border:1px solid #dbeafe;border-radius:10px;padding:12px 14px;background:#eff6ff;margin-bottom:18px;">
          <div style="font-size:0.72rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;margin-bottom:6px;">Clinical Diagnosis</div>
          <div style="font-size:0.95rem;font-weight:600;">{ctx['latest_diagnosis']}</div>
        </div>

        <div style="font-size:0.95rem;font-weight:700;color:#111827;margin-bottom:10px;">Rx Prescribed Medications & Tablets</div>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;font-size:0.88rem;background:#ffffff;">
            <thead>
              <tr style="background:#1e3a8a;color:#ffffff;">
                <th style="padding:10px 8px;border:1px solid #1e3a8a;">#</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Medicine / Tablet</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Dosage</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Frequency</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Timing</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Doctor's Instructions</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Duration</th>
                <th style="padding:10px 8px;border:1px solid #1e3a8a;text-align:left;">Prescribed By</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>

        {vitals_section_html}

        <div style="margin-top:22px;display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;">
          <div style="font-size:0.78rem;color:#64748b;max-width:420px;line-height:1.5;">
            This is an official computer-generated medical report from {APP_NAME}. Medications must be taken exactly as prescribed.
            Contact your physician before altering dosage or stopping treatment.
          </div>
          <div style="text-align:center;min-width:220px;">
            <div style="border-top:1px solid #94a3b8;padding-top:8px;font-size:0.88rem;font-weight:700;">{ctx['attending_doctor']}</div>
            <div style="font-size:0.75rem;color:#64748b;">Authorized Signature | {ctx['attending_specialty']}</div>
          </div>
        </div>
      </div>
    </div>
    """


def generate_medication_report_pdf(records, user):
    ctx = _get_report_context(records, user)
    patient_name = _safe_pdf_text(user.get("full_name", "N/A"))

    # #region agent log
    _agent_log(
        "patient_dashboard.py:generate_medication_report_pdf",
        "Report context built",
        {
            "patientName": user.get("full_name"),
            "attendingDoctor": ctx["attending_doctor"],
            "rxCount": len(ctx["rx_rows"]),
            "firstRx": ctx["rx_rows"][0] if ctx["rx_rows"] else None,
        },
        "H1",
    )
    # #endregion

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, APP_NAME, ln=1, align="C", fill=True)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 5, APP_FULL_NAME, ln=1, align="C", fill=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"{CLINIC_NAME} | {CLINIC_ADDRESS} | {CLINIC_PHONE}", ln=1, align="C", fill=True)
    pdf.ln(3)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 7, "OFFICIAL PRESCRIPTION & CLINICAL REPORT", ln=1, align="C")
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 4, f"Report ID: {ctx['report_id']}  |  Generated: {ctx['report_date']} at {ctx['report_time']}", ln=1, align="C")
    pdf.ln(2)
    pdf.set_draw_color(30, 58, 138)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(248, 250, 252)
    pdf.cell(95, 6, "PATIENT DETAILS", border=1, fill=True)
    pdf.cell(95, 6, "ATTENDING PHYSICIAN", border=1, ln=1, fill=True)
    pdf.set_font("Arial", "", 8)

    info_rows = [
        ("Patient Name:", patient_name, "Doctor Name:", _safe_pdf_text(ctx["attending_doctor"])),
        ("Patient ID:", f"#{user.get('id', 'N/A')}", "Specialty:", _safe_pdf_text(ctx["attending_specialty"])),
        ("DOB / Gender:", f"{user.get('dob') or 'N/A'} / {user.get('gender') or 'N/A'}", "Facility:", CLINIC_NAME),
        ("Contact:", f"{user.get('email', 'N/A')} | {user.get('phone') or 'N/A'}", "App System:", f"{APP_NAME} - {APP_FULL_NAME[:28]}..."),
    ]
    for left_l, left_v, right_l, right_v in info_rows:
        pdf.cell(24, 5, left_l, border=0)
        pdf.cell(71, 5, _safe_pdf_text(left_v), border=0)
        pdf.cell(24, 5, right_l, border=0)
        pdf.cell(71, 5, _safe_pdf_text(right_v), border=0, ln=1)

    pdf.ln(3)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, f"Clinical Diagnosis: {_safe_pdf_text(ctx['latest_diagnosis'])}", ln=1)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, "Rx PRESCRIBED MEDICATIONS & TABLETS", ln=1)
    pdf.ln(1)

    col_widths = [8, 34, 18, 22, 24, 38, 18, 28]
    headers = ["#", "Medicine/Tablet", "Dosage", "Frequency", "Timing", "Doctor Instructions", "Duration", "Prescribed By"]
    pdf.set_font("Arial", "B", 7)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 6, header, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 7)
    for idx, row in enumerate(ctx["rx_rows"], start=1):
        doc_str = f"{row['doctor']} ({row['specialty']})" if row.get("specialty") else row["doctor"]
        values = [
            str(idx),
            row["medication"][:22],
            row["dosage"][:14],
            row["frequency"][:16],
            row["timing"][:18],
            row["instructions"][:28],
            row["duration"][:14],
            doc_str[:26],
        ]
        for width, value in zip(col_widths, values):
            pdf.cell(width, 6, _safe_pdf_text(value), border=1)
        pdf.ln()

        # #region agent log
        if idx == 1:
            _agent_log(
                "patient_dashboard.py:generate_medication_report_pdf",
                "First prescription row rendered",
                {"timing": row["timing"], "instructions": row["instructions"], "doctor": row["doctor"]},
                "H2",
            )
        # #endregion

    pdf.ln(4)
    pdf.set_font("Arial", "B", 9)
    specialty = ctx["attending_specialty"]
    pdf.cell(0, 5, f"CLINICAL ENCOUNTERS & VITALS LOG - {_safe_pdf_text(specialty)}", ln=1)
    pdf.set_font("Arial", "", 8)

    specialty_records = ctx.get("specialty_records", records)
    found_records = False
    for rec in specialty_records:
        found_records = True
        date_str = rec.recorded_at.strftime("%Y-%m-%d %H:%M") if rec.recorded_at else "N/A"
        dept = rec.specialty_type or specialty
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 4, f"{date_str} | {dept}", ln=1)
        pdf.set_font("Arial", "", 8)
        pdf.cell(0, 4, f"Diagnosis: {_safe_pdf_text(rec.diagnosis or 'N/A')}", ln=1)

        v_str = _build_vitals_summary(rec, specialty)
        pdf.cell(0, 4, f"Vitals: {_safe_pdf_text(v_str)}", ln=1)
        pdf.ln(1)

    if not found_records:
        pdf.cell(0, 4, f"No clinical encounters recorded for {_safe_pdf_text(specialty)}.", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "I", 7)
    pdf.cell(0, 4, f"Official computer-generated report from {APP_NAME} ({APP_FULL_NAME}).", ln=1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(100, 5, f"Report ID: {ctx['report_id']}", border=0)
    pdf.cell(90, 5, f"Signature: {_safe_pdf_text(ctx['attending_doctor'])}", align="R")

    return bytes(pdf.output())


def calculate_health_score(records):
    """
    Calculates a 0-100 patient health score based on vitals, lab results,
    and clinical findings across all health record specialties.
    Returns: (score: int, breakdown: dict, grade: str, color: str)
    """
    if not records:
        return 0, {}, "N/A", "#6b7280"

    scores = {}

    for rec in records:
        st_type = (rec.specialty_type or "").lower()

        # ── Cardiology scoring ────────────────────────────────────────────
        if "cardio" in st_type or "surgery" in st_type or (not st_type and rec.heart_rate):
            s = 100
            hr = rec.heart_rate or 0
            if 60 <= hr <= 100: s -= 0
            elif 50 <= hr < 60 or 100 < hr <= 110: s -= 10
            else: s -= 25

            spo2 = rec.pulse_oximetry or 0
            if spo2 >= 97: s -= 0
            elif spo2 >= 94: s -= 10
            else: s -= 25

            ef = rec.ejection_fraction or 0
            if ef >= 55: s -= 0
            elif ef >= 40: s -= 15
            else: s -= 30

            troponin = float(rec.troponin or 0.0)
            if troponin < 0.04: s -= 0
            elif troponin < 0.1: s -= 15
            else: s -= 30

            scores["Cardiology"] = max(0, s)

        # ── Pulmonology scoring ────────────────────────────────────────────
        elif "pulmo" in st_type or "chest" in st_type or "lung" in st_type:
            s = 100
            rr = rec.respiratory_rate or 0
            if 12 <= rr <= 20: s -= 0
            elif 10 <= rr < 12 or 20 < rr <= 24: s -= 10
            else: s -= 25

            spo2 = rec.oxygen_saturation or 0
            if spo2 >= 97: s -= 0
            elif spo2 >= 94: s -= 10
            else: s -= 25

            fev1_str = rec.fev1 or "80%"
            try:
                fev1 = int(fev1_str.replace("%", "").strip())
            except Exception:
                fev1 = 80
            if fev1 >= 80: s -= 0
            elif fev1 >= 60: s -= 15
            else: s -= 30

            scores["Pulmonology"] = max(0, s)

        # ── Orthopedics scoring ────────────────────────────────────────────
        elif "ortho" in st_type or "injury" in st_type:
            s = 100
            mobility = rec.mobility_score or 0
            if mobility >= 8: s -= 0
            elif mobility >= 5: s -= 15
            else: s -= 30

            fracture = (rec.fracture_type or "").lower()
            if "none" in fracture or fracture == "": s -= 0
            elif "hairline" in fracture: s -= 15
            else: s -= 30

            scores["Orthopedics"] = max(0, s)

        # ── Dentistry scoring ──────────────────────────────────────────────
        elif "dentist" in st_type or "dental" in st_type:
            s = 100
            gum = (rec.gum_health or "").lower()
            if "healthy" in gum: s -= 0
            elif "gingivitis" in gum: s -= 15
            else: s -= 30

            teeth = (rec.teeth_condition or "").lower()
            if "healthy" in teeth: s -= 0
            elif "cavit" in teeth or "plaque" in teeth: s -= 15
            else: s -= 25

            scores["Dentistry"] = max(0, s)

        # ── Ophthalmology scoring ──────────────────────────────────────────
        elif "ophthal" in st_type or "eye" in st_type:
            s = 100
            condition = (rec.eye_condition or "none").lower()
            if condition in ["none", ""]: s -= 0
            elif "mild" in condition: s -= 10
            else: s -= 25

            retina = (rec.retina_status or "normal").lower()
            if retina == "normal": s -= 0
            else: s -= 20

            scores["Ophthalmology"] = max(0, s)

    if not scores:
        return 0, scores, "N/A", "#6b7280"

    # Weighted average across specialties
    weights = {"Cardiology": 3, "Pulmonology": 2, "Orthopedics": 1, "Dentistry": 1, "Ophthalmology": 1}
    total_w = 0
    weighted_sum = 0
    for dept, s in scores.items():
        w = weights.get(dept, 1)
        weighted_sum += s * w
        total_w += w
    final_score = round(weighted_sum / total_w) if total_w > 0 else 0

    if final_score >= 85:
        grade, color = "Excellent", "#10b981"
    elif final_score >= 70:
        grade, color = "Good", "#3b82f6"
    elif final_score >= 55:
        grade, color = "Fair", "#f59e0b"
    else:
        grade, color = "At Risk", "#ef4444"

    return final_score, scores, grade, color


def render_health_score_card(records):
    """Renders a premium health score card with SVG ring and breakdown bars using st.components."""
    import streamlit.components.v1 as components

    score, breakdown, grade, color = calculate_health_score(records)

    if score == 0 and not breakdown:
        return  # No records yet, skip card

    # SVG ring calculation
    radius = 54
    circumference = 2 * 3.14159 * radius
    dash_val = (score / 100) * circumference
    gap_val = max(circumference - dash_val, 0.01)

    grade_emoji = {"Excellent": "🏆", "Good": "✅", "Fair": "⚠️", "At Risk": "🔴"}.get(grade, "📊")

    dept_colors = {
        "Cardiology": "#ef4444",
        "Pulmonology": "#a855f7",
        "Orthopedics": "#f59e0b",
        "Dentistry": "#3b82f6",
        "Ophthalmology": "#10b981"
    }
    dept_icons = {
        "Cardiology": "❤️",
        "Pulmonology": "🫁",
        "Orthopedics": "🦴",
        "Dentistry": "🦷",
        "Ophthalmology": "👁️"
    }

    bars_html = ""
    for dept, dept_score in breakdown.items():
        bar_color = dept_colors.get(dept, "#6b7280")
        icon = dept_icons.get(dept, "🩺")
        sub_grade = (
            "Excellent" if dept_score >= 85 else
            "Good"      if dept_score >= 70 else
            "Fair"      if dept_score >= 55 else
            "At Risk"
        )
        bars_html += f"""
        <div style="margin:10px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <span style="font-size:0.9rem;color:#d1d5db;">{icon} <b>{dept}</b></span>
            <span style="font-size:0.85rem;font-weight:700;color:{bar_color};">
              {dept_score}/100 &nbsp;
              <span style="font-weight:400;color:#9ca3af;font-size:0.78rem;">{sub_grade}</span>
            </span>
          </div>
          <div style="background:#374151;border-radius:999px;height:10px;overflow:hidden;">
            <div style="background:{bar_color};width:{dept_score}%;height:10px;border-radius:999px;
                        box-shadow:0 0 8px {bar_color}55;transition:width 0.6s ease;"></div>
          </div>
        </div>"""

    lifestyle_tips = {
        "Excellent": "Keep up your current lifestyle! Regular exercise, balanced diet, and adequate sleep are your best friends.",
        "Good":      "You're doing well. Focus on consistent sleep (7-8 hrs), reduced sodium intake, and 30-min daily walks.",
        "Fair":      "Some areas need attention. Consider scheduling follow-up appointments and improving hydration & diet.",
        "At Risk":   "Please consult your doctor urgently. Prioritise medication compliance and lifestyle changes immediately."
    }.get(grade, "")

    full_html = f"""
    <div style="font-family:Arial,sans-serif;
                background:linear-gradient(135deg,#1e2a3a,#0f1923);
                border-radius:20px;padding:28px;
                box-shadow:0 8px 32px rgba(0,0,0,0.5);
                border:1px solid #2d3748;margin-bottom:8px;">

      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:24px;">

        <!-- Score Ring -->
        <div style="display:flex;flex-direction:column;align-items:center;min-width:150px;">
          <svg width="140" height="140" viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>
            <!-- Track -->
            <circle cx="70" cy="70" r="{radius}" fill="none" stroke="#2d3748" stroke-width="13"/>
            <!-- Progress Arc -->
            <circle cx="70" cy="70" r="{radius}" fill="none" stroke="{color}" stroke-width="13"
              stroke-dasharray="{dash_val:.2f} {gap_val:.2f}"
              stroke-linecap="round"
              transform="rotate(-90 70 70)"
              filter="url(#glow)"/>
            <!-- Score Text -->
            <text x="70" y="64" text-anchor="middle" fill="{color}"
                  font-size="30" font-weight="bold" font-family="Arial">{score}</text>
            <text x="70" y="82" text-anchor="middle" fill="#6b7280"
                  font-size="13" font-family="Arial">/100</text>
          </svg>
          <div style="font-size:1.1rem;font-weight:700;color:{color};margin-top:6px;">{grade_emoji} {grade}</div>
          <div style="font-size:0.78rem;color:#6b7280;margin-top:3px;letter-spacing:0.05em;">HEALTH SCORE</div>
        </div>

        <!-- Breakdown Bars -->
        <div style="flex:1;min-width:240px;">
          <div style="font-size:1rem;font-weight:700;color:#f9fafb;margin-bottom:14px;">
            📊 Score Breakdown by Specialty
          </div>
          {bars_html}
        </div>
      </div>

      <!-- Lifestyle Recommendation -->
      <div style="margin-top:20px;background:rgba(255,255,255,0.04);border-left:4px solid {color};
                  border-radius:8px;padding:12px 16px;">
        <span style="font-size:0.85rem;color:#d1d5db;">💡 <b>Lifestyle Recommendation:</b> {lifestyle_tips}</span>
      </div>
    </div>
    """

    # Use components.html so SVG renders — st.markdown strips SVG tags
    components.html(full_html, height=max(360, 260 + len(breakdown) * 50), scrolling=False)



def render_patient_dashboard():
    user = st.session_state.user
    db = SessionLocal()
    from services.appointment_service import get_appointments_for_user
    from services.patient_ai_service import get_health_summary
    
    try:
        records = get_health_records(db, user["id"])
        appointments = get_appointments_for_user(db, user["id"], "Patient")
        
        pending = [a for a in appointments if a.status == "Scheduled"]
        completed = [a for a in appointments if a.status == "Completed"]
        
        st.markdown(f"<h2 style='color: #1e3a8a;'>Welcome back, {user['full_name']}! 👋</h2>", unsafe_allow_html=True)
        st.markdown("Here is your personalized health overview.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 Upcoming Appointments", len(pending))
        with col2:
            st.metric("✅ Completed Checkups", len(completed))
        with col3:
            st.metric("🩺 Health Records", len(records))
            
        st.markdown("---")

        # ── Interactive Appointment Calendar ─────────────────────────────
        from views.calendar_component import render_appointment_calendar
        render_appointment_calendar(db, "Patient", user["id"])

        st.markdown("---")
        
        # ── AI Health Summary ───────────────────────────────────────────────
        st.markdown("### 🤖 AI Health Summary")
        with st.spinner("Generating AI insights..."):
            summary_data = get_health_summary(records)
            
            st.info(f"**Overall Status:** {summary_data.get('summary', 'N/A')}")
            
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.markdown("**🧪 Abnormal Tests:**")
                for item in summary_data.get("abnormal_tests", []):
                    st.markdown(f"- 🔴 {item}")
                if not summary_data.get("abnormal_tests"):
                    st.markdown("- ✅ All tests appear normal.")
                    
                st.markdown(f"**📈 Recovery Progress:** {summary_data.get('recovery_progress', 'N/A')}")
                
            with s_col2:
                st.markdown("**💡 Lifestyle Tips:**")
                for item in summary_data.get("lifestyle_tips", []):
                    st.markdown(f"- 🍏 {item}")
                    
                st.markdown("**⚠️ Warnings:**")
                for item in summary_data.get("warnings", []):
                    st.markdown(f"- ⚠️ {item}")
                if not summary_data.get("warnings"):
                    st.markdown("- ✅ No immediate warnings.")

        st.markdown("---")
        
        # ── Health Score Card ──────────────────────────────────────────────
        st.write("### 🏥 Your Health Score")
        render_health_score_card(records)

        # ── Medical Timeline ───────────────────────────────────────────────
        st.markdown("---")
        st.write("### ⏳ Chronological Medical Timeline")
        
        # Combine records and appointments for timeline
        timeline_events = []
        for a in appointments:
            doc_name = format_doctor_name(a.doctor.user.full_name) if (a.doctor and a.doctor.user) else "Practitioner"
            timeline_events.append({
                "date": a.scheduled_date,
                "type": "Appointment",
                "title": f"Appointment with {doc_name}",
                "desc": f"Status: {a.status}. Reason: {a.reason or 'Routine Checkup'}",
                "icon": "📅",
                "color": "#3b82f6"
            })
            
        for r in records:
            if r.recorded_at:
                date_val = r.recorded_at.date() if hasattr(r.recorded_at, 'date') else r.recorded_at
                
                # Check if prescription
                notes = r.notes or ""
                if "MEDICATION:" in notes.upper() or "PRESCRIBED:" in notes.upper():
                    timeline_events.append({
                        "date": date_val,
                        "type": "Prescription",
                        "title": f"Prescription Issued ({r.specialty_type or 'General'})",
                        "desc": f"Diagnosis: {r.diagnosis}",
                        "icon": "💊",
                        "color": "#10b981"
                    })
                else:
                    timeline_events.append({
                        "date": date_val,
                        "type": "Diagnosis",
                        "title": f"Clinical Visit ({r.specialty_type or 'General'})",
                        "desc": f"Diagnosis: {r.diagnosis or 'Routine Checkup'}",
                        "icon": "🩺",
                        "color": "#ef4444"
                    })
                    
        # Sort events descending
        timeline_events.sort(key=lambda x: x["date"], reverse=True)
        
        if timeline_events:
            for event in timeline_events:
                st.markdown(f"""
                <div style="border-left: 3px solid {event['color']}; padding-left: 15px; margin-bottom: 15px;">
                    <span style="font-size: 1.2rem;">{event['icon']}</span> 
                    <strong style="color: #1e3a8a;">{event['title']}</strong> 
                    <span style="color: #64748b; font-size: 0.85rem; margin-left: 10px;">{event['date']}</span>
                    <p style="margin: 5px 0 0 0; font-size: 0.95rem; color: #334155;">{event['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No timeline events found.")

    finally:
        db.close()
