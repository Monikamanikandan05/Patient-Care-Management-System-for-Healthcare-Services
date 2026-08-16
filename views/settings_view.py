import streamlit as st
import datetime
from core.database import SessionLocal
from models.models import User
from views.components import html

def _calculate_age(dob):
    """Return age in years from a date object, or None if dob is None."""
    if dob is None:
        return None
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

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

        # DOB & Age — only for Patient and Doctor
        dob = None
        if user.get("role") != "Admin":
            st.markdown("---")
            st.markdown("##### Date of Birth & Age")
            current_dob = db_user.dob if db_user else user.get("dob")
            max_dob = datetime.date.today() - datetime.timedelta(days=365)  # at least 1 year old
            dob = st.date_input(
                "Date of Birth",
                value=current_dob,
                min_value=datetime.date(1900, 1, 1),
                max_value=max_dob,
                key="settings_dob",
                help="Update your date of birth. Age is calculated automatically."
            )
            if dob:
                age_preview = _calculate_age(dob)
                st.caption(f"🎂 Age: **{age_preview} years**")
            elif current_dob is None:
                st.info("📌 Your date of birth is not set yet. Please select it above.")

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
                # Save DOB for Patient / Doctor
                if user.get("role") != "Admin":
                    db_user.dob = dob
                db.commit()
                # Update session state
                st.session_state.user["full_name"] = full_name
                st.session_state.user["email"] = email
                st.session_state.user["phone"] = phone
                st.session_state.user["gender"] = gender
                if user.get("role") != "Admin":
                    st.session_state.user["dob"] = dob
                    st.session_state.user["age"] = _calculate_age(dob)
                st.success("✅ Profile and settings updated successfully!")
                st.rerun()
    finally:
        db.close()
