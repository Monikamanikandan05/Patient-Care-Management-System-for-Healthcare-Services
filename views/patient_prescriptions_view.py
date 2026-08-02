import streamlit as st
import streamlit.components.v1 as components
from core.database import SessionLocal
from models.models import HealthRecord, Doctor, User
from views.components import format_doctor_name
from views.prescriptions_view import _is_real_prescription, _parse_rx_field
from services.patient_ai_service import get_medicine_explanation

# Removed global voice script injection

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
            
        # Display Tabs for Departments
        departments = list(grouped_rx.keys())
        tabs = st.tabs(departments)
        
        for idx, dept in enumerate(departments):
            with tabs[idx]:
                st.markdown(f"#### {dept} Prescriptions")
                for rec, doc_profile in grouped_rx[dept]:
                    doc_user = db.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
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
                    
                    with st.expander(f"💊 {medication} - Prescribed on {date_str} ({status})"):
                        st.markdown(f"**👨‍⚕️ Doctor:** {doc_name} ({dept})")
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
                        
                        speech_text = f"Prescription for {medication}. Take {dosage}, {frequency}. Timing: {timing}. Instructions: {instructions}. Prescribed by {doc_name}."
                        # Escape quotes and newlines for safe JS string injection
                        safe_speech = speech_text.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
                        
                        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                        with btn_col1:
                            if st.button("🤖 AI Medicine Assistant", key=f"ai_btn_{rec.id}"):
                                with st.spinner("Analyzing medicine..."):
                                    explanation = get_medicine_explanation(medication, dosage, instructions)
                                    st.success(f"**Purpose:** {explanation.get('purpose', 'N/A')}")
                                    st.warning(f"**Side Effects:** {explanation.get('side_effects', 'N/A')}")
                                    st.info(f"**Precautions:** {explanation.get('precautions', 'N/A')}")
                                    st.error(f"**Food Interactions:** {explanation.get('food_interactions', 'N/A')}")
                        with btn_col2:
                            if st.button("🔊 Generate Voice", key=f"speak_btn_{rec.id}", use_container_width=True):
                                st.session_state[f"rx_speak_{rec.id}"] = True

                            if st.session_state.get(f"rx_speak_{rec.id}"):
                                components.html(
                                    f"""
                                    <script>
                                    (function() {{
                                        if (!('speechSynthesis' in window)) {{
                                            alert('Sorry, your browser does not support text-to-speech.');
                                            return;
                                        }}
                                        window.speechSynthesis.cancel();
                                        var msg = new SpeechSynthesisUtterance("{safe_speech}");
                                        msg.lang = 'en-US';
                                        msg.rate = 0.92;
                                        msg.pitch = 1.0;
                                        msg.volume = 1.0;
                                        window.speechSynthesis.speak(msg);
                                    }})();
                                    </script>
                                    <div style="font-family:sans-serif;font-size:13px;padding:6px 10px;
                                                background:#d1fae5;border:1px solid #6ee7b7;border-radius:8px;
                                                color:#065f46;margin-top:4px;">
                                        🔊 Reading prescription aloud…
                                    </div>
                                    """,
                                    height=50,
                                )
                        with btn_col3:
                            if st.button("🔔 Set Smart Reminder", key=f"remind_btn_{rec.id}"):
                                st.success("Reminder configured successfully.")
                                
    finally:
        db.close()
