import streamlit as st
import datetime
from core.database import SessionLocal
from services.appointment_service import book_appointment, get_appointments_for_user, cancel_appointment
from services.doctor_service import get_all_doctors, get_specialties, get_doctor_slots
from models.models import User, Doctor, Specialty, Appointment
from views.components import html

def render_appointments_view():
    user = st.session_state.user
    db = SessionLocal()
    try:
        # ── DOCTOR VIEW ─────────────────────────────────────────────────────────
        # Doctors cannot book appointments. They only see their own booked patients.
        if user["role"] == "Doctor":
            st.write("### 📋 Your Patient Appointment Schedule")

            # Resolve this doctor's profile and specialty
            doc_profile = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
            if not doc_profile:
                st.warning("⚠️ No doctor profile found. Please set up your profile in the About Doctor tab.")
                return

            spec = doc_profile.specialty
            spec_name = spec.name if spec else "General"
            spec_icon = spec.icon if spec else "🩺"

            st.info(f"{spec_icon} Showing appointments booked specifically for **Dr. {user['full_name']}** ({spec_name})")

            # Status filter
            status_filter = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled"], key="doc_appt_filter")

            appointments = get_appointments_for_user(db, user["id"], "Doctor")

            if status_filter != "All":
                appointments = [a for a in appointments if a.status == status_filter]

            if not appointments:
                st.info(f"No {status_filter.lower()} appointments found for your schedule.")
                return

            st.markdown(f"**{len(appointments)} appointment(s) found**")
            st.markdown("---")

            for appt in appointments:
                patient = db.query(User).filter(User.id == appt.patient_id).first()
                patient_name = patient.full_name if patient else "Unknown Patient"
                patient_email = patient.email if patient else "N/A"
                patient_phone = patient.phone if patient else "N/A"

                status_color = {"Scheduled": "#f59e0b", "Completed": "#22c55e", "Cancelled": "#ef4444"}.get(appt.status, "#9ca3af")
                status_bg    = {"Scheduled": "#fef3c7", "Completed": "#d1fae5", "Cancelled": "#fee2e2"}.get(appt.status, "#f1f5f9")
                status_border= {"Scheduled": "#fde68a", "Completed": "#a7f3d0", "Cancelled": "#fecaca"}.get(appt.status, "#e2e8f0")

                html(f"""
                <div class="medical-card" style="border-left: 4px solid {status_color};">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h4 style="margin:0; color:#ffffff;">👤 {patient_name}</h4>
                        <span style="background:{status_bg}; color:{status_color}; border:1px solid {status_border};
                                     padding:3px 12px; border-radius:20px; font-size:0.78rem; font-weight:700;">
                            {appt.status}
                        </span>
                    </div>
                    <p style="margin:0; font-size:0.88rem; color:#cbd5e1; line-height:1.8;">
                        📅 <b>Date:</b> {appt.scheduled_date} &nbsp;|&nbsp; ⏰ <b>Time:</b> {appt.start_time}<br>
                        🩺 <b>Specialty:</b> {spec_name} &nbsp;|&nbsp; 💬 <b>Reason:</b> {appt.reason or "General Consultation"}<br>
                        📧 <b>Patient Email:</b> {patient_email} &nbsp;|&nbsp; 📞 <b>Phone:</b> {patient_phone or "N/A"}
                    </p>
                </div>
                """)

                if appt.status == "Scheduled":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Mark Completed", key=f"done_{appt.id}"):
                            a = db.query(Appointment).filter(Appointment.id == appt.id).first()
                            a.status = "Completed"
                            db.commit()
                            st.success(f"Appointment with {patient_name} marked as completed!")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Cancel Appointment", key=f"cancel_{appt.id}"):
                            cancel_appointment(db, appt.id)
                            st.success("Appointment cancelled.")
                            st.rerun()

        # ── PATIENT VIEW ─────────────────────────────────────────────────────────
        # Patients can book appointments and view their own schedule.
        elif user["role"] == "Patient":
            st.write("### 📅 Appointments")
            tab1, tab2 = st.tabs(["📅 Book New Appointment", "📋 My Appointment History"])

            with tab1:
                st.write("#### Schedule a Consultation")
                specialties = get_specialties(db)
                doctors = get_all_doctors(db)

                if not doctors:
                    st.info("No active doctors found in the system.")
                else:
                    spec_names = ["All Specialties"] + [s.name for s in specialties]
                    selected_spec = st.selectbox("Filter by Specialty / Department", spec_names)

                    filtered_docs = []
                    for doc in doctors:
                        doc_user = db.query(User).filter(User.id == doc.user_id).first()
                        doc_name = doc_user.full_name if doc_user else "Unknown"
                        doc_spec = db.query(Specialty).filter(Specialty.id == doc.specialty_id).first()
                        spec_name = doc_spec.name if doc_spec else "General"

                        if selected_spec == "All Specialties" or spec_name == selected_spec:
                            icon = doc_spec.icon if doc_spec else "🩺"
                            filtered_docs.append((doc.id, f"{icon} Dr. {doc_name} ({spec_name}) — Fee: ₹{doc.consultation_fee}"))

                    if not filtered_docs:
                        st.info("No doctors found for the selected specialty.")
                    else:
                        doc_id_map = {text: doc_id for doc_id, text in filtered_docs}
                        selected_doc_text = st.selectbox("Choose Your Doctor", list(doc_id_map.keys()))
                        selected_doc_id = doc_id_map[selected_doc_text]

                        selected_date = st.date_input(
                            "Preferred Appointment Date",
                            min_value=datetime.date.today(),
                            max_value=datetime.date.today() + datetime.timedelta(days=30)
                        )

                        slots = get_doctor_slots(db, selected_doc_id)
                        time_options = [s.start_time for s in slots] if slots else [
                            datetime.time(9, 0), datetime.time(9, 30),
                            datetime.time(10, 0), datetime.time(10, 30),
                            datetime.time(11, 0), datetime.time(11, 30),
                            datetime.time(14, 0), datetime.time(14, 30),
                            datetime.time(15, 0), datetime.time(15, 30)
                        ]

                        selected_time = st.selectbox("Choose Available Time Slot", time_options)
                        reason = st.text_input("Reason for Appointment", placeholder="e.g. Routine checkup, dental pain, eye examination...")

                        if st.button("✅ Confirm Booking", use_container_width=True):
                            try:
                                book_appointment(db, user["id"], selected_doc_id, selected_date, selected_time, reason)
                                st.success("✅ Appointment successfully booked! Your doctor will confirm shortly.")
                            except ValueError as ve:
                                st.error(str(ve))
                            except Exception as e:
                                st.error(f"Booking failed: {e}")

            with tab2:
                st.write("#### My Consultation History")
                appointments = get_appointments_for_user(db, user["id"], "Patient")

                if appointments:
                    for appt in appointments:
                        doc_profile = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
                        doc_user = db.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
                        doc_name = doc_user.full_name if doc_user else "Unknown"
                        doc_spec = db.query(Specialty).filter(Specialty.id == doc_profile.specialty_id).first() if doc_profile else None
                        spec_label = doc_spec.name if doc_spec else "General"

                        status_color = {"Scheduled": "#f59e0b", "Completed": "#22c55e", "Cancelled": "#ef4444"}.get(appt.status, "#9ca3af")

                        html(f"""
                        <div class="medical-card" style="border-left: 4px solid {status_color};">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <h4 style="margin:0; color:#ffffff;">Dr. {doc_name}</h4>
                                <span style="color:{status_color}; font-weight:700; font-size:0.82rem;">{appt.status}</span>
                            </div>
                            <p style="margin:0; font-size:0.88rem; color:#cbd5e1; line-height:1.8;">
                                🩺 <b>Specialty:</b> {spec_label}<br>
                                📅 <b>Date:</b> {appt.scheduled_date} &nbsp;|&nbsp; ⏰ <b>Time:</b> {appt.start_time}<br>
                                💬 <b>Reason:</b> {appt.reason or "General consultation"}
                            </p>
                        </div>
                        """)

                        if appt.status == "Scheduled":
                            if st.button(f"❌ Cancel Appointment (ID: {appt.id})", key=f"pat_cancel_{appt.id}"):
                                cancel_appointment(db, appt.id)
                                st.success("Appointment cancelled.")
                                st.rerun()
                else:
                    st.info("You have no scheduled or past consultations.")

        # ── ADMIN VIEW ─────────────────────────────────────────────────────────
        else:
            st.write("### 📋 All Hospital Appointments")
            appointments = get_appointments_for_user(db, user["id"], "Admin")

            status_filter = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled"])
            if status_filter != "All":
                appointments = [a for a in appointments if a.status == status_filter]

            if not appointments:
                st.info(f"No {status_filter.lower()} appointments found.")
            else:
                for appt in appointments:
                    doc_profile = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
                    doc_user = db.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
                    patient = db.query(User).filter(User.id == appt.patient_id).first()

                    doc_name = doc_user.full_name if doc_user else "Unknown"
                    patient_name = patient.full_name if patient else "Unknown"
                    status_color = {"Scheduled": "#f59e0b", "Completed": "#22c55e", "Cancelled": "#ef4444"}.get(appt.status, "#9ca3af")

                    html(f"""
                    <div class="medical-card" style="border-left: 4px solid {status_color};">
                        <div style="display:flex; justify-content:space-between;">
                            <h5 style="margin:0; color:#ffffff;">👤 {patient_name} → Dr. {doc_name}</h5>
                            <span style="color:{status_color}; font-weight:700; font-size:0.82rem;">{appt.status}</span>
                        </div>
                        <p style="margin:6px 0 0 0; font-size:0.85rem; color:#cbd5e1;">
                            📅 {appt.scheduled_date} ⏰ {appt.start_time} | 💬 {appt.reason or "General"}
                        </p>
                    </div>
                    """)

    finally:
        db.close()
