import streamlit as st
from core.database import SessionLocal
from models.models import User, HealthRecord, Doctor
from services.health_service import add_health_record
from views.components import html, heartbeat_metric
from views.doctor_portal import _render_vitals_form

def render_vitals_view():
    st.write("### ❤️ Vital Signs Tracking & Clinical History")
    user = st.session_state.user
    db = SessionLocal()
    try:
        specialty_name = ""
        doc_profile = None
        
        if user["role"] == "Doctor":
            doc_profile = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
            if doc_profile and doc_profile.specialty:
                specialty_name = doc_profile.specialty.name
                icon = doc_profile.specialty.icon or "🩺"
                st.info(f"{icon} Doctor Specialty: **{specialty_name}** — Showing ONLY vital sign records for {specialty_name}.")
            else:
                st.info("🩺 Practitioner Access: Displaying vital parameters.")

        patients = db.query(User).filter(User.role == 'Patient').all()
        
        if user["role"] == "Patient":
            selected_patient_id = user["id"]
            patient_name = user["full_name"]
        else:
            if not patients:
                st.info("No patient registries found.")
                return
            patient_map = {p.full_name: p.id for p in patients}
            selected_patient_name = st.selectbox("Select Patient Profile", list(patient_map.keys()), key="vitals_page_pat_sel")
            selected_patient_id = patient_map[selected_patient_name]
            patient_name = selected_patient_name

        records = db.query(HealthRecord).filter(HealthRecord.patient_id == selected_patient_id).order_by(HealthRecord.recorded_at.desc()).all()

        # For Doctor role: Delete / filter out all other specialty vital records! Show ONLY doctor's specialty.
        if user["role"] == "Doctor" and specialty_name:
            sn_check = specialty_name.lower()
            records = [
                r for r in records 
                if r.specialty_type and (sn_check in r.specialty_type.lower() or r.specialty_type.lower() in sn_check)
            ]

        # Record form for doctor
        if user["role"] == "Doctor":
            st.markdown(f"#### 📝 Record Vital Signs for **{patient_name}** ({specialty_name or 'Clinical'})")
            with st.expander("➕ Click to Enter New Vital Measurements", expanded=True):
                spec_for_form = specialty_name or "Cardiology"
                vitals_data = _render_vitals_form(spec_for_form)
                diagnosis = st.text_input("Diagnosis / Clinical Summary", key="vitals_view_diag", placeholder="e.g. Clinical assessment, vital signs stable...")
                notes = st.text_area("Prescription & Notes", key="vitals_view_notes", placeholder="Treatment plan, notes...")
                if st.button("💾 Submit Vital Measurements", key="vitals_view_save_btn", use_container_width=True):
                    add_health_record(
                        db=db,
                        patient_id=selected_patient_id,
                        doctor_user_id=user["id"],
                        specialty_type=spec_for_form,
                        diagnosis=diagnosis,
                        notes=notes,
                        **vitals_data
                    )
                    st.success(f"✅ Vital signs recorded for **{patient_name}**!")
                    st.rerun()

        st.markdown("---")
        st.markdown(f"##### 📊 Vital History ({patient_name} — {specialty_name or 'Clinical'})")

        if not records:
            st.info(f"No {specialty_name} vital records found for {patient_name}.")
            return

        latest = records[0]
        st_type = (latest.specialty_type or specialty_name or "General").lower()

        col1, col2 = st.columns(2)
        with col1:
            if "cardio" in st_type or "surgery" in st_type:
                heartbeat_metric("❤️ Heart Rate", f"{latest.heart_rate or 72} bpm")
                st.metric("🩸 Blood Pressure", latest.blood_pressure or "120/80")
                st.metric("🧪 Troponin Level", f"{latest.troponin or 0.015} ng/mL")
            elif "dentist" in st_type or "dental" in st_type:
                st.metric("🦷 Teeth Condition", latest.teeth_condition or "Healthy")
                st.metric("👄 Gum Health", latest.gum_health or "Healthy")
                st.metric("🛠️ Procedure Done", latest.procedure_done or "Scaling")
            elif "ophthal" in st_type or "eye" in st_type:
                st.metric("👁️ Vision (Right/Left)", f"{latest.right_eye_vision or '6/6'} / {latest.left_eye_vision or '6/6'}")
                st.metric("👁️ IOP Pressure", latest.eye_pressure_iop or "14 mmHg")
                st.metric("🔬 Retina Status", latest.retina_status or "Normal")
            elif "pulmo" in st_type or "chest" in st_type or "lung" in st_type:
                st.metric("🌬️ Respiratory Rate", f"{latest.respiratory_rate or 16} br/min")
                st.metric("🫁 SpO2 Oxygen", f"{latest.oxygen_saturation or latest.pulse_oximetry or 98}%")
                st.metric("📊 FEV1 Spirometry", latest.fev1 or "82%")
            elif "ortho" in st_type or "injury" in st_type:
                st.metric("🦵 Injury Location", latest.injury_location or "Knee")
                st.metric("🦴 Fracture Type", latest.fracture_type or "None")
                st.metric("🏃 Mobility Score", f"{latest.mobility_score or 7}/10")
            else:
                heartbeat_metric("❤️ Heart Rate", f"{latest.heart_rate or 72} bpm")
                st.metric("🩸 Blood Pressure", latest.blood_pressure or "120/80")

        with col2:
            if "cardio" in st_type or "surgery" in st_type:
                st.metric("⚡ Ejection Fraction", f"{latest.ejection_fraction or 55}%")
                st.metric("🌬️ SpO2 Oxygen", f"{latest.pulse_oximetry or latest.oxygen_saturation or 98}%")
                st.metric("📈 ECG Rhythm", latest.ecg_note or "Normal Sinus Rhythm")
            elif "dentist" in st_type or "dental" in st_type:
                st.metric("🔍 X-Ray Finding", latest.xray_finding or "Normal")
                st.metric("📅 Next Visit", latest.next_dental_visit or "6 months")
            elif "ophthal" in st_type or "eye" in st_type:
                st.metric("🔍 Eye Condition", latest.eye_condition or "None")
            elif "pulmo" in st_type or "chest" in st_type or "lung" in st_type:
                st.metric("🩺 Lung Condition", latest.lung_condition or "Healthy")
                st.metric("🔬 Chest X-Ray", latest.chest_xray_finding or "Clear")
            elif "ortho" in st_type or "injury" in st_type:
                st.metric("🩹 Treatment Plan", latest.treatment_plan or "Physiotherapy")
                st.metric("🔬 MRI/X-Ray Finding", latest.mri_xray_finding or "Clear")
            else:
                st.metric("⚡ Ejection Fraction", f"{latest.ejection_fraction or 55}%")

        st.markdown("---")
        st.markdown(f"##### 📜 Recorded {specialty_name or 'Specialty'} Vitals Log")

        for r in records:
            rec_st = r.specialty_type or "General"
            rec_st_lower = rec_st.lower()
            rec_date = r.recorded_at.strftime("%Y-%m-%d %H:%M") if r.recorded_at else "N/A"

            vitals_summary = []
            if "cardio" in rec_st_lower or "surgery" in rec_st_lower:
                if r.heart_rate: vitals_summary.append(f"HR: {r.heart_rate} bpm")
                if r.blood_pressure: vitals_summary.append(f"BP: {r.blood_pressure}")
                if r.troponin: vitals_summary.append(f"Troponin: {r.troponin} ng/mL")
                if r.ejection_fraction: vitals_summary.append(f"EF: {r.ejection_fraction}%")
                if r.ecg_note: vitals_summary.append(f"ECG: {r.ecg_note}")
            elif "dentist" in rec_st_lower or "dental" in rec_st_lower:
                if r.teeth_condition: vitals_summary.append(f"Teeth: {r.teeth_condition}")
                if r.gum_health: vitals_summary.append(f"Gums: {r.gum_health}")
                if r.procedure_done: vitals_summary.append(f"Procedure: {r.procedure_done}")
                if r.xray_finding: vitals_summary.append(f"X-Ray: {r.xray_finding}")
            elif "ophthal" in rec_st_lower or "eye" in rec_st_lower:
                if r.right_eye_vision: vitals_summary.append(f"Vision R/L: {r.right_eye_vision}/{r.left_eye_vision}")
                if r.eye_pressure_iop: vitals_summary.append(f"IOP: {r.eye_pressure_iop}")
                if r.eye_condition: vitals_summary.append(f"Condition: {r.eye_condition}")
            elif "pulmo" in rec_st_lower or "chest" in rec_st_lower or "lung" in rec_st_lower:
                if r.respiratory_rate: vitals_summary.append(f"RR: {r.respiratory_rate} br/min")
                if r.oxygen_saturation: vitals_summary.append(f"SpO2: {r.oxygen_saturation}%")
                if r.fev1: vitals_summary.append(f"FEV1: {r.fev1}")
                if r.lung_condition: vitals_summary.append(f"Condition: {r.lung_condition}")
            elif "ortho" in rec_st_lower or "injury" in rec_st_lower:
                if r.injury_location: vitals_summary.append(f"Location: {r.injury_location}")
                if r.fracture_type: vitals_summary.append(f"Fracture: {r.fracture_type}")
                if r.mobility_score is not None: vitals_summary.append(f"Mobility: {r.mobility_score}/10")
                if r.treatment_plan: vitals_summary.append(f"Plan: {r.treatment_plan}")
            else:
                if r.heart_rate: vitals_summary.append(f"HR: {r.heart_rate} bpm")
                if r.blood_pressure: vitals_summary.append(f"BP: {r.blood_pressure}")

            summary_str = " &nbsp;|&nbsp; ".join(vitals_summary) if vitals_summary else "Standard vitals"

            html(f"""
            <div class="medical-card" style="border-left: 4px solid #ef4444; margin-bottom: 12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h5 style="margin:0;color:#ffffff;">🩺 [{rec_st}] Vital Signs Record</h5>
                    <small style="color:#ef4444;">Recorded: {rec_date}</small>
                </div>
                <p style="margin:8px 0 0 0;font-size:0.85rem;color:#cbd5e1;line-height:1.8;">
                    📊 <b>Vitals:</b> {summary_str}<br>
                    🔬 <b>Diagnosis:</b> {r.diagnosis or "N/A"}<br>
                    📝 <b>Notes:</b> {r.notes or "None"}
                </p>
            </div>
            """)
            if st.button("🗑️ Delete Record", key=f"del_vital_{r.id}", use_container_width=False):
                try:
                    db.query(HealthRecord).filter(HealthRecord.id == r.id).delete()
                    db.commit()
                    st.success("Record deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete record: {e}")
    finally:
        db.close()
