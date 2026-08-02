import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, time
from core.database import SessionLocal
from services.analytics_service import get_admin_stats
from services.doctor_service import (
    get_all_doctors, add_doctor_profile, get_specialties,
    create_specialty, add_doctor_slot, remove_doctor_slot
)
from services.auth_service import register_user
from services.pharmacy_service import (
    get_all_medicines, add_medicine, update_stock, deactivate_medicine,
    reactivate_medicine, get_all_orders, update_order_status, seed_medicines,
    get_categories
)
from models.models import User, Doctor, Appointment, HealthRecord, Specialty, DoctorSlot, PharmacyMedicine
import streamlit.components.v1 as components
from views.prescriptions_view import _render_prescription_card, _is_real_prescription, _render_read_only_prescriptions_table

def render_admin_portal():
    db = SessionLocal()
    try:
        stats = get_admin_stats(db)

        # ── Welcome Banner ────────────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,rgba(168,85,247,.15),rgba(168,85,247,.03));
                        border:1px solid rgba(168,85,247,.3);border-radius:16px;
                        padding:22px 28px;margin-bottom:24px;">
                <h2 style="margin:0;color:#fff;">🛡️ <span style="color:#a855f7;">Admin Control Center</span></h2>
                <p style="margin:6px 0 0;color:#9ca3af;font-size:.95rem;">
                    Today: <b>{date.today().strftime('%A, %d %B %Y')}</b> &nbsp;|&nbsp; Full system access
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── KPI Strip ─────────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("👥 Total Users",         stats["total_users"])
        with k2:
            st.metric("👨‍⚕️ Active Doctors",      stats["total_doctors"])
        with k3:
            st.metric("🧑‍⚕️ Registered Patients", stats["total_patients"])
        with k4:
            st.metric("📅 Total Appointments",  stats["total_appointments"])

        st.markdown("---")

        # ── Tabs ──────────────────────────────────────────────────────────────
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "📊 System Analytics",
            "👨‍⚕️ Manage Doctors",
            "🏥 Medical Specialties",
            "🧑‍⚕️ Patient Directory",
            "📅 All Appointments",
            "🩺 Health Records",
            "💊 Prescriptions",
            "👥 User Management",
            "🏪 Pharmacy",
        ])

        # ── TAB 1: System Analytics ───────────────────────────────────────────
        with tab1:
            st.markdown("### 📊 Detailed System Analytics")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### Appointment Status Distribution")
                if stats.get("status_distribution"):
                    df_status = pd.DataFrame(list(stats["status_distribution"].items()), columns=["Status", "Count"])
                    st.bar_chart(df_status.set_index("Status"))
                else:
                    st.info("No appointment data yet.")

            with col_b:
                st.markdown("#### User Role Breakdown")
                role_data = {
                    "Admin":   db.query(User).filter(User.role == "Admin").count(),
                    "Doctor":  db.query(User).filter(User.role == "Doctor").count(),
                    "Patient": db.query(User).filter(User.role == "Patient").count(),
                }
                df_roles = pd.DataFrame(list(role_data.items()), columns=["Role", "Count"])
                st.bar_chart(df_roles.set_index("Role"))
            
            st.markdown("#### 📈 Key Metrics")
            m1, m2, m3, m4 = st.columns(4)
            total_records = db.query(HealthRecord).count()
            with m1:
                st.metric("🩺 Health Records",  total_records)
            with m2:
                completed = stats["status_distribution"].get("Completed", 0) if stats.get("status_distribution") else 0
                total_a   = stats["total_appointments"]
                rate      = round(completed / total_a * 100, 1) if total_a > 0 else 0
                st.metric("✅ Completion Rate", f"{rate}%")
            with m3:
                st.metric("🏥 Doctor-Patient Ratio", f"1:{round(stats['total_patients']/max(stats['total_doctors'],1),1)}")
            with m4:
                avg_appts = round(stats["total_appointments"] / max(stats["total_patients"], 1), 1)
                st.metric("📅 Avg Appts/Patient", avg_appts)

        # ── TAB 2: Manage Doctors ─────────────────────────────────────────────
        with tab2:
            st.markdown("### 👨‍⚕️ Manage Doctors")
            doc_tab1, doc_tab2, doc_tab3 = st.tabs(["➕ Create Doctor", "🔄 Assign Profile", "⏰ Manage Availability"])

            # ── Sub-Tab 1: Create Doctor
            with doc_tab1:
                st.markdown("#### Create New Doctor")
                with st.form("create_doctor_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Full Name", placeholder="e.g. Dr. Jane Smith")
                        new_email = st.text_input("Email", placeholder="doctor@hospital.com")
                        new_pass = st.text_input("Password", type="password")
                        new_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    with col2:
                        new_phone = st.text_input("Phone Number")
                        specialties = get_specialties(db)
                        spec_options = {s.name: s.id for s in specialties}
                        new_spec = st.selectbox("Specialty", list(spec_options.keys()) if specialties else ["None"])
                        new_exp = st.number_input("Experience (Years)", min_value=0, max_value=60, value=5)
                        new_fee = st.number_input("Consultation Fee ($)", min_value=0.0, max_value=2000.0, value=100.0, step=5.0)
                    new_bio = st.text_area("Biography")
                    
                    if st.form_submit_button("Create Doctor User & Profile"):
                        if not specialties:
                            st.error("Please create a specialty first in the 'Medical Specialties' tab.")
                        elif new_name and new_email and new_pass:
                            try:
                                user = register_user(db, new_name, new_email, new_pass, "Doctor", new_gender, new_phone)
                                add_doctor_profile(db, user.id, spec_options[new_spec], new_bio, int(new_exp), float(new_fee))
                                st.success(f"✅ Successfully created Doctor {new_name}!")
                            except ValueError as e:
                                st.error(str(e))
                        else:
                            st.warning("Please fill in name, email, and password.")

            # ── Sub-Tab 2: Assign Profile
            with doc_tab2:
                st.markdown("#### Update Existing Doctor Profile")
                docs_users  = db.query(User).filter(User.role == "Doctor").all()
                specialties = get_specialties(db)

                if not docs_users:
                    st.info("No registered doctors.")
                else:
                    doc_user_map      = {u.full_name: u.id for u in docs_users}
                    sel_doc_name      = st.selectbox("Select Doctor", list(doc_user_map.keys()), key="assign_doc")
                    sel_doc_id        = doc_user_map[sel_doc_name]

                    spec_map          = {s.name: s.id for s in specialties}
                    if spec_map:
                        sel_spec_name     = st.selectbox("Assign Specialty", list(spec_map.keys()), key="assign_spec")
                        sel_spec_id       = spec_map[sel_spec_name]

                        experience        = st.number_input("Years of Experience", min_value=0, max_value=60, value=5, key="assign_exp")
                        fee               = st.number_input("Consultation Fee ($)", min_value=0.0, max_value=1000.0, value=75.0, step=5.0, key="assign_fee")
                        bio               = st.text_area("Doctor Bio", "Experienced medical professional dedicated to patient care.", key="assign_bio")

                        if st.button("💾 Save Doctor Profile", use_container_width=True):
                            add_doctor_profile(db, sel_doc_id, sel_spec_id, bio, int(experience), float(fee))
                            st.success(f"✅ Doctor profile for **{sel_doc_name}** saved!")
                    else:
                        st.warning("No specialties available.")

            # ── Sub-Tab 3: Manage Availability
            with doc_tab3:
                st.markdown("#### Manage Availability Slots")
                all_doctors = db.query(Doctor).all()
                if not all_doctors:
                    st.info("No doctors found with complete profiles.")
                else:
                    doc_map = {db.query(User).filter(User.id == d.user_id).first().full_name: d.id for d in all_doctors}
                    sel_avail_doc = st.selectbox("Select Doctor", list(doc_map.keys()), key="avail_doc")
                    sel_avail_id = doc_map[sel_avail_doc]
                    
                    with st.form("add_slot_form"):
                        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        day_sel = st.selectbox("Day of Week", day_names)
                        day_idx = day_names.index(day_sel)
                        
                        t1, t2 = st.columns(2)
                        with t1:
                            start_t = st.time_input("Start Time", value=time(9, 0))
                        with t2:
                            end_t = st.time_input("End Time", value=time(17, 0))
                        
                        if st.form_submit_button("Add Slot"):
                            add_doctor_slot(db, sel_avail_id, day_idx, start_t, end_t)
                            st.success("Slot added successfully!")
                    
                    st.markdown("##### Current Slots")
                    slots = db.query(DoctorSlot).filter(DoctorSlot.doctor_id == sel_avail_id).all()
                    if slots:
                        for s in slots:
                            col_s1, col_s2 = st.columns([3, 1])
                            with col_s1:
                                st.markdown(f"**{day_names[s.day_of_week]}**: {s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}")
                            with col_s2:
                                if st.button("Delete", key=f"del_slot_{s.id}"):
                                    remove_doctor_slot(db, s.id)
                                    st.rerun()
                    else:
                        st.info("No slots assigned.")

        # ── TAB 3: Medical Specialties ────────────────────────────────────────
        with tab3:
            st.markdown("### 🏥 Medical Specialties")
            spec_tab1, spec_tab2 = st.tabs(["📋 View Specialties", "➕ Add Specialty"])
            
            with spec_tab1:
                specialties = get_specialties(db)
                if specialties:
                    for spec in specialties:
                        doc_count = db.query(Doctor).filter(Doctor.specialty_id == spec.id).count()
                        st.markdown(
                            f"""<div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
                                        border-left:4px solid #a855f7;border-radius:10px;padding:14px 18px;margin-bottom:10px;">
                                <span style="font-size:1.4rem;">{spec.icon or '🏥'}</span>
                                <span style="font-weight:700;color:#fff;margin-left:10px;">{spec.name}</span>
                                <span style="float:right;color:#a855f7;font-size:.85rem;">{doc_count} doctor(s)</span>
                                <p style="margin:6px 0 0;color:#9ca3af;font-size:.88rem;">{spec.description or 'No description.'}</p>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No specialties configured.")
            
            with spec_tab2:
                with st.form("add_specialty_form"):
                    s_name = st.text_input("Specialty Name", placeholder="e.g. Cardiology")
                    s_icon = st.text_input("Icon Emoji", placeholder="e.g. ❤️")
                    s_desc = st.text_area("Description")
                    if st.form_submit_button("Add Specialty"):
                        if s_name:
                            create_specialty(db, s_name, s_desc, s_icon)
                            st.success(f"✅ Added {s_name} successfully!")
                            st.rerun()
                        else:
                            st.error("Name is required.")

        # ── TAB 4: Patient Directory ──────────────────────────────────────────
        with tab4:
            st.markdown("### 🧑‍⚕️ Registered Patient Directory")
            search = st.text_input("🔍 Search patients by name or email", placeholder="Type to search…")
            patients = db.query(User).filter(User.role == "Patient").all()
            if search:
                patients = [p for p in patients if search.lower() in p.full_name.lower() or search.lower() in (p.email or "").lower()]

            st.markdown(f"**{len(patients)} patient(s) found**")
            for p in patients:
                record_count = db.query(HealthRecord).filter(HealthRecord.patient_id == p.id).count()
                appt_count   = db.query(Appointment).filter(Appointment.patient_id == p.id).count()
                st.markdown(
                    f"""<div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
                                border-left:4px solid #22c55e;border-radius:10px;padding:14px 18px;margin-bottom:10px;">
                        <span style="font-weight:700;color:#fff;">🧑‍⚕️ {p.full_name}</span>
                        <span style="float:right;color:#9ca3af;font-size:.85rem;">{p.email}</span>
                        <p style="margin:6px 0 0;color:#9ca3af;font-size:.88rem;">
                            ⚧ {p.gender or 'N/A'} &nbsp;|&nbsp; 📱 {p.phone or 'N/A'}
                            &nbsp;|&nbsp; 🩺 {record_count} records &nbsp;|&nbsp; 📅 {appt_count} appts
                        </p>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # ── TAB 5: All Appointments ───────────────────────────────────────────
        with tab5:
            st.markdown("### 📅 All System Appointments")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                status_filter = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled"], key="admin_appt_filter")
            with col_f2:
                search_appt = st.text_input("🔍 Search by Patient/Doctor Name")
                
            all_appts = db.query(Appointment).order_by(Appointment.scheduled_date.desc()).all()
            if status_filter != "All":
                all_appts = [a for a in all_appts if a.status == status_filter]
                
            if search_appt:
                filtered_appts = []
                for a in all_appts:
                    pat = db.query(User).filter(User.id == a.patient_id).first()
                    doc_u = db.query(User).join(Doctor, Doctor.user_id == User.id).filter(Doctor.id == a.doctor_id).first()
                    pat_name = pat.full_name.lower() if pat else ""
                    doc_name = doc_u.full_name.lower() if doc_u else ""
                    if search_appt.lower() in pat_name or search_appt.lower() in doc_name:
                        filtered_appts.append(a)
                all_appts = filtered_appts

            st.markdown(f"**{len(all_appts)} appointment(s)**")
            for appt in all_appts:
                patient = db.query(User).filter(User.id == appt.patient_id).first()
                doctor_user = db.query(User).join(Doctor, Doctor.user_id == User.id).filter(Doctor.id == appt.doctor_id).first()
                status_color = {"Scheduled": "#3b82f6", "Completed": "#22c55e", "Cancelled": "#ef4444"}.get(appt.status, "#9ca3af")
                
                with st.expander(f"{appt.scheduled_date} | {patient.full_name if patient else 'Unknown'} → {doctor_user.full_name if doctor_user else 'Unknown'} ({appt.status})"):
                    st.markdown(f"**Reason:** {appt.reason or 'Not specified'}")
                    st.markdown(f"**Time:** {appt.start_time.strftime('%I:%M %p') if appt.start_time else ''} - {appt.end_time.strftime('%I:%M %p') if appt.end_time else 'TBD'}")
                    st.markdown(f"**Source:** {appt.source or 'Manual'}")
                    st.markdown(f"**Created At:** {appt.created_at}")
                    
                    if appt.status == "Scheduled":
                        if st.button("Cancel Appointment", key=f"cancel_{appt.id}"):
                            appt.status = "Cancelled"
                            db.commit()
                            st.success("Appointment cancelled.")
                            st.rerun()

        # ── TAB 6: Health Records ─────────────────────────────────────────────
        with tab6:
            st.markdown("### 🩺 Global Health Records")
            records = db.query(HealthRecord).order_by(HealthRecord.recorded_at.desc()).limit(100).all()
            if records:
                for rec in records:
                    pat = db.query(User).filter(User.id == rec.patient_id).first()
                    doc = db.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
                    doc_u = db.query(User).filter(User.id == doc.user_id).first() if doc else None
                    
                    st.markdown(
                        f"""<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.1);
                                    border-left:4px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:8px;">
                            <div style="display:flex;justify-content:space-between;">
                                <strong>Patient: {pat.full_name if pat else 'Unknown'}</strong>
                                <span style="color:#9ca3af;font-size:0.8rem;">{rec.recorded_at.strftime('%Y-%m-%d %H:%M') if rec.recorded_at else ''}</span>
                            </div>
                            <div style="color:#cbd5e1;font-size:0.9rem;margin-top:4px;">
                                Doctor: {doc_u.full_name if doc_u else 'System'} &nbsp;|&nbsp; Specialty: {rec.specialty_type or 'General'}
                            </div>
                            <div style="color:#e2e8f0;font-size:0.9rem;margin-top:6px;background:rgba(0,0,0,0.2);padding:8px;border-radius:4px;">
                                <strong>Diagnosis:</strong> {rec.diagnosis or 'None'}<br/>
                                <strong>Notes:</strong> {rec.notes or 'No notes'}
                            </div>
                        </div>""",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No health records found in the system.")

        # ── TAB 7: Prescriptions ──────────────────────────────────────────────
        with tab7:
            st.markdown("### 💊 System-Wide Prescriptions")
            st.markdown(
                """<div style="background:linear-gradient(135deg,rgba(168,85,247,.15),rgba(168,85,247,.03));
                            border:1px solid rgba(168,85,247,.3);border-radius:12px;
                            padding:14px 18px;margin-bottom:16px;">
                    <div style="color:#a855f7;font-weight:700;">🛡️ Admin Read-Only Access</div>
                    <div style="color:#9ca3af;font-size:0.85rem;">
                        Administrators have <b>read-only</b> access to inspect all system-wide prescriptions. 
                        Prescription creation (issuance), modification, and deletion (CRUD) are restricted to authorized doctors.
                    </div>
                </div>""",
                unsafe_allow_html=True
            )
            records = db.query(HealthRecord).order_by(HealthRecord.recorded_at.desc()).all()
            rx_records = [r for r in records if _is_real_prescription(r)]
            
            if rx_records:
                # Search filter
                search_rx = st.text_input("🔍 Search Prescriptions", placeholder="Filter by patient name, prescribing doctor, or medication...", key="tab7_rx_search")
                if search_rx:
                    filtered_rx = []
                    sq = search_rx.lower()
                    for r in rx_records:
                        pat = db.query(User).filter(User.id == r.patient_id).first()
                        doc = db.query(Doctor).filter(Doctor.id == r.doctor_id).first()
                        doc_u = db.query(User).filter(User.id == doc.user_id).first() if doc else None
                        pat_name = pat.full_name.lower() if pat else ""
                        doc_name = doc_u.full_name.lower() if doc_u else ""
                        notes = (r.notes or "").lower()
                        if sq in pat_name or sq in doc_name or sq in notes:
                            filtered_rx.append(r)
                    rx_records = filtered_rx

                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("💊 Total Prescriptions", len(rx_records))
                m2.metric("🧑‍⚕️ Unique Patients", len(set(r.patient_id for r in rx_records)))
                m3.metric("👨‍⚕️ Prescribing Doctors", len(set(r.doctor_id for r in rx_records if r.doctor_id)))

                st.markdown("---")
                if rx_records:
                    _render_read_only_prescriptions_table(rx_records, db, is_admin=True)
                else:
                    st.warning("No prescriptions match your search criteria.")
            else:
                st.info("No prescriptions have been issued yet.")

        # ── TAB 8: User Management ────────────────────────────────────────────
        with tab8:
            st.markdown("### 👥 All System Users")
            search_u = st.text_input("🔍 Search by name or email", placeholder="Type to search…", key="user_search")
            role_filter = st.selectbox("Filter by Role", ["All", "Admin", "Doctor", "Patient"], key="user_role_filter")

            all_users = db.query(User).all()
            if search_u:
                all_users = [u for u in all_users if search_u.lower() in u.full_name.lower() or search_u.lower() in (u.email or "").lower()]
            if role_filter != "All":
                all_users = [u for u in all_users if u.role == role_filter]

            st.markdown(f"**{len(all_users)} user(s) found**")
            role_colors = {"Admin": "#a855f7", "Doctor": "#3b82f6", "Patient": "#22c55e"}
            for u in all_users:
                rc = role_colors.get(u.role, "#9ca3af")
                st.markdown(
                    f"""<div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
                                border-radius:10px;padding:12px 18px;margin-bottom:8px;
                                display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="color:#fff;font-weight:700;">👤 {u.full_name}</span>
                            <span style="color:#9ca3af;font-size:.85rem;margin-left:12px;">{u.email}</span>
                        </div>
                        <span style="background:{rc}22;color:{rc};padding:2px 12px;border-radius:12px;font-size:.8rem;font-weight:700;">{u.role}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )


        # ── TAB 9: Pharmacy ───────────────────────────────────────────────────
        with tab9:
            render_admin_pharmacy_view()

    finally:
        db.close()


def render_admin_pharmacy_view():
    db = SessionLocal()
    try:
        seed_medicines(db)
        st.markdown("### 🏪 Pharmacy Management")

        BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        def _stock_badge_admin(qty):
            if qty == 0:
                return "<span style='background:#ef444422;color:#ef4444;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700;'>❌ Out of Stock</span>"
            if qty <= 20:
                return f"<span style='background:#f59e0b22;color:#f59e0b;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700;'>⚠️ Low ({qty})</span>"
            return f"<span style='background:#22c55e22;color:#22c55e;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700;'>✅ In Stock ({qty})</span>"

        def _expiry_badge_admin(expiry_date_val):
            if not expiry_date_val:
                return ""
            today_d = date.today()
            days_left = (expiry_date_val - today_d).days
            if days_left < 0:
                return f"<span style='background:#ef444422;color:#ef4444;padding:2px 10px;border-radius:20px;font-size:.73rem;font-weight:700;'>❌ EXPIRED ({expiry_date_val.strftime('%b %Y')})</span>"
            if days_left <= 180:
                return f"<span style='background:#f59e0b22;color:#f59e0b;padding:2px 10px;border-radius:20px;font-size:.73rem;font-weight:700;'>⚠️ Exp: {expiry_date_val.strftime('%d %b %Y')}</span>"
            return f"<span style='background:#22c55e22;color:#22c55e;padding:2px 10px;border-radius:20px;font-size:.73rem;font-weight:700;'>✅ Exp: {expiry_date_val.strftime('%d %b %Y')}</span>"

        ph_tab1, ph_tab2, ph_tab3, ph_tab4 = st.tabs([
            "📦 Medicine Inventory", "📊 Stock Management", "➕ Add Medicine", "🧾 All Orders"
        ])

        # ── Inventory ─────────────────────────────────────────────────────
        with ph_tab1:
            medicines = get_all_medicines(db, include_inactive=True)
            if not medicines:
                st.info("No medicines in inventory. Add some using the 'Add Medicine' tab.")
            else:
                total_meds   = len(medicines)
                active_meds  = sum(1 for m in medicines if m.is_active)
                low_stock    = sum(1 for m in medicines if 0 < m.stock_qty <= 20)
                out_of_stock = sum(1 for m in medicines if m.stock_qty == 0)
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("💊 Total Medicines", total_meds)
                k2.metric("✅ Active", active_meds)
                k3.metric("⚠️ Low Stock", low_stock)
                k4.metric("❌ Out of Stock", out_of_stock)
                st.markdown("---")

                for med in medicines:
                    status_color = med.color_theme if med.is_active else "#6b7280"
                    img_abs = os.path.join(BASE_PATH, med.image_path.replace("/", os.sep)) if med.image_path else None
                    has_image = img_abs and os.path.exists(img_abs)
                    exp_suffix = f"  |  Exp: {med.expiry_date.strftime('%d %b %Y')}" if med.expiry_date else ""

                    with st.expander(
                        f"{'✅' if med.is_active else '⛔'} {med.name}  |  "
                        f"${float(med.price):.2f}  |  Stock: {med.stock_qty}{exp_suffix}"
                    ):
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            if has_image:
                                st.image(img_abs, width=140)
                            else:
                                emoji_map = {
                                    "Cardiology": "❤️", "Antibiotics": "🧬",
                                    "Cough & Cold": "🍃", "Cholesterol": "🫀",
                                    "Diabetes": "💉", "Pain Relief": "🩹",
                                    "Thyroid": "🦋", "Ophthalmology": "👁️",
                                    "Dermatology": "🧴",
                                }
                                st.markdown(
                                    f"""<div style='background:linear-gradient(135deg,{status_color}22,{status_color}08);
                                        border:2px solid {status_color}55;border-radius:10px;
                                        height:120px;display:flex;align-items:center;justify-content:center;
                                        font-size:3rem;'>{emoji_map.get(med.category or '', '💊')}</div>""",
                                    unsafe_allow_html=True,
                                )
                        with c2:
                            rx_badge = '<span style="background:#a855f722;color:#a855f7;padding:2px 10px;border-radius:20px;font-size:.75rem;">Rx Required</span>' if med.requires_prescription else '<span style="background:#22c55e22;color:#22c55e;padding:2px 10px;border-radius:20px;font-size:.75rem;">OTC</span>'
                            mfg_html  = f"<div style='font-size:.8rem;color:#9ca3af;'>🏭 Mfg: <b>{med.manufacture_date.strftime('%d %b %Y')}</b></div>" if med.manufacture_date else ""
                            st.markdown(
                                f"""<div style='padding-left:12px;'>
                                    <div style='font-weight:800;color:#fff;font-size:1.05rem;'>{med.name}</div>
                                    <div style='color:#9ca3af;font-size:.85rem;margin-bottom:4px;'>{med.generic_name or ''}</div>
                                    <div style='margin:6px 0;display:flex;flex-wrap:wrap;gap:6px;'>
                                        <span style='background:{status_color}22;color:{status_color};padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700;'>{med.category or 'General'}</span>
                                        {rx_badge}
                                        {_stock_badge_admin(med.stock_qty)}
                                    </div>
                                    <div style='color:#cbd5e1;font-size:.88rem;margin-bottom:8px;'>{med.description or ''}</div>
                                    <div style='display:flex;flex-wrap:wrap;gap:16px;align-items:center;'>
                                        <span style='color:{status_color};font-weight:800;font-size:1.1rem;'>${float(med.price):.2f}</span>
                                        <span style='color:#9ca3af;font-size:.82rem;'>/ {med.unit}</span>
                                    </div>
                                    <div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;'>
                                        {mfg_html}
                                        {_expiry_badge_admin(med.expiry_date)}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        st.markdown("---")
                        toggle_label = "⛔ Deactivate" if med.is_active else "✅ Reactivate"
                        if st.button(toggle_label, key=f"toggle_{med.id}"):
                            if med.is_active:
                                deactivate_medicine(db, med.id)
                            else:
                                reactivate_medicine(db, med.id)
                            st.rerun()

        # ── Stock Management ──────────────────────────────────────────────
        with ph_tab2:
            st.markdown("#### 📊 Stock & Price Management")
            st.markdown(
                "<p style='color:#9ca3af;font-size:.9rem;'>Update stock quantities, prices, and batch dates for any medicine.</p>",
                unsafe_allow_html=True,
            )
            medicines_all = get_all_medicines(db, include_inactive=True)
            if not medicines_all:
                st.info("No medicines to manage.")
            else:
                stock_filter = st.selectbox(
                    "Show medicines",
                    ["All", "Low Stock (≤20)", "Out of Stock", "In Stock"],
                    key="stock_filter"
                )
                filtered = medicines_all
                if stock_filter == "Low Stock (≤20)":
                    filtered = [m for m in filtered if 0 < m.stock_qty <= 20]
                elif stock_filter == "Out of Stock":
                    filtered = [m for m in filtered if m.stock_qty == 0]
                elif stock_filter == "In Stock":
                    filtered = [m for m in filtered if m.stock_qty > 20]

                st.markdown(f"<p style='color:#9ca3af;font-size:.85rem;'>{len(filtered)} medicine(s) shown</p>", unsafe_allow_html=True)

                for med in filtered:
                    today_d = date.today()
                    expiry_color = "#9ca3af"
                    if med.expiry_date:
                        days_left = (med.expiry_date - today_d).days
                        expiry_color = "#ef4444" if days_left < 0 else "#f59e0b" if days_left <= 180 else "#22c55e"
                    exp_tag = f'<span style="background:{expiry_color}22;color:{expiry_color};padding:2px 10px;border-radius:20px;font-size:.73rem;font-weight:600;">Exp: {med.expiry_date.strftime("%b %Y")}</span>' if med.expiry_date else ""

                    st.markdown(
                        f"""<div style='background:rgba(255,255,255,.04);border:1px solid {med.color_theme}44;
                            border-left:4px solid {med.color_theme};border-radius:12px;
                            padding:14px 18px;margin-bottom:4px;'>
                            <div style='display:flex;justify-content:space-between;align-items:center;'>
                                <div>
                                    <span style='font-weight:700;color:#fff;font-size:.95rem;'>{med.name}</span>
                                    <span style='color:#9ca3af;font-size:.8rem;margin-left:10px;'>{med.unit}</span>
                                </div>
                                <div style='display:flex;gap:10px;'>
                                    <span style='background:{med.color_theme}22;color:{med.color_theme};padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700;'>Current: {med.stock_qty}</span>
                                    {exp_tag}
                                </div>
                            </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    col_s, col_p, col_mfg, col_exp, col_save = st.columns([2, 2, 2, 2, 1.5])
                    with col_s:
                        new_stock = st.number_input(
                            f"Stock (units)", min_value=0, max_value=9999,
                            value=med.stock_qty, key=f"stock_{med.id}"
                        )
                    with col_p:
                        new_price = st.number_input(
                            "Price ($)", min_value=0.01, max_value=9999.0,
                            value=float(med.price), step=0.50,
                            key=f"price_{med.id}"
                        )
                    with col_mfg:
                        new_mfg = st.date_input(
                            "Manufacture Date", value=med.manufacture_date,
                            key=f"mfg_{med.id}"
                        )
                    with col_exp:
                        new_exp_date = st.date_input(
                            "Expiry Date", value=med.expiry_date,
                            key=f"exp_{med.id}"
                        )
                    with col_save:
                        st.write("")
                        st.write("")
                        if st.button("💾 Save", key=f"save_all_{med.id}", use_container_width=True):
                            from services.pharmacy_service import update_medicine
                            update_medicine(db, med.id,
                                            stock_qty=new_stock,
                                            price=new_price,
                                            manufacture_date=new_mfg,
                                            expiry_date=new_exp_date)
                            st.success(f"✅ {med.name} updated!")
                            st.rerun()

                    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

        # ── Add Medicine ──────────────────────────────────────────────────
        with ph_tab3:
            st.markdown("#### ➕ Add New Medicine")
            with st.form("add_medicine_form"):
                m1, m2 = st.columns(2)
                with m1:
                    m_name     = st.text_input("Medicine Name *", placeholder="e.g. Metformin 500mg Tablets")
                    m_generic  = st.text_input("Generic Name", placeholder="e.g. Metformin HCl")
                    m_category = st.selectbox("Category", [
                        "Cardiology", "Antibiotics", "Cough & Cold", "Cholesterol",
                        "Diabetes", "Pain Relief", "Thyroid", "Ophthalmology",
                        "Dermatology", "Vitamins", "Other"
                    ])
                    m_price = st.number_input("Price ($)", min_value=0.01, max_value=9999.0, value=10.0, step=0.5)
                    m_stock = st.number_input("Initial Stock (units)", min_value=0, max_value=9999, value=100)
                with m2:
                    m_unit     = st.text_input("Unit", placeholder="e.g. Tablet (30 pack)")
                    m_color    = st.color_picker("Card Accent Color", "#a855f7")
                    m_rx       = st.checkbox("Requires Prescription")
                    m_image    = st.text_input("Image Path (relative)", placeholder="assets/pharmacy/medicine.jpg")
                    m_mfg_date = st.date_input("Manufacture Date", value=date.today(), key="add_mfg_date")
                    m_exp_date = st.date_input("Expiry Date",
                                               value=date(date.today().year + 2, date.today().month, date.today().day),
                                               key="add_exp_date")
                m_desc = st.text_area("Description", placeholder="Brief description of the medicine and its uses.")
                if st.form_submit_button("➕ Add Medicine", use_container_width=True):
                    if m_name:
                        add_medicine(
                            db, m_name, m_generic, m_category, m_desc,
                            m_price, m_stock, m_unit or "Unit", m_rx,
                            m_image or None, m_color,
                            manufacture_date=m_mfg_date,
                            expiry_date=m_exp_date,
                        )
                        st.success(f"✅ {m_name} added to pharmacy inventory!")
                        st.rerun()
                    else:
                        st.error("Medicine name is required.")

        # ── All Orders ────────────────────────────────────────────────────
        with ph_tab4:
            st.markdown("#### 🧾 All Patient Pharmacy Orders")
            all_orders = get_all_orders(db)
            if not all_orders:
                st.info("No pharmacy orders yet.")
            else:
                status_colors = {"Pending": "#f59e0b", "Confirmed": "#3b82f6", "Delivered": "#22c55e", "Cancelled": "#ef4444"}
                status_icons  = {"Pending": "⏳", "Confirmed": "✅", "Delivered": "🚚", "Cancelled": "❌"}

                for order in all_orders:
                    patient = db.query(User).filter(User.id == order.patient_id).first()
                    sc = status_colors.get(order.status, "#9ca3af")
                    si = status_icons.get(order.status, "📋")
                    with st.expander(
                        f"#{order.id} | {patient.full_name if patient else 'Unknown'} | "
                        f"${float(order.total_amount):.2f} | {si} {order.status} | "
                        f"{order.created_at.strftime('%d %b %Y, %H:%M')}"
                    ):
                        for it in order.items:
                            med = it.medicine
                            st.markdown(
                                f"""<div style='display:flex;justify-content:space-between;
                                    padding:8px 12px;background:rgba(255,255,255,.04);
                                    border-radius:8px;margin-bottom:6px;'>
                                    <span style='color:#fff;'>💊 {med.name if med else 'Unknown'}</span>
                                    <span style='color:#9ca3af;'>Qty: {it.quantity} × ${float(it.unit_price):.2f}</span>
                                    <span style='color:#10b981;font-weight:700;'>${float(it.unit_price * it.quantity):.2f}</span>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                        st.markdown(
                            f"""<div style='text-align:right;margin-top:8px;font-weight:800;color:#fff;'>
                                Total: <span style='color:{sc};'>${float(order.total_amount):.2f}</span>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                        status_options = ["Pending", "Confirmed", "Delivered", "Cancelled"]
                        new_status = st.selectbox(
                            "Update Status", status_options,
                            index=status_options.index(order.status) if order.status in status_options else 0,
                            key=f"ord_status_{order.id}"
                        )
                        if st.button("💾 Update Status", key=f"save_ord_{order.id}"):
                            update_order_status(db, order.id, new_status)
                            st.success(f"Order #{order.id} status → {new_status}")
                            st.rerun()

    finally:
        db.close()
