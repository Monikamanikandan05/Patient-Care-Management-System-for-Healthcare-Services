import streamlit as st
from core.database import SessionLocal
from models.models import User, HealthRecord, Doctor
from views.components import html

def render_lab_reports_view():
    st.write("### 🧪 Laboratory & Diagnostic Reports")
    user = st.session_state.user
    db = SessionLocal()
    try:
        specialty_name = ""
        if user["role"] == "Doctor":
            doc_profile = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
            if doc_profile and doc_profile.specialty:
                specialty_name = doc_profile.specialty.name
                icon = doc_profile.specialty.icon or "🩺"
                st.info(f"{icon} Doctor Specialty: **{specialty_name}** — Displaying ONLY lab reports for {specialty_name}.")

        patients = db.query(User).filter(User.role == 'Patient').all()
        
        if user["role"] == "Patient":
            selected_patient_id = user["id"]
            patient_name = user["full_name"]
        else:
            if not patients:
                st.info("No patient registries found.")
                return
            patient_map = {p.full_name: p.id for p in patients}
            selected_patient_name = st.selectbox("Select Patient to View Lab Reports", list(patient_map.keys()), key="lab_reports_pat_sel")
            selected_patient_id = patient_map[selected_patient_name]
            patient_name = selected_patient_name

        records = db.query(HealthRecord).filter(HealthRecord.patient_id == selected_patient_id).order_by(HealthRecord.recorded_at.desc()).all()

        # For Doctor role: Delete / filter out all other specialty lab records! Show ONLY doctor's specialty.
        if user["role"] == "Doctor" and specialty_name:
            sn_check = specialty_name.lower()
            records = [
                r for r in records 
                if r.specialty_type and (sn_check in r.specialty_type.lower() or r.specialty_type.lower() in sn_check)
            ]

        st.markdown(f"##### Diagnostic & Lab Report Panels (**Patient: {patient_name}**) ")

        sn = specialty_name.lower() if specialty_name else ""

        # Render ONLY the doctor's specific specialty lab report panel
        if user["role"] == "Doctor":
            if "cardio" in sn or "surgery" in sn:
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #ef4444;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#ef4444;">❤️ High-Sensitivity Cardiac Troponin & ECG Assessment</h4>
                        <span style="background:#fee2e2; color:#b91c1c; border:1px solid #fecaca; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                        • <b>Cardiac Troponin-T:</b> 0.015 ng/mL (Normal &lt; 0.014 ng/mL - Stable)<br>
                        • <b>Ejection Fraction (EF):</b> 55% (Normal Range: 55-70%)<br>
                        • <b>Cardiac Output:</b> 5.0 L/min (Normal: 4.0-8.0 L/min)<br>
                        • <b>ECG Rhythm Strip:</b> Normal Sinus Rhythm, no acute ST elevation
                    </p>
                </div>
                """)

            elif "dentist" in sn or "dental" in sn:
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #3b82f6;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#3b82f6;">🦷 Digital Dental Radiography & Panoramic X-Ray Report</h4>
                        <span style="background:#dbeafe; color:#1e40af; border:1px solid #bfdbfe; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                        • <b>Panoramic X-Ray Finding:</b> No periapical radiolucency observed; minor enamel caries on lower molar.<br>
                        • <b>Periodontal Bone Level:</b> Normal alveolar bone height (&gt; 90%).<br>
                        • <b>TMJ Assessment:</b> Bilateral condylar head alignment intact.
                    </p>
                </div>
                """)

            elif "ophthal" in sn or "eye" in sn:
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #f59e0b;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#f59e0b;">👁️ Intraocular Pressure (IOP) Tonometry & Glaucoma Scan</h4>
                        <span style="background:#fef3c7; color:#92400e; border:1px solid #fde68a; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                        • <b>Right Eye (OD) IOP:</b> 14 mmHg (Normal: 10-21 mmHg)<br>
                        • <b>Left Eye (OS) IOP:</b> 15 mmHg (Normal: 10-21 mmHg)<br>
                        • <b>OCT Retinal Thickness:</b> 265 µm (Normal contours intact)
                    </p>
                </div>
                """)

            elif "pulmo" in sn or "chest" in sn or "lung" in sn:
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #3b82f6;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#3b82f6;">🫁 Spirometry & Pulmonary Function Test (PFT) Panel</h4>
                        <span style="background:#dbeafe; color:#1e40af; border:1px solid #bfdbfe; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                        • <b>FEV1 (Forced Expiratory Volume 1s):</b> 3.2 L (84% of predicted)<br>
                        • <b>FVC (Forced Vital Capacity):</b> 4.1 L (88% of predicted)<br>
                        • <b>Chest X-Ray Finding:</b> Clear lung parenchyma; no focal consolidation or effusion.
                    </p>
                </div>
                """)

            elif "ortho" in sn or "injury" in sn:
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #f59e0b;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#f59e0b;">🦴 Musculoskeletal MRI Radiology Report</h4>
                        <span style="background:#fef3c7; color:#92400e; border:1px solid #fde68a; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                        • <b>MRI Finding:</b> Intact joint articular cartilage; mild Grade 1 patellar tendon strain.<br>
                        • <b>Joint Space:</b> Preserved femorotibial joint gap.<br>
                        • <b>Mobility Assessment Score:</b> 7/10
                    </p>
                </div>
                """)
            else:
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #a855f7;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#a855f7;">🧪 Complete Blood Count (CBC) Panel</h4>
                        <span style="background:#f3e8ff; color:#6b21a8; border:1px solid #e9d5ff; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                        • <b>WBC Count:</b> 6.5 x10^3/uL (Normal: 4.5-11.0)<br>
                        • <b>RBC Count:</b> 4.8 x10^6/uL (Normal: 4.3-5.9)<br>
                        • <b>Hemoglobin:</b> 14.2 g/dL (Normal: 13.5-17.5)
                    </p>
                </div>
                """)

        else:
            # Patient / Admin view
            html(f"""
            <div class="medical-card" style="border-left: 4px solid #a855f7;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;color:#a855f7;">🧪 Complete Blood Count (CBC) Panel</h4>
                    <span style="background:#f3e8ff; color:#6b21a8; border:1px solid #e9d5ff; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                </div>
                <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                    • <b>WBC Count:</b> 6.5 x10^3/uL (Normal: 4.5-11.0)<br>
                    • <b>RBC Count:</b> 4.8 x10^6/uL (Normal: 4.3-5.9)<br>
                    • <b>Hemoglobin:</b> 14.2 g/dL (Normal: 13.5-17.5)<br>
                    • <b>Platelets:</b> 250 x10^3/uL (Normal: 150-450)
                </p>
            </div>
            
            <div class="medical-card" style="border-left: 4px solid #3b82f6;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;color:#3b82f6;">🧪 Comprehensive Lipid Metabolic Panel</h4>
                    <span style="background:#dbeafe; color:#1e40af; border:1px solid #bfdbfe; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Completed</span>
                </div>
                <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;line-height:1.8;">
                    • <b>Total Cholesterol:</b> 185 mg/dL (Normal &lt; 200)<br>
                    • <b>Triglycerides:</b> 130 mg/dL (Normal &lt; 150)<br>
                    • <b>HDL (Good):</b> 52 mg/dL (Optimal &gt; 40)<br>
                    • <b>LDL (Bad):</b> 107 mg/dL (Normal &lt; 100 - Borderline)
                </p>
            </div>
            """)

        # Display registered diagnostic records matching doctor's specialty
        if records:
            st.markdown(f"##### 📜 Registered Diagnostic Findings ({specialty_name or 'All'})")
            for rec in records:
                rec_st = rec.specialty_type or "General"
                rec_date = rec.recorded_at.strftime("%Y-%m-%d %H:%M") if rec.recorded_at else "N/A"
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #22c55e; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h5 style="margin:0;color:#22c55e;">🩺 [{rec_st}] Diagnostic Finding Report</h5>
                        <small style="color:#64748b;">Date: {rec_date}</small>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.85rem;color:#cbd5e1;line-height:1.8;">
                        🔬 <b>Diagnosis:</b> {rec.diagnosis or "Stable clinical presentation"}<br>
                        📝 <b>Notes:</b> {rec.notes or "None"}
                    </p>
                </div>
                """)
                if st.button("🗑️ Delete Report", key=f"del_lab_{rec.id}", use_container_width=False):
                    try:
                        db.query(HealthRecord).filter(HealthRecord.id == rec.id).delete()
                        db.commit()
                        st.success("Report deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete report: {e}")

    finally:
        db.close()
