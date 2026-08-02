import datetime
import streamlit as st
from core.database import session_scope
from models.models import Specialty, Doctor, User, DoctorSlot, Appointment
from services import doctor_service, appointment_service
from views.components import html


def render_booking_wizard(user: dict):
    """Guided deterministic booking flow widget rendered inside the chat view."""

    html("""
    <div style="background:linear-gradient(135deg,#0f1f3d,#1a2e4a);
                border:1px solid #3b82f6;border-radius:16px;
                padding:20px 24px;margin:16px 0 8px 0;
                box-shadow:0 4px 24px rgba(59,130,246,0.15);">
      <div style="font-size:1.15rem;font-weight:800;color:#60a5fa;margin-bottom:4px;">
        📅 Appointment Booking Wizard
      </div>
      <div style="font-size:0.83rem;color:#94a3b8;">
        Fill in the steps below to confirm your appointment directly into the system.
      </div>
    </div>
    """)

    with session_scope() as s:
        specialties = s.query(Specialty).all()
        spec_options = {spec.name: spec.id for spec in specialties}

    if not spec_options:
        st.warning("⚠️ No specialties available at this time. Please contact reception.")
        if st.button("✖ Close Wizard"):
            st.session_state.show_booking_wizard = False
            st.rerun()
        return

    # ── Step 1 & 2: Specialty + Doctor ───────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Step 1 — Specialty**")
        sel_spec_name = st.selectbox(
            "Clinical Specialty",
            list(spec_options.keys()),
            key="bw_specialty",
            label_visibility="collapsed"
        )
        spec_id = spec_options[sel_spec_name]

    with session_scope() as s:
        doctors = doctor_service.get_doctors_by_specialty(s, spec_id)
        doc_map = {
            f"Dr. {d.user.full_name}  —  {d.experience_years} yrs  |  ₹{int(d.consultation_fee or 0)}": d.id
            for d in doctors if d.user
        }

    with col2:
        st.markdown("**Step 2 — Doctor**")
        if not doc_map:
            st.info("No doctors available in this specialty.")
            if st.button("✖ Close Wizard", key="bw_close_nodoctor"):
                st.session_state.show_booking_wizard = False
                st.rerun()
            return
        sel_doc_label = st.selectbox(
            "Doctor",
            list(doc_map.keys()),
            key="bw_doctor",
            label_visibility="collapsed"
        )
        doc_id = doc_map[sel_doc_label]

    # ── Step 3 & 4: Date + Time ───────────────────────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Step 3 — Date**")
        today = datetime.date.today()
        sel_date = st.date_input(
            "Appointment Date",
            min_value=today + datetime.timedelta(days=1),
            value=today + datetime.timedelta(days=1),
            key="bw_date",
            label_visibility="collapsed"
        )

    with col4:
        st.markdown("**Step 4 — Time Slot**")
        available_slots = [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "12:00", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
        ]
        sel_time_str = st.selectbox(
            "Time Slot",
            available_slots,
            key="bw_time",
            label_visibility="collapsed"
        )
        sel_time = datetime.datetime.strptime(sel_time_str, "%H:%M").time()

    # ── Step 5: Reason ────────────────────────────────────────────────────────
    st.markdown("**Step 5 — Reason for Visit**")
    reason = st.text_input(
        "Reason",
        placeholder="e.g. Routine cardiac checkup, chest discomfort, follow-up consultation",
        key="bw_reason",
        label_visibility="collapsed"
    )

    st.markdown("")  # spacer

    # ── Action Buttons ────────────────────────────────────────────────────────
    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button("✅ Confirm Appointment", type="primary", use_container_width=True, key="bw_confirm"):
            try:
                with session_scope() as s:
                    appt = appointment_service.book_appointment(
                        db=s,
                        patient_id=user["id"],
                        doctor_id=doc_id,
                        date=sel_date,
                        start_time=sel_time,
                        reason=reason or "Booked via SmartCare AI",
                        source="chatbot"
                    )

                # Build success message and add to chat
                success_msg = (
                    f"✅ **Appointment Confirmed!**\n\n"
                    f"- 👨‍⚕️ **Doctor:** {sel_doc_label.split('—')[0].strip()}\n"
                    f"- 🏥 **Specialty:** {sel_spec_name}\n"
                    f"- 📅 **Date:** {sel_date.strftime('%A, %d %B %Y')}\n"
                    f"- ⏰ **Time:** {sel_time_str}\n"
                    f"- 💬 **Reason:** {reason or 'General Consultation'}\n\n"
                    "You can view this in your **Appointments** tab. See you soon! 😊"
                )
                st.session_state.chat_history.append({"role": "assistant", "content": success_msg})
                st.session_state.show_booking_wizard = False
                st.success("🎉 Appointment booked successfully!")
                st.rerun()

            except ValueError as ve:
                st.error(f"⚠️ Booking conflict: {ve}")
            except Exception as exc:
                st.error(f"❌ Could not complete booking: {exc}")

    with btn_col2:
        if st.button("✖ Cancel", use_container_width=True, key="bw_cancel"):
            st.session_state.show_booking_wizard = False
            st.rerun()
