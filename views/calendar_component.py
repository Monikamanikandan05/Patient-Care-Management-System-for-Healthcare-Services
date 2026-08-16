import datetime
import calendar
import streamlit as st
from models.models import Appointment, User, Doctor
from services.appointment_service import get_appointments_for_user
from views.components import format_doctor_name


def render_appointment_calendar(db, user_role: str, user_id: int = None):
    """
    Renders an interactive Appointment Calendar component with Month-wise and Date-wise views.
    - Patient mode: Shows doctor name and specialty for patient's appointments.
    - Doctor mode: Shows patient name for doctor's appointments.
    - Admin mode: Shows doctor ↔ patient pairings for all clinic appointments.
    """
    st.markdown("""
        <style>
        .cal-header-box {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 12px;
            padding: 16px 20px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 16px;
        }
        .cal-day-header {
            text-align: center;
            font-weight: 700;
            font-size: 0.85rem;
            color: #94a3b8;
            padding: 8px 0;
            text-transform: uppercase;
        }
        .cal-day-cell {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            min-height: 90px;
            padding: 6px;
            transition: all 0.2s ease;
        }
        .cal-day-cell:hover {
            border-color: #3b82f6;
            background: rgba(30, 41, 59, 0.95);
        }
        .cal-day-cell.today {
            border: 2px solid #3b82f6 !important;
            background: rgba(37, 99, 235, 0.15);
        }
        .cal-day-cell.other-month {
            opacity: 0.35;
        }
        .cal-date-num {
            font-weight: 800;
            font-size: 0.85rem;
            color: #e2e8f0;
            margin-bottom: 4px;
        }
        .appt-badge {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            margin-bottom: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: block;
        }
        .badge-scheduled { background: rgba(59, 130, 246, 0.25); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
        .badge-completed { background: rgba(34, 197, 94, 0.25); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.4); }
        .badge-cancelled { background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
        .detail-card {
            background: rgba(15, 23, 42, 0.6);
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 📅 Appointment Calendar Hub")

    # Fetch appointments depending on role
    if user_role == "Admin":
        all_appts = db.query(Appointment).all()
    elif user_role == "Doctor":
        all_appts = get_appointments_for_user(db, user_id, "Doctor")
    else:  # Patient
        all_appts = get_appointments_for_user(db, user_id, "Patient")

    # View Mode Selector: Month-wise vs Date-wise
    v_col1, v_col2 = st.columns([1, 2])
    with v_col1:
        view_mode = st.radio(
            "Select View Mode",
            ["📅 Month-Wise View", "📆 Date-Wise View"],
            horizontal=True,
            key=f"cal_view_mode_{user_role}"
        )

    # State for current selected month & date
    today = datetime.date.today()
    if f"cal_year_{user_role}" not in st.session_state:
        st.session_state[f"cal_year_{user_role}"] = today.year
    if f"cal_month_{user_role}" not in st.session_state:
        st.session_state[f"cal_month_{user_role}"] = today.month
    if f"cal_selected_date_{user_role}" not in st.session_state:
        st.session_state[f"cal_selected_date_{user_role}"] = today

    cur_year = st.session_state[f"cal_year_{user_role}"]
    cur_month = st.session_state[f"cal_month_{user_role}"]

    # Map appointments by date
    appts_by_date = {}
    for appt in all_appts:
        d = appt.scheduled_date
        if d not in appts_by_date:
            appts_by_date[d] = []
        appts_by_date[d].append(appt)

    # ──────────────────────────────────────────────────────────────────────────
    # MONTH-WISE VIEW
    # ──────────────────────────────────────────────────────────────────────────
    if "Month-Wise" in view_mode:
        # Month navigation controls
        n_col1, n_col2, n_col3, n_col4 = st.columns([1.5, 2, 2, 1.5])
        with n_col1:
            if st.button("◀ Previous Month", key=f"btn_prev_{user_role}", use_container_width=True):
                if cur_month == 1:
                    st.session_state[f"cal_month_{user_role}"] = 12
                    st.session_state[f"cal_year_{user_role}"] -= 1
                else:
                    st.session_state[f"cal_month_{user_role}"] -= 1
                st.rerun()
        with n_col2:
            month_names = list(calendar.month_name)[1:]
            sel_m_name = st.selectbox(
                "Month",
                month_names,
                index=cur_month - 1,
                key=f"sb_m_{user_role}",
                label_visibility="collapsed"
            )
            st.session_state[f"cal_month_{user_role}"] = month_names.index(sel_m_name) + 1
        with n_col3:
            years = list(range(today.year - 2, today.year + 3))
            sel_y = st.selectbox(
                "Year",
                years,
                index=years.index(cur_year) if cur_year in years else 2,
                key=f"sb_y_{user_role}",
                label_visibility="collapsed"
            )
            st.session_state[f"cal_year_{user_role}"] = sel_y
        with n_col4:
            if st.button("Current Month", key=f"btn_today_{user_role}", use_container_width=True):
                st.session_state[f"cal_month_{user_role}"] = today.month
                st.session_state[f"cal_year_{user_role}"] = today.year
                st.session_state[f"cal_selected_date_{user_role}"] = today
                st.rerun()

        cur_year = st.session_state[f"cal_year_{user_role}"]
        cur_month = st.session_state[f"cal_month_{user_role}"]

        # Calendar month info
        cal_obj = calendar.Calendar(firstweekday=6) # Sunday start
        month_days = list(cal_obj.itermonthdates(cur_year, cur_month))

        st.markdown(
            f"<h4 style='text-align: center; color: #60a5fa; margin-top: 10px;'>"
            f"📆 {calendar.month_name[cur_month]} {cur_year}</h4>",
            unsafe_allow_html=True
        )

        # Legend
        st.markdown(
            "<div style='display: flex; gap: 15px; justify-content: center; margin-bottom: 12px; font-size: 0.8rem;'>"
            "<span class='appt-badge badge-scheduled'>🔵 Scheduled</span>"
            "<span class='appt-badge badge-completed'>🟢 Completed</span>"
            "<span class='appt-badge badge-cancelled'>🔴 Cancelled</span>"
            "</div>",
            unsafe_allow_html=True
        )

        # Header Row: Days of Week
        day_headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        h_cols = st.columns(7)
        for idx, h in enumerate(day_headers):
            h_cols[idx].markdown(f"<div class='cal-day-header'>{h}</div>", unsafe_allow_html=True)

        # Calendar Grid (Weeks)
        for w in range(0, len(month_days), 7):
            week = month_days[w:w+7]
            w_cols = st.columns(7)
            for idx, d in enumerate(week):
                with w_cols[idx]:
                    is_current_month = (d.month == cur_month)
                    is_today = (d == today)

                    # Build badges for appointments on this date
                    day_appts = appts_by_date.get(d, [])
                    badges_html = ""
                    for a in day_appts[:3]: # Max 3 items per box
                        b_cls = "badge-scheduled"
                        if a.status == "Completed":
                            b_cls = "badge-completed"
                        elif a.status == "Cancelled":
                            b_cls = "badge-cancelled"

                        # Role specific short summary
                        if user_role == "Patient":
                            doc_u = a.doctor.user if (a.doctor and a.doctor.user) else None
                            label = f"Dr. {doc_u.full_name.split()[-1]}" if doc_u else "Doctor"
                        elif user_role == "Doctor":
                            pat_u = a.patient
                            label = pat_u.full_name.split()[0] if pat_u else "Patient"
                        else: # Admin
                            doc_u = a.doctor.user if (a.doctor and a.doctor.user) else None
                            pat_u = a.patient
                            d_short = doc_u.full_name.split()[-1] if doc_u else "Doc"
                            p_short = pat_u.full_name.split()[0] if pat_u else "Pat"
                            label = f"Dr.{d_short}↔{p_short}"

                        badges_html += f"<span class='appt-badge {b_cls}' title='{a.status} - {label} ({a.start_time})'>{label} ({a.start_time})</span>"

                    if len(day_appts) > 3:
                        badges_html += f"<span class='appt-badge' style='background:rgba(255,255,255,0.1); color:#94a3b8;'>+{len(day_appts)-3} more</span>"

                    cell_cls = "cal-day-cell"
                    if not is_current_month:
                        cell_cls += " other-month"
                    if is_today:
                        cell_cls += " today"

                    st.markdown(
                        f"<div class='{cell_cls}'>"
                        f"<div class='cal-date-num'>{d.day}</div>"
                        f"{badges_html}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    # Quick click date button to inspect
                    if is_current_month and day_appts:
                        if st.button(f"Inspect ({len(day_appts)})", key=f"btn_d_{d.strftime('%Y%m%d')}_{user_role}", use_container_width=True):
                            st.session_state[f"cal_selected_date_{user_role}"] = d
                            st.rerun()

        # Section to inspect selected date from month view
        sel_date = st.session_state[f"cal_selected_date_{user_role}"]
        st.markdown("---")
        _render_date_details(db, sel_date, appts_by_date.get(sel_date, []), user_role)

    # ──────────────────────────────────────────────────────────────────────────
    # DATE-WISE VIEW
    # ──────────────────────────────────────────────────────────────────────────
    else:
        st.markdown("#### 📆 Select Date to Inspect Appointments")
        d_col1, d_col2 = st.columns([1, 2])
        with d_col1:
            picked_date = st.date_input(
                "Choose Date",
                value=st.session_state[f"cal_selected_date_{user_role}"],
                key=f"dpi_{user_role}"
            )
            st.session_state[f"cal_selected_date_{user_role}"] = picked_date

        selected_appts = appts_by_date.get(picked_date, [])
        _render_date_details(db, picked_date, selected_appts, user_role)


def _render_date_details(db, target_date: datetime.date, appts: list, user_role: str):
    """Renders detailed appointment cards for a given date."""
    formatted_date = target_date.strftime('%A, %d %B %Y')
    st.markdown(f"#### 📋 Appointments for {formatted_date} ({len(appts)} Total)")

    if not appts:
        st.info(f"No appointments scheduled on {formatted_date}.")
        return

    for a in appts:
        status_color = "#3b82f6"
        if a.status == "Completed":
            status_color = "#22c55e"
        elif a.status == "Cancelled":
            status_color = "#ef4444"

        # Information building based on role
        if user_role == "Patient":
            doc_u = a.doctor.user if (a.doctor and a.doctor.user) else None
            d_name = format_doctor_name(doc_u.full_name) if doc_u else "Medical Specialist"
            spec = a.doctor.specialty.name if (a.doctor and a.doctor.specialty) else "General Medicine"
            title_str = f"👨‍⚕️ {d_name} ({spec})"
            subtitle_str = f"⏰ Time: **{a.start_time}** | Reason: {a.reason or 'Routine Checkup'}"

        elif user_role == "Doctor":
            pat_u = a.patient
            p_name = pat_u.full_name if pat_u else "Unknown Patient"
            phone = pat_u.phone if (pat_u and pat_u.phone) else "N/A"
            title_str = f"👤 Patient: {p_name}"
            subtitle_str = f"⏰ Time: **{a.start_time}** | 📞 Contact: {phone} | Reason: {a.reason or 'Consultation'}"

        else:  # Admin
            doc_u = a.doctor.user if (a.doctor and a.doctor.user) else None
            pat_u = a.patient
            d_name = format_doctor_name(doc_u.full_name) if doc_u else "Doctor"
            p_name = pat_u.full_name if pat_u else "Patient"
            title_str = f"🏥 Dr. {d_name} ↔ Patient: {p_name}"
            subtitle_str = f"⏰ Time: **{a.start_time}** | Source: {a.source or 'Portal'} | Reason: {a.reason or 'Consultation'}"

        st.markdown(
            f"""
            <div class="detail-card" style="border-left-color: {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1rem; color: #f8fafc;">{title_str}</span>
                    <span class="appt-badge badge-{'scheduled' if a.status=='Scheduled' else ('completed' if a.status=='Completed' else 'cancelled')}">{a.status}</span>
                </div>
                <div style="margin-top: 6px; font-size: 0.88rem; color: #cbd5e1;">
                    {subtitle_str}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
