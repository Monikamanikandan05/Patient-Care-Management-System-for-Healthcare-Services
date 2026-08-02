import streamlit as st
from core.database import SessionLocal
from models.models import User, HealthRecord
from views.components import html

def render_patients_view():
    st.write("### 👥 Patient Directory & Registries")
    user = st.session_state.user
    
    if user["role"] == "Patient":
        st.warning("⚠️ Access Restricted: Patient Directory is only accessible to authorized medical practitioners.")
        return
        
    db = SessionLocal()
    try:
        patients = db.query(User).filter(User.role == "Patient").all()
        
        search_pat = st.text_input("🔍 Search Patients by Name or Email", placeholder="e.g. John Doe...")
        
        for p in patients:
            if search_pat and search_pat.lower() not in p.full_name.lower() and search_pat.lower() not in p.email.lower():
                continue
                
            # Get count of health records
            rec_count = db.query(HealthRecord).filter(HealthRecord.patient_id == p.id).count()
            
            html(f"""
            <div class="medical-card" style="border-left: 4px solid #3b82f6;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;color:#2563eb;">{p.full_name}</h4>
                    <span class="hospital-badge" style="background:#eff6ff;color:#2563eb;border-color:#bfdbfe;">ID: #{p.id}</span>
                </div>
                <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;">
                    📧 <b>Email:</b> {p.email} | 📞 <b>Phone:</b> {p.phone or "N/A"}<br>
                    ⚧ <b>Gender:</b> {p.gender or "N/A"} | 🩺 <b>Total Health Records:</b> {rec_count}
                </p>
            </div>
            """)
    finally:
        db.close()
