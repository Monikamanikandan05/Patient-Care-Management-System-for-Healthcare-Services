import streamlit as st
from core.database import SessionLocal
from services.doctor_service import get_all_doctors, get_specialties
from models.models import User, Specialty
from views.components import html

def render_doctors_view():
    db = SessionLocal()
    try:
        st.write("### Medical Practitioner Directory")
        specialties = get_specialties(db)
        doctors = get_all_doctors(db)
        
        if not doctors:
            st.info("No active practitioners listed.")
        else:
            spec_names = ["All Specialties"] + [s.name for s in specialties]
            selected_spec = st.selectbox("Search by Specialty", spec_names)
            
            for doc in doctors:
                doc_user = db.query(User).filter(User.id == doc.user_id).first()
                doc_name = doc_user.full_name if doc_user else "Unknown"
                doc_spec = db.query(Specialty).filter(Specialty.id == doc.specialty_id).first()
                spec_name = doc_spec.name if doc_spec else "General Medicine"
                
                if selected_spec == "All Specialties" or spec_name == selected_spec:
                    html(
                        f'<div class="medical-card">'
                        f'<h4 style="margin:0;color:#ef4444;">Dr. {doc_name}</h4>'
                        f'<p style="margin:5px 0;font-size:0.95rem;font-weight:600;color:#cbd5e1;">Specialty: {spec_name} | Experience: {doc.experience_years} Years</p>'
                        f'<p style="margin:8px 0;font-size:0.9rem;color:#9ca3af;line-height:1.4;"><i>{doc.bio or "Dedicated cardiovascular specialist providing custom diagnostics and treatment plans."}</i></p>'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;border-top:1px solid rgba(255,255,255,0.05);padding-top:10px;">'
                        f'<span style="font-size:0.9rem;color:#ef4444;font-weight:700;">Consultation Fee: ${doc.consultation_fee}</span>'
                        f'<span class="hospital-badge">Active</span></div></div>'
                    )
    finally:
        db.close()
