import streamlit as st
from views.components import load_global_css, load_dashboard_bg_css
from views.auth_view import render_login_view, render_register_view
from views.admin_portal import render_admin_portal, render_admin_pharmacy_view
from views.doctor_portal import render_doctor_portal
from views.patient_dashboard import render_patient_dashboard
from views.appointments_view import render_appointments_view
from views.doctors_view import render_doctors_view
from views.chatbot_view import render_chatbot_view

# New modular clinical views
from views.patients_view import render_patients_view
from views.prescriptions_view import render_prescriptions_view
from views.lab_reports_view import render_lab_reports_view
from views.billing_view import render_billing_view
from views.vitals_view import render_vitals_view
from views.notifications_view import render_notifications_view
from views.settings_view import render_settings_view
from views.analytics_view import render_analytics_view
from views.pharmacy_view import render_pharmacy_view, render_doctor_pharmacy_view
from views.patient_prescriptions_view import render_patient_prescriptions_view
from views.patient_reports_view import render_patient_reports_view

import logging
from core.database import create_tables

# Ensure all DB tables (including pharmacy) exist
create_tables()

_audit_log = logging.getLogger("smartcare")
if not _audit_log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s"))
    _audit_log.addHandler(_handler)
_audit_log.setLevel(logging.INFO)
_audit_log.propagate = False

st.set_page_config(
    page_title="IPCMS",
    page_icon="🏥",
    layout="wide"
)

load_global_css()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

