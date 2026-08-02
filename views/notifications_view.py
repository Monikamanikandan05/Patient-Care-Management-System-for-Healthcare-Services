import streamlit as st
from views.components import html

def render_notifications_view():
    st.write("### 🔔 Live Hospital Notifications")
    user = st.session_state.user
    user_id = user["id"]
    notif_key = f"user_notifications_{user_id}"

    # Initialize notifications state for this user if not present
    if notif_key not in st.session_state:
        role = user.get("role", "Patient")
        if role == "Doctor":
            st.session_state[notif_key] = [
                {
                    "id": 1,
                    "title": "📅 New Patient Appointment Scheduled",
                    "time": "10 mins ago",
                    "color": "#3b82f6",
                    "desc": "A new consultation has been booked for your morning clinic schedule."
                },
                {
                    "id": 2,
                    "title": "🩺 Patient Vital Alert Updated",
                    "time": "1 hour ago",
                    "color": "#f59e0b",
                    "desc": "New diagnostic vital measurements submitted for review on your patient roster."
                },
                {
                    "id": 3,
                    "title": "🧪 Laboratory Results Ready",
                    "time": "Yesterday",
                    "color": "#10b981",
                    "desc": "Specialty lab diagnostic report results have been attached to patient records."
                }
            ]
        elif role == "Admin":
            st.session_state[notif_key] = [
                {
                    "id": 1,
                    "title": "🛡️ Daily System Audit Completed",
                    "time": "30 mins ago",
                    "color": "#10b981",
                    "desc": "Database backup and system compliance checks completed successfully."
                },
                {
                    "id": 2,
                    "title": "👤 New Doctor Profile Registered",
                    "time": "2 hours ago",
                    "color": "#a855f7",
                    "desc": "A practitioner account has completed registration and specialty assignment."
                }
            ]
        else:  # Patient
            st.session_state[notif_key] = [
                {
                    "id": 1,
                    "title": "📅 Appointment Confirmed",
                    "time": "1 hour ago",
                    "color": "#3b82f6",
                    "desc": "Your consultation booking request has been successfully approved by the physician desk."
                },
                {
                    "id": 2,
                    "title": "💊 Prescription Released",
                    "time": "Yesterday",
                    "color": "#10b981",
                    "desc": "A new medical prescription note has been authorized and issued to your log."
                },
                {
                    "id": 3,
                    "title": "⚠️ Health Diagnostic Alert",
                    "time": "3 days ago",
                    "color": "#ef4444",
                    "desc": "Slightly elevated blood pressure detected in your latest vitals check. Advised regular checkup."
                }
            ]

    notifications = st.session_state[notif_key]

    col_title, col_btn = st.columns([2.5, 1])
    with col_title:
        st.markdown(f"##### Inbox Alerts ({len(notifications)})")
    
    with col_btn:
        if notifications:
            if st.button("🧹 Clear All Notifications", key="clear_all_notifs_btn", use_container_width=True):
                st.session_state[notif_key] = []
                st.success("✅ All notifications cleared!")
                st.rerun()

    if not notifications:
        html("""
        <div class="medical-card" style="text-align:center; padding:35px; border: 2px dashed rgba(255,255,255,0.12);">
            <div style="font-size:3rem;">🎉</div>
            <div style="font-weight:700; color:#22c55e; font-size:1.1rem; margin-top:8px;">All Caught Up!</div>
            <div style="color:#9ca3af; font-size:0.85rem; margin-top:4px;">You have cleared all active notifications. New hospital alerts will appear here.</div>
        </div>
        """)
        return

    # Render each notification card with individual dismiss button
    to_delete = None
    for idx, notif in enumerate(notifications):
        n_id = notif.get("id", idx)
        color = notif.get("color", "#3b82f6")
        
        c_card, c_del = st.columns([4.8, 1.2])
        with c_card:
            html(f"""
            <div class="medical-card" style="border-left: 4px solid {color}; background-color: rgba(22, 25, 30, 0.6); margin-bottom: 10px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h5 style="margin:0;color:{color};">{notif['title']}</h5>
                    <small style="color:#64748b;">{notif['time']}</small>
                </div>
                <p style="margin:6px 0 0 0;font-size:0.88rem;color:#cbd5e1;">
                    {notif['desc']}
                </p>
            </div>
            """)
        with c_del:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("❌ Dismiss", key=f"dismiss_notif_{idx}_{n_id}", use_container_width=True):
                to_delete = idx

    if to_delete is not None:
        st.session_state[notif_key].pop(to_delete)
        st.rerun()
