import streamlit as st
from core.database import SessionLocal
from models.models import User
from views.components import html

def render_settings_view():
    st.write("### ⚙️ Account & Application Settings")
    user = st.session_state.user
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.id == user["id"]).first()
        
        st.markdown("##### My Profile Details")
        
        full_name = st.text_input("Full Name", value=db_user.full_name if db_user else user["full_name"])
        email = st.text_input("Email Address", value=db_user.email if db_user else user["email"])
        phone = st.text_input("Phone Number", value=db_user.phone if db_user else (user.get("phone") or ""))
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(db_user.gender) if (db_user and db_user.gender in ["Male", "Female", "Other"]) else 0)
        
        st.markdown("---")
        st.markdown("##### App Preferences")
        theme = st.selectbox("Preferred Theme", ["Crimson Dark Vitals (Default)", "Modern Indigo", "Emerald Clinical Light"])
        notifications_enabled = st.checkbox("Enable Real-time SMS & Email Alert Dispatching", value=True)
        
        if st.button("💾 Save Settings & Update Profile", use_container_width=True):
            if db_user:
                db_user.full_name = full_name
                db_user.email = email
                db_user.phone = phone
                db_user.gender = gender
                db.commit()
                # Update session state
                st.session_state.user["full_name"] = full_name
                st.session_state.user["email"] = email
                st.session_state.user["phone"] = phone
                st.session_state.user["gender"] = gender
                st.success("✅ Profile and settings updated successfully!")
                st.rerun()
    finally:
        db.close()
