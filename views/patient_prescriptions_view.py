import streamlit as st
from core.database import SessionLocal
from models.models import HealthRecord, Doctor, User
from views.components import format_doctor_name
from views.prescriptions_view import _is_real_prescription, _parse_rx_field
from services.patient_ai_service import get_medicine_explanation

def render_patient_prescriptions_view():
    st.write("### 💊 Unified Prescriptions Dashboard")
    st.markdown("View all your prescriptions organized by medical department.")
    
    user = st.session_state.user
    db = SessionLocal()
    try:
        records = (
            db.query(HealthRecord)
            .filter(HealthRecord.patient_id == user["id"])
            .order_by(HealthRecord.recorded_at.desc())
            .all()
        )
        rx_records = [r for r in records if _is_real_prescription(r)]
        
        if not rx_records:
            st.info("No prescriptions found on your record.")
            return

        # Group by department by resolving the doctor's specialty
        grouped_rx = {}
        for rec in rx_records:
            doc_profile = db.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
            if doc_profile and doc_profile.specialty:
                dept = doc_profile.specialty.name
            else:
                dept = rec.specialty_type or "General Medicine"
                
            if dept not in grouped_rx:
                grouped_rx[dept] = []
            grouped_rx[dept].append((rec, doc_profile))
                  # Helper function to render a prescription card to avoid duplicate keys
        def _render_prescription_card(db_session, rec, doc_profile, tab_name):
            doc_user = db_session.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
            doc_name = format_doctor_name(doc_user.full_name) if doc_user else "Dr. Medical Specialist"
            
            notes = rec.notes or ""
            medication = _parse_rx_field(notes, "MEDICATION") or "N/A"
            dosage = _parse_rx_field(notes, "DOSAGE") or "N/A"
            frequency = _parse_rx_field(notes, "FREQUENCY") or "N/A"
            timing = _parse_rx_field(notes, "TIMING") or "N/A"
            duration = _parse_rx_field(notes, "DURATION") or "N/A"
            instructions = _parse_rx_field(notes, "INSTRUCTIONS") or "As directed"
            date_str = rec.recorded_at.strftime('%d %b %Y') if rec.recorded_at else "N/A"
            
            status = "Active" if "Days" in duration else "Completed"
            
            key_suffix = f"{rec.id}_{tab_name.replace(' ', '_').lower()}"
            
            with st.expander(f"💊 {medication} - Prescribed on {date_str} ({status})"):
                st.markdown(f"**👨‍⚕️ Doctor:** {doc_name} ({tab_name if tab_name != 'All Prescriptions' else (doc_profile.specialty.name if doc_profile and doc_profile.specialty else rec.specialty_type or 'General Medicine')})")
                st.markdown(f"**🩺 Diagnosis:** {rec.diagnosis or 'N/A'}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**🧪 Dosage:** {dosage}")
                    st.write(f"**🔄 Frequency:** {frequency}")
                    st.write(f"**⏰ Timing:** {timing}")
                with col2:
                    st.write(f"**📅 Duration:** {duration}")
                    st.write(f"**📌 Status:** {status}")
                    
                # Vitals Checkups
                st.markdown("---")
                st.markdown("**📊 Vitals Recorded During Visit:**")
                vitals_col1, vitals_col2, vitals_col3 = st.columns(3)
                with vitals_col1:
                    st.write(f"**❤️ Heart Rate:** {rec.heart_rate or 'N/A'} bpm")
                    st.write(f"**🩸 Blood Pressure:** {rec.blood_pressure or 'N/A'}")
                with vitals_col2:
                    st.write(f"**🌬️ SpO2:** {rec.pulse_oximetry or 'N/A'}%")
                    st.write(f"**🌡️ Blood Sugar:** {getattr(rec, 'blood_sugar', 'N/A') or 'N/A'} mg/dL")
                with vitals_col3:
                    st.write(f"**⚖️ Weight:** {getattr(rec, 'weight', 'N/A') or 'N/A'} kg")
                    st.write(f"**🍔 Cholesterol:** {getattr(rec, 'cholesterol', 'N/A') or 'N/A'} mg/dL")
                    
                st.markdown("---")
                st.info(f"**📋 Instructions:** {instructions}")
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("🤖 AI Medicine Assistant", key=f"ai_btn_{key_suffix}", use_container_width=True):
                        st.session_state[f"show_ai_{key_suffix}"] = not st.session_state.get(f"show_ai_{key_suffix}", False)
        
                with btn_col2:
                    if st.button("🔔 Set Smart Reminder", key=f"remind_btn_{key_suffix}", use_container_width=True):
                        st.success("Reminder configured successfully.")
        
                # Render AI explanation if toggled
                if st.session_state.get(f"show_ai_{key_suffix}"):
                    with st.spinner("Analyzing medicine..."):
                        explanation = get_medicine_explanation(medication, dosage, instructions)
                        st.success(f"**Purpose:** {explanation.get('purpose', 'N/A')}")
                        st.warning(f"**Side Effects:** {explanation.get('side_effects', 'N/A')}")
                        st.info(f"**Precautions:** {explanation.get('precautions', 'N/A')}")
                        st.error(f"**Food Interactions:** {explanation.get('food_interactions', 'N/A')}")

        # Display Tabs for Departments
        departments = ["All Prescriptions"] + list(grouped_rx.keys())
        tabs = st.tabs(departments)
        
        # Render All Prescriptions
        with tabs[0]:
            st.markdown("#### All Prescriptions")
            for rec in rx_records:
                doc_profile = db.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
                _render_prescription_card(db, rec, doc_profile, "All Prescriptions")
        
        # Render department specific prescriptions
        for idx, dept in enumerate(list(grouped_rx.keys()), start=1):
            with tabs[idx]:
                st.markdown(f"#### {dept} Prescriptions")
                for rec, doc_profile in grouped_rx[dept]:
                    _render_prescription_card(db, rec, doc_profile, dept)
                                
    finally:
        db.close()