if st.session_state.logged_in:
    user = st.session_state.user
    load_dashboard_bg_css(user["role"])

    # ── Hospital Logo & Header ───────────────────────────────────────────────
    # We display the logo and full clinic name at the top of the sidebar.
    st.sidebar.markdown(
        """<div style='text-align: center; margin-bottom: 12px; padding-top: 10px;'>
            <div style='font-size: 2.8rem; line-height: 1;'>🏥</div>
            <div style='font-size: 1.15rem; font-weight: 800; color: #1e3a8a; margin-top: 6px; letter-spacing: -0.01em;'>IPCMS</div>
            <div style='font-size: 0.65rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 2px;'>Integrated Patient Care Management System</div>
        </div>""",
        unsafe_allow_html=True
    )

    st.sidebar.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ── Search Filter ─────────────────────────────────────────────────────────
    # Allows doctors/patients to search menu items quickly.
    search_query = st.sidebar.text_input("🔍 Search Menu Items", placeholder="Type to filter...", label_visibility="collapsed")

    # Define role-specific menu items
    role = user["role"]

    if role == "Doctor":
        raw_menu_items = [
            {"label": "🏠 Dashboard",          "page": "Dashboard",      "section": "General"},
            {"label": "📅 Appointments",        "page": "Appointments",   "section": "Clinical"},
            {"label": "❤️ Vital Signs",         "page": "Vital Signs",    "section": "Clinical"},
            {"label": "🧪 Lab Reports",         "page": "Lab Reports",    "section": "Clinical"},
            {"label": "💊 Prescriptions",       "page": "Prescriptions",  "section": "Clinical"},
            {"label": "🛒 Pharmacy",           "page": "Pharmacy",       "section": "Clinical"},
            {"label": "🤖 AI Health Assistant", "page": "AI Assistant",   "section": "Tools"},
            {"label": "🔔 Notifications",       "page": "Notifications",  "section": "Tools"},
            {"label": "⚙️ Settings",            "page": "Settings",       "section": "Tools"},
            {"label": "🚪 Logout",              "page": "Logout",         "section": "Tools"},
        ]
    elif role == "Admin":
        raw_menu_items = [
            {"label": "🏠 Dashboard",             "page": "Dashboard",      "section": "General"},
            {"label": "👤 Patients",              "page": "Patients",       "section": "Management"},
            {"label": "👨‍⚕️ Doctors",              "page": "Doctors",        "section": "Management"},
            {"label": "📅 Appointments",          "page": "Appointments",   "section": "Management"},
            {"label": "🩺 Health Records",        "page": "Health Records", "section": "Management"},
            {"label": "💊 Prescriptions",         "page": "Prescriptions",  "section": "Management"},
            {"label": "🧪 Lab Reports",           "page": "Lab Reports",    "section": "Management"},
            {"label": "❤️ Vital Signs",           "page": "Vital Signs",    "section": "Management"},
            {"label": "💳 Billing",               "page": "Billing",        "section": "Administration"},
            {"label": "🏪 Pharmacy",              "page": "Pharmacy",       "section": "Administration"},
            {"label": "📊 Reports & Analytics",   "page": "Analytics",      "section": "Administration"},
            {"label": "🤖 AI Health Assistant",   "page": "AI Assistant",   "section": "Services"},
            {"label": "🔔 Notifications",         "page": "Notifications",  "section": "Services"},
            {"label": "⚙️ Settings",              "page": "Settings",       "section": "Services"},
            {"label": "🚪 Logout",               "page": "Logout",         "section": "Services"},
        ]
    else:  # Patient
        raw_menu_items = [
            {"label": "🏠 Dashboard",          "page": "Dashboard",      "section": "General"},
            {"label": "📅 Appointments",        "page": "Appointments",   "section": "My Health"},
            {"label": "🩺 Health Records",      "page": "Health Records", "section": "My Health"},
            {"label": "💊 Prescriptions",       "page": "Prescriptions",  "section": "My Health"},
            {"label": "🧪 Lab Reports",         "page": "Lab Reports",    "section": "My Health"},
            {"label": "❤️ Vital Signs",         "page": "Vital Signs",    "section": "My Health"},
            {"label": "💳 Billing",             "page": "Billing",        "section": "My Health"},
            {"label": "🛒 Pharmacy",           "page": "Pharmacy",       "section": "My Health"},
            {"label": "🤖 AI Health Assistant", "page": "AI Assistant",   "section": "Support"},
            {"label": "🔔 Notifications",       "page": "Notifications",  "section": "Support"},
            {"label": "⚙️ Settings",            "page": "Settings",       "section": "Support"},
            {"label": "🚪 Logout",              "page": "Logout",         "section": "Support"},
        ]

    # Filter items based on search query
    if search_query.strip():
        filtered_menu = [item for item in raw_menu_items if search_query.lower() in item["label"].lower()]
    else:
        filtered_menu = raw_menu_items

    # Render menu items grouped by section
    current_section = None
    for item in filtered_menu:
        if item["section"] != current_section and not search_query.strip():
            current_section = item["section"]
            st.sidebar.markdown(f"<div class='sidebar-section-title'>{current_section}</div>", unsafe_allow_html=True)
        
        is_active = st.session_state.current_page == item["page"]
        
        # We use Streamlit native buttons but style them dynamically via kind (primary vs secondary)
        if st.sidebar.button(
            item["label"], 
            key=f"menu_{item['page']}", 
            type="primary" if is_active else "secondary", 
            use_container_width=True
        ):
            if item["page"] == "Logout":
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.current_page = "Dashboard"
                if "chat_history" in st.session_state:
                    del st.session_state["chat_history"]
                st.rerun()
            else:
                st.session_state.current_page = item["page"]
                st.rerun()

    st.sidebar.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ── User Profile Card ────────────────────────────────────────────────────
    avatar_letter = user["full_name"][0].upper() if user["full_name"] else "U"
    role_color = {"Admin": "#a855f7", "Doctor": "#3b82f6", "Patient": "#22c55e"}.get(user["role"], "#64748b")
    
    profile_html = f"""
    <div style="background-color: rgba(15, 23, 42, 0.65); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 10px; margin-top: 10px; margin-bottom: 10px; backdrop-filter: blur(8px);">
        <div style="position: relative; width: 40px; height: 40px; border-radius: 50%; background-color: {role_color}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.15rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            {avatar_letter}
            <div style="position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; border-radius: 50%; background-color: #22c55e; border: 2px solid #ffffff;"></div>
        </div>
        <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-grow: 1;">
            <div style="font-weight: 700; font-size: 0.88rem; color: #f8fafc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 2px;">{user['full_name']}</div>
            <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 600;">{user['role']} &bull; <span style="color:#22c55e;font-weight:700;">Online</span></div>
        </div>
    </div>
    """
    st.sidebar.markdown(profile_html, unsafe_allow_html=True)

    # ── Page Routing ─────────────────────────────────────────────────────────
    page = st.session_state.current_page

    if page == "Dashboard":
        if user["role"] == "Admin":
            render_admin_portal()
        elif user["role"] == "Doctor":
            render_doctor_portal()
        else:
            render_patient_dashboard()

    elif page == "Patients":
        render_patients_view()

    elif page == "Doctors":
        render_doctors_view()

    elif page == "Appointments":
        render_appointments_view()

    elif page == "Health Records":
        if user["role"] == "Patient":
            render_patient_reports_view()
        elif user["role"] == "Doctor":
            render_doctor_portal()
        else:
            render_admin_portal()

    elif page == "Prescriptions":
        if user["role"] == "Patient":
            render_patient_prescriptions_view()
        else:
            render_prescriptions_view()

    elif page == "Lab Reports":
        render_lab_reports_view()

    elif page == "Vital Signs":
        render_vitals_view()

    elif page == "Billing":
        render_billing_view()

    elif page == "Analytics":
        render_analytics_view()

    elif page == "Pharmacy":
        if user["role"] == "Admin":
            render_admin_pharmacy_view()
        elif user["role"] == "Doctor":
            render_doctor_pharmacy_view()
        else:
            render_pharmacy_view()

    elif page == "AI Assistant":
        render_chatbot_view()

    elif page == "Notifications":
        render_notifications_view()

    elif page == "Settings":
        render_settings_view()

else:
    # ── Auth Portal (Sign In / Register) ──────────────────────────────────────
    choice = st.sidebar.selectbox("Access Mode", ["Sign In", "Register"])
    
    st.sidebar.markdown(
        """<div style='text-align: center; margin-top: 40px; padding: 20px; background-color: rgba(15, 23, 42, 0.55); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.15); backdrop-filter: blur(8px);'>
            <span style='font-size: 2.2rem;'>🏥</span>
            <div style='font-weight: 800; color: #60a5fa; margin-top: 6px; font-size: 0.95rem;'>Smart Care IPCMS</div>
            <div style='font-size: 0.7rem; color: #94a3b8; margin-top: 2px;'>Integrated Clinic Hub</div>
        </div>""",
        unsafe_allow_html=True
    )

    if choice == "Sign In":
        render_login_view()
    else:
        render_register_view()