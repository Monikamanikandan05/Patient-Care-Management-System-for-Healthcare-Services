import streamlit as st
from core.database import SessionLocal
from models.models import User, HealthRecord, Doctor
from views.components import html

def render_billing_view():
    st.write("### 💳 Invoice Registry & Billing System")
    user = st.session_state.user
    db = SessionLocal()
    try:
        patients = db.query(User).filter(User.role == 'Patient').all()
        
        if user["role"] == "Patient":
            selected_patient_id = user["id"]
            patient_name = user["full_name"]
        else:
            if not patients:
                st.info("No patients registered.")
                return
            patient_map = {p.full_name: p.id for p in patients}
            selected_patient_name = st.selectbox("Select Patient to Manage Invoices", list(patient_map.keys()))
            selected_patient_id = patient_map[selected_patient_name]
            patient_name = selected_patient_name
            
        records = db.query(HealthRecord).filter(HealthRecord.patient_id == selected_patient_id).all()
        
        st.markdown(f"##### Invoices for **{patient_name}**")
        
        # Display static setup checkup fee and dynamically loaded consultation fees
        html("""
        <div class="medical-card" style="border-left: 4px solid #10b981;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0;color:#10b981;">💳 Hospital Registration Fee</h4>
                <span class="hospital-badge" style="background:#d1fae5;color:#065f46;border-color:#a7f3d0;">PAID</span>
            </div>
            <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;">
                <b>Invoice ID:</b> #INV-REG-1092 | <b>Amount:</b> $50.00<br>
                <b>Date:</b> 2026-07-01 | <b>Method:</b> Visa ending in 4242
            </p>
        </div>
        """)
        
        found = False
        for rec in records:
            if rec.doctor_id:
                found = True
                doc_profile = db.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
                doc_user = db.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
                doc_name = doc_user.full_name if doc_user else "Practitioner"
                fee = float(doc_profile.consultation_fee) if (doc_profile and doc_profile.consultation_fee) else 80.00
                
                html(f"""
                <div class="medical-card" style="border-left: 4px solid #f59e0b;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;color:#f59e0b;">💳 Consultation - Dr. {doc_name} ({rec.specialty_type or "General"})</h4>
                        <span class="hospital-badge" style="background:#fef3c7;color:#92400e;border-color:#fde68a;">UNPAID</span>
                    </div>
                    <p style="margin:8px 0 0 0;font-size:0.9rem;color:#cbd5e1;">
                        <b>Invoice ID:</b> #INV-CONS-{rec.id} | <b>Amount:</b> ${fee:.2f}<br>
                        <b>Date:</b> {rec.recorded_at.date() if rec.recorded_at else "N/A"}
                    </p>
                </div>
                """)
                
        if not found:
            st.info("No consultation invoices found.")
            
        if user["role"] == "Patient" and found:
            if st.button("💳 Proceed to Checkout & Pay Unpaid Bills", use_container_width=True):
                st.success("✅ Payment successful! All outstanding consultation invoices have been cleared.")
    finally:
        db.close()
