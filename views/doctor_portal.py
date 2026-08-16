import streamlit as st
from core.database import SessionLocal
from services.analytics_service import get_doctor_stats
from services.appointment_service import get_appointments_for_user
from services.health_service import add_health_record
from services.doctor_service import add_doctor_profile
from models.models import User, Appointment, Doctor, Specialty, HealthRecord
from views.components import html, format_doctor_name

# ── Specialty → vitals form renderer ──────────────────────────────────────────
def _render_vitals_form(specialty_name: str):
    """Render vitals input fields based on the doctor's specialty. Returns a dict of field values."""
    sn = specialty_name.lower() if specialty_name else ""
    fields = {}

    if "cardio" in sn or "cardiac" in sn or "electro" in sn:
        st.markdown("##### ❤️ Cardiac Vitals")
        c1, c2 = st.columns(2)
        with c1:
            fields["heart_rate"]        = st.number_input("Heart Rate (bpm)", min_value=30, max_value=250, value=72)
            fields["blood_pressure"]    = st.text_input("Blood Pressure (mmHg)", value="120/80", placeholder="e.g. 120/80")
            fields["troponin"]          = st.number_input("Troponin (ng/mL)", min_value=0.000, max_value=50.000, value=0.015, format="%.3f", step=0.005)
            fields["ejection_fraction"] = st.number_input("Ejection Fraction (%)", min_value=10, max_value=85, value=55)
        with c2:
            fields["cardiac_output"]    = st.number_input("Cardiac Output (L/min)", min_value=1.0, max_value=15.0, value=5.0, step=0.1)
            fields["pulse_oximetry"]    = st.number_input("SpO2 (%)", min_value=50, max_value=100, value=98)
            fields["ecg_note"]          = st.selectbox("ECG Rhythm", [
                "Normal Sinus Rhythm", "Sinus Tachycardia", "Sinus Bradycardia",
                "Atrial Fibrillation", "Premature Ventricular Contractions"
            ])

    elif "dentist" in sn or "dental" in sn:
        st.markdown("##### 🦷 Dental Checkup")
        c1, c2 = st.columns(2)
        with c1:
            fields["teeth_condition"]  = st.selectbox("Teeth Condition", [
                "Healthy", "Minor Cavities", "Multiple Cavities", "Plaque Build-up",
                "Cracked Tooth", "Tooth Decay"
            ])
            fields["gum_health"]       = st.selectbox("Gum Health", [
                "Healthy", "Mild Gingivitis", "Moderate Gingivitis", "Periodontitis"
            ])
            fields["procedure_done"]   = st.selectbox("Procedure Performed", [
                "None", "Scaling & Polishing", "Tooth Filling", "Root Canal Treatment",
                "Tooth Extraction", "Orthodontic Adjustment", "Whitening"
            ])
        with c2:
            fields["xray_finding"]     = st.text_input("X-Ray Finding", placeholder="e.g. No abnormalities / Periapical abscess")
            fields["next_dental_visit"]= st.selectbox("Next Visit Recommended In", [
                "1 month", "3 months", "6 months", "1 year"
            ])

    elif "ophthal" in sn or "eye" in sn:
        st.markdown("##### 👁️ Eye Examination")
        c1, c2 = st.columns(2)
        with c1:
            fields["right_eye_vision"] = st.text_input("Right Eye Vision", value="6/6", placeholder="e.g. 6/6, 6/12")
            fields["left_eye_vision"]  = st.text_input("Left Eye Vision", value="6/6", placeholder="e.g. 6/6, 6/12")
            fields["eye_pressure_iop"] = st.text_input("IOP (Intraocular Pressure)", value="14 mmHg", placeholder="e.g. 14 mmHg")
        with c2:
            fields["eye_condition"]    = st.selectbox("Diagnosed Eye Condition", [
                "None", "Myopia", "Hyperopia", "Astigmatism", "Cataract",
                "Glaucoma", "Diabetic Retinopathy", "Macular Degeneration"
            ])
            fields["retina_status"]    = st.selectbox("Retina Status", [
                "Normal", "Early Retinopathy", "Moderate Retinopathy",
                "Severe Retinopathy", "Retinal Detachment"
            ])

    elif "pulmo" in sn or "chest" in sn or "lung" in sn:
        st.markdown("##### 🫁 Pulmonary / Chest Examination")
        c1, c2 = st.columns(2)
        with c1:
            fields["respiratory_rate"]  = st.number_input("Respiratory Rate (breaths/min)", min_value=8, max_value=60, value=16)
            fields["oxygen_saturation"] = st.number_input("Oxygen Saturation SpO2 (%)", min_value=50, max_value=100, value=97)
            fields["fev1"]              = st.text_input("FEV1 (Spirometry Result)", value="82%", placeholder="e.g. 82% of predicted")
        with c2:
            fields["lung_condition"]    = st.selectbox("Lung Condition", [
                "Healthy", "Asthma", "COPD", "Bronchitis", "Pneumonia",
                "Pulmonary Fibrosis", "Pleural Effusion", "Tuberculosis"
            ])
            fields["chest_xray_finding"] = st.text_input("Chest X-Ray Finding", placeholder="e.g. Clear lung fields / Consolidation at right lower lobe")

    elif "ortho" in sn or "injury" in sn or "bone" in sn or "sport" in sn:
        st.markdown("##### 🦵 Orthopedic / Injury Assessment")
        c1, c2 = st.columns(2)
        with c1:
            fields["injury_location"]  = st.text_input("Injury / Pain Location", placeholder="e.g. Right Knee, Left Ankle, Lower Back")
            fields["fracture_type"]    = st.selectbox("Fracture / Injury Type", [
                "None", "Hairline Fracture", "Stress Fracture", "Compound Fracture",
                "Dislocation", "Ligament Tear", "Muscle Strain", "Sprain"
            ])
            fields["mobility_score"]   = st.slider("Mobility Score (0 = No movement, 10 = Full mobility)", 0, 10, 7)
        with c2:
            fields["mri_xray_finding"] = st.text_input("MRI / X-Ray Finding", placeholder="e.g. ACL Partial Tear, No structural damage")
            fields["treatment_plan"]   = st.selectbox("Treatment Plan", [
                "Rest & Observation", "Physiotherapy (4 weeks)", "Physiotherapy (6 weeks)",
                "Cast / Splint", "Surgical Intervention", "Pain Management Only", "Rehabilitation Program"
            ])
    else:
        # Generic / Unknown specialty fallback
        st.markdown("##### 🩺 General Health Assessment")
        c1, c2 = st.columns(2)
        with c1:
            fields["heart_rate"]     = st.number_input("Heart Rate (bpm)", min_value=30, max_value=250, value=72)
            fields["blood_pressure"] = st.text_input("Blood Pressure", value="120/80")
            fields["pulse_oximetry"] = st.number_input("SpO2 (%)", min_value=50, max_value=100, value=98)
        with c2:
            fields["respiratory_rate"] = st.number_input("Respiratory Rate (breaths/min)", min_value=8, max_value=60, value=16)

    return fields


def render_doctor_portal():
    user = st.session_state.user
    db = SessionLocal()
    try:
        stats = get_doctor_stats(db, user["id"])

        # Fetch doctor profile info
        doc_profile = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
        spec_name = "General Practice"
        spec_icon = "🩺"
        experience = 0
        fee = 0.0
        bio = ""
        if doc_profile:
            if doc_profile.specialty:
                spec_name = doc_profile.specialty.name
                spec_icon = doc_profile.specialty.icon or "🩺"
            experience = doc_profile.experience_years or 0
            fee = float(doc_profile.consultation_fee or 0)
            bio = doc_profile.bio or ""

        # Fetch today's appointments
        import datetime
        today = datetime.date.today()
        today_appts = get_appointments_for_user(db, user["id"], "Doctor")
        today_appts = [a for a in today_appts if a.scheduled_date == today and a.status == "Scheduled"]
        pending_appts = [a for a in get_appointments_for_user(db, user["id"], "Doctor") if a.status == "Scheduled"]

        # ── Welcome Banner ────────────────────────────────────────────────────
        greeting_hour = datetime.datetime.now().hour
        greeting = "Good Morning" if greeting_hour < 12 else ("Good Afternoon" if greeting_hour < 17 else "Good Evening")

        html(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #3b82f6 100%);
                    border-radius: 20px; padding: 28px 32px; margin-bottom: 24px;
                    box-shadow: 0 10px 40px rgba(37, 99, 235, 0.35);">
            <div style="display:flex; align-items:center; gap:18px;">
                <div style="font-size: 3.2rem; background: rgba(255,255,255,0.15);
                            border-radius: 50%; width: 72px; height: 72px;
                            display:flex; align-items:center; justify-content:center;">
                    👨‍⚕️
                </div>
                <div>
                    <div style="font-size: 0.85rem; color: rgba(255,255,255,0.75); font-weight: 600;
                                text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                        {greeting}, Doctor 👋
                    </div>
                    <div style="font-size: 1.7rem; font-weight: 800; color: #ffffff; line-height: 1.1;">
                        {format_doctor_name(user['full_name'])}
                    </div>
                    <div style="margin-top: 6px; display:flex; gap:10px; flex-wrap:wrap;">
                        <span style="background: rgba(255,255,255,0.2); color:#fff; padding: 3px 12px;
                                     border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
                            {spec_icon} {spec_name}
                        </span>
                        <span style="background: rgba(255,255,255,0.2); color:#fff; padding: 3px 12px;
                                     border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
                            ⭐ {experience} yrs Experience
                        </span>
                        <span style="background: rgba(34,197,94,0.3); color:#bbf7d0; padding: 3px 12px;
                                     border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
                            🟢 Online & Available
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """)

        # ── Key Metrics Row ────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            html(f"""<div class="medical-card" style="text-align:center; border-top: 3px solid #3b82f6; padding:18px;">
                <div style="font-size:2rem; font-weight:900; color:#3b82f6;">{stats['total_appointments']}</div>
                <div style="font-size:0.8rem; color:#9ca3af; font-weight:600; margin-top:4px;">📅 Total Bookings</div>
            </div>""")
        with col2:
            html(f"""<div class="medical-card" style="text-align:center; border-top: 3px solid #22c55e; padding:18px;">
                <div style="font-size:2rem; font-weight:900; color:#22c55e;">{stats['completed_appointments']}</div>
                <div style="font-size:0.8rem; color:#9ca3af; font-weight:600; margin-top:4px;">✅ Consults Done</div>
            </div>""")
        with col3:
            html(f"""<div class="medical-card" style="text-align:center; border-top: 3px solid #f59e0b; padding:18px;">
                <div style="font-size:2rem; font-weight:900; color:#f59e0b;">{len(pending_appts)}</div>
                <div style="font-size:0.8rem; color:#9ca3af; font-weight:600; margin-top:4px;">⏳ Pending Appts</div>
            </div>""")
        with col4:
            html(f"""<div class="medical-card" style="text-align:center; border-top: 3px solid #a855f7; padding:18px;">
                <div style="font-size:2rem; font-weight:900; color:#a855f7;">{stats['active_patients']}</div>
                <div style="font-size:0.8rem; color:#9ca3af; font-weight:600; margin-top:4px;">👥 Unique Patients</div>
            </div>""")

        st.markdown("---")

        # ── Today's Schedule & Doctor Info side by side ────────────────────────
        left_col, right_col = st.columns([1.6, 1])

        with left_col:
            st.markdown("#### 📅 Today's Appointment Schedule")
            if today_appts:
                for appt in today_appts:
                    patient = db.query(User).filter(User.id == appt.patient_id).first()
                    pname = patient.full_name if patient else "Unknown"
                    html(f"""
                    <div class="medical-card" style="border-left: 4px solid #f59e0b; padding: 14px 18px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#ffffff;">👤 {pname}</span>
                            <span style="background:#fef3c7; color:#92400e; border:1px solid #fde68a;
                                         padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">Scheduled</span>
                        </div>
                        <div style="font-size:0.85rem; color:#cbd5e1; margin-top:6px;">
                            ⏰ {appt.start_time} &nbsp;|&nbsp; 💬 {appt.reason or "General Consultation"}
                        </div>
                    </div>
                    """)
            else:
                html("""<div class="medical-card" style="text-align:center; padding:30px; border: 2px dashed rgba(255,255,255,0.1);">
                    <div style="font-size:2.5rem;">🎉</div>
                    <div style="color:#9ca3af; margin-top:10px; font-size:0.9rem;">No appointments scheduled for today.</div>
                    <div style="color:#64748b; font-size:0.8rem; margin-top:4px;">Enjoy your free time, Doctor!</div>
                </div>""")

        with right_col:
            st.markdown("#### 🏥 Your Clinic Profile")
            html(f"""
            <div class="medical-card" style="border-top: 3px solid #2563eb; padding: 20px;">
                <div style="font-size:2rem; margin-bottom: 10px;">{spec_icon}</div>
                <div style="font-weight:800; color:#ffffff; font-size:1rem;">{format_doctor_name(user['full_name'])}</div>
                <div style="color:#64748b; font-size:0.8rem; margin:4px 0 12px 0;">{spec_name}</div>
                <div style="height:1px; background:rgba(255,255,255,0.08); margin-bottom:12px;"></div>
                <div style="font-size:0.84rem; color:#cbd5e1; line-height:2;">
                    📧 <b>Email:</b> {user['email']}<br>
                    🎓 <b>Experience:</b> {experience} years<br>
                    💰 <b>Consult Fee:</b> ₹{fee:.0f}<br>
                    🏷️ <b>Specialty:</b> {spec_name}
                </div>
                {f'<div style="margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08); font-size:0.82rem; color:#94a3b8; font-style:italic;">"{bio[:120]}{"..." if len(bio) > 120 else ""}"</div>' if bio else ""}
            </div>
            """)

        st.markdown("---")

        # ── Interactive Appointment Calendar ─────────────────────────────
        from views.calendar_component import render_appointment_calendar
        render_appointment_calendar(db, "Doctor", user["id"])

        st.markdown("---")

        # ── Practitioner Control Desk ──────────────────────────────────────────
        st.subheader("👨‍⚕️ Practitioner Control Desk")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📅 My Appointments",
            "💊 Prescribe & Clinical Notes",
            "📋 My Prescriptions",
            "👨‍⚕️ My Profile"
        ])

        # ── Tab 1: Appointments ────────────────────────────────────────────────
        with tab1:
            st.write("### 📋 Your Patient Appointment Schedule")

            doc_profile_appt = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
            spec_name_appt = ""
            if doc_profile_appt and doc_profile_appt.specialty:
                spec_name_appt = doc_profile_appt.specialty.name
                spec_icon_appt = doc_profile_appt.specialty.icon or "🩺"
                st.info(f"{spec_icon_appt} Showing only appointments booked with **{format_doctor_name(user['full_name'])}** under **{spec_name_appt}**")

            status_filter = st.selectbox("Filter by Appointment Status", ["All", "Scheduled", "Completed", "Cancelled"], key="portal_appt_filter")

            appointments = get_appointments_for_user(db, user["id"], "Doctor")
            if status_filter != "All":
                appointments = [a for a in appointments if a.status == status_filter]

            if appointments:
                st.markdown(f"**{len(appointments)} appointment(s) found**")
                for appt in appointments:
                    patient = db.query(User).filter(User.id == appt.patient_id).first()
                    patient_name  = patient.full_name if patient else "Unknown"
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
                            🩺 <b>Specialty:</b> {spec_name_appt or "General"} &nbsp;|&nbsp; 💬 <b>Reason:</b> {appt.reason or "General Consultation"}<br>
                            📧 <b>Email:</b> {patient_email} &nbsp;|&nbsp; 📞 <b>Phone:</b> {patient_phone or "N/A"}
                        </p>
                    </div>
                    """)

                    if appt.status == "Scheduled":
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Mark Completed", key=f"comp_{appt.id}"):
                                a = db.query(Appointment).filter(Appointment.id == appt.id).first()
                                a.status = "Completed"
                                db.commit()
                                st.success(f"Appointment with {patient_name} marked completed!")
                                st.rerun()
                        with col2:
                            if st.button("❌ Cancel", key=f"canc_{appt.id}"):
                                a = db.query(Appointment).filter(Appointment.id == appt.id).first()
                                a.status = "Cancelled"
                                db.commit()
                                st.success("Appointment cancelled.")
                                st.rerun()
            else:
                st.info(f"No {status_filter.lower()} appointments found for your schedule.")

        # ── Tab 2: Prescribe & Clinical Notes ──────────────────────────────────
        with tab2:
            st.write("### 💊 Issue Multiple Tablet Prescriptions & Clinical Notes")

            doctor_profile = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
            specialty_name = doctor_profile.specialty.name if (doctor_profile and doctor_profile.specialty) else "General"

            patients = db.query(User).filter(User.role == 'Patient').all()
            if patients:
                patient_map = {p.full_name: p.id for p in patients}
                selected_patient_name = st.selectbox("Select Patient", list(patient_map.keys()), key="portal_notes_pat_sel")
                selected_patient_id = patient_map[selected_patient_name]

                st.markdown("---")
                st.markdown("##### 🩺 Clinical Impression")
                diagnosis = st.text_input("Diagnosis / Clinical Impression", placeholder="e.g. Mild cardiac arrhythmia, stable vital signs...", key="portal_diag")

                st.markdown("##### 💊 Prescribed Medications & Tablets")

                # Initialize session state for multiple tablet rows
                if "doc_num_rx_items" not in st.session_state:
                    st.session_state.doc_num_rx_items = 1

                # Buttons to add/remove tablet rows
                btn_col1, btn_col2, _ = st.columns([1.5, 1.5, 3])
                with btn_col1:
                    if st.button("➕ Add Another Tablet", key="add_rx_btn", use_container_width=True):
                        st.session_state.doc_num_rx_items += 1
                        st.rerun()
                with btn_col2:
                    if st.session_state.doc_num_rx_items > 1:
                        if st.button("❌ Remove Last Tablet", key="rem_rx_btn", use_container_width=True):
                            st.session_state.doc_num_rx_items -= 1
                            st.rerun()

                tablets_data = []
                freq_options = [
                    "Once daily", "Twice daily", "Three times daily",
                    "Four times daily", "Every 6 hours", "Every 8 hours",
                    "Once weekly", "As needed (PRN)"
                ]
                timing_options = [
                    "After food", "Before food", "At bedtime",
                    "In the morning", "With food", "Empty stomach"
                ]

                # Load pharmacy medicines from DB and prepend to list
                from services.pharmacy_service import get_all_medicines as _get_pharm_meds
                pharm_meds = _get_pharm_meds(db)
                pharm_med_names = [m.name for m in pharm_meds if m.is_active]



                for idx in range(st.session_state.doc_num_rx_items):
                    with st.expander(f"💊 Tablet #{idx + 1} Details", expanded=True):
                        rx_col1, rx_col2 = st.columns(2)
                        with rx_col1:
                            # Master list of all medicines & pharmacy inventory
                            ALL_MEDICINES_LIST = pharm_med_names + [
                                "Paracetamol 500mg", "Paracetamol 650mg", "Paracetamol 1000mg",
                                "Aspirin 75mg", "Aspirin 150mg", "Aspirin 325mg",
                                "Ibuprofen 200mg", "Ibuprofen 400mg", "Ibuprofen 600mg",
                                "Diclofenac 50mg", "Diclofenac 75mg", "Diclofenac 100mg SR",
                                "Naproxen 250mg", "Naproxen 500mg",
                                "Tramadol 50mg", "Tramadol 100mg",
                                "Mefenamic Acid 500mg",
                                "Amoxicillin 250mg", "Amoxicillin 500mg",
                                "Amoxicillin + Clavulanate 625mg", "Amoxicillin + Clavulanate 1000mg",
                                "Azithromycin 250mg", "Azithromycin 500mg",
                                "Ciprofloxacin 250mg", "Ciprofloxacin 500mg", "Ciprofloxacin 750mg",
                                "Doxycycline 100mg", "Metronidazole 200mg", "Metronidazole 400mg",
                                "Cefixime 200mg", "Cefixime 400mg",
                                "Cephalexin 250mg", "Cephalexin 500mg",
                                "Clarithromycin 250mg", "Clarithromycin 500mg",
                                "Levofloxacin 250mg", "Levofloxacin 500mg", "Levofloxacin 750mg",
                                "Amlodipine 2.5mg", "Amlodipine 5mg", "Amlodipine 10mg",
                                "Atenolol 25mg", "Atenolol 50mg", "Atenolol 100mg",
                                "Metoprolol 25mg", "Metoprolol 50mg", "Metoprolol 100mg",
                                "Losartan 25mg", "Losartan 50mg", "Losartan 100mg",
                                "Telmisartan 20mg", "Telmisartan 40mg", "Telmisartan 80mg",
                                "Enalapril 2.5mg", "Enalapril 5mg", "Enalapril 10mg",
                                "Ramipril 2.5mg", "Ramipril 5mg", "Ramipril 10mg",
                                "Lisinopril 5mg", "Lisinopril 10mg", "Lisinopril 20mg",
                                "Metformin 500mg", "Metformin 850mg", "Metformin 1000mg",
                                "Glimepiride 1mg", "Glimepiride 2mg", "Glimepiride 4mg",
                                "Sitagliptin 25mg", "Sitagliptin 50mg", "Sitagliptin 100mg",
                                "Atorvastatin 10mg", "Atorvastatin 20mg", "Atorvastatin 40mg",
                                "Rosuvastatin 5mg", "Rosuvastatin 10mg", "Rosuvastatin 20mg",
                                "Omeprazole 20mg", "Omeprazole 40mg",
                                "Pantoprazole 20mg", "Pantoprazole 40mg",
                                "Esomeprazole 20mg", "Esomeprazole 40mg",
                                "Cetirizine 5mg", "Cetirizine 10mg",
                                "Montelukast 10mg", "Levothyroxine 50mcg", "Levothyroxine 100mcg",
                                "Vitamin D3 60000 IU", "Calcium + Vitamin D3 500mg",
                                "Vitamin C 500mg", "Zinc 20mg"
                            ]
                            seen = set()
                            unique_meds = []
                            for m in ALL_MEDICINES_LIST:
                                if m.lower() not in seen:
                                    seen.add(m.lower())
                                    unique_meds.append(m)

                            options_list = unique_meds + ["➕ Other (Specify Custom Name)"]

                            selected_tablet = st.selectbox(
                                f"💊 Tablet / Medication Name #{idx+1}",
                                options=options_list,
                                index=None,
                                placeholder="Type to search tablets… e.g. Amoxicillin, Paracetamol",
                                key=f"doc_rx_select_{idx}"
                            )

                            if selected_tablet == "➕ Other (Specify Custom Name)":
                                med_name = st.text_input(
                                    f"Enter Custom Tablet Name #{idx+1}",
                                    placeholder="e.g. Specialized Drug 10mg",
                                    key=f"doc_rx_custom_{idx}"
                                ).strip()
                            elif selected_tablet:
                                med_name = selected_tablet
                            else:
                                med_name = ""

                            dosage = st.text_input(f"Dosage #{idx+1}", placeholder="e.g. 1 Tablet / 2 Capsules", key=f"dosage_{idx}")
                        with rx_col2:
                            frequency = st.selectbox(f"Frequency #{idx+1}", freq_options, key=f"freq_{idx}")
                            duration = st.text_input(f"Duration #{idx+1}", placeholder="e.g. 7 days, 30 days", key=f"dur_{idx}")
                        timing = st.selectbox(f"Timing #{idx+1}", timing_options, key=f"timing_{idx}")

                        tablets_data.append({
                            "med_name": med_name,
                            "dosage": dosage.strip(),
                            "frequency": frequency,
                            "duration": duration.strip(),
                            "timing": timing
                        })

                st.markdown("##### 🗒️ Doctor Instructions & Follow-up Notes")
                notes = st.text_area("Additional Doctor Instructions / Follow-up Notes", placeholder="e.g. Avoid alcohol. Drink plenty of water. Return in 2 weeks for review.", key="portal_notes")

                if st.button("💾 Save All Prescriptions & Clinical Notes", key="save_all_rx_btn", use_container_width=True):
                    valid_tablets = [t for t in tablets_data if t["med_name"]]
                    if not valid_tablets:
                        st.warning("⚠️ Please fill in at least one Medication / Tablet name before saving.")
                    else:
                        saved_count = 0
                        for t in valid_tablets:
                            rx_parts = []
                            rx_parts.append(f"MEDICATION: {t['med_name']}")
                            if t["dosage"]:    rx_parts.append(f"DOSAGE: {t['dosage']}")
                            if t["frequency"]: rx_parts.append(f"FREQUENCY: {t['frequency']}")
                            if t["timing"]:    rx_parts.append(f"TIMING: {t['timing']}")
                            if t["duration"]:  rx_parts.append(f"DURATION: {t['duration']}")
                            if notes:          rx_parts.append(f"INSTRUCTIONS: {notes}")

                            full_notes = " | ".join(rx_parts)

                            add_health_record(
                                db=db,
                                patient_id=selected_patient_id,
                                doctor_user_id=user["id"],
                                specialty_type=specialty_name,
                                diagnosis=diagnosis or "Clinical Assessment",
                                notes=full_notes
                            )
                            saved_count += 1

                        st.success(f"✅ Successfully issued **{saved_count} tablet prescription(s)** for **{selected_patient_name}**! Available in their medical report.")
                        st.session_state.doc_num_rx_items = 1
                        st.rerun()
            else:
                st.info("No patient profiles registered.")

        # ── Tab 3: My Prescriptions ────────────────────────────────────────────
        with tab3:
            st.write("### 📋 My Issued Prescriptions")
            st.caption("View, edit or delete prescriptions you have previously issued to patients.")

            # Load all HealthRecords this doctor created (doctor_id FK via Doctor table)
            doc_profile_rx = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()

            from sqlalchemy import or_
            if doc_profile_rx:
                # Match by doctor_id (Doctor table PK) OR null doctor_id records linked to this user's patients
                my_records = (
                    db.query(HealthRecord)
                    .filter(HealthRecord.doctor_id == doc_profile_rx.id)
                    .filter(HealthRecord.notes.isnot(None))
                    .filter(HealthRecord.notes.like("%MEDICATION:%"))
                    .order_by(HealthRecord.recorded_at.desc())
                    .all()
                )
            else:
                my_records = []

            # Fallback: also show prescription records with NULL doctor_id
            # (saved before a Doctor profile existed) — query all MEDICATION records
            null_doc_records = (
                db.query(HealthRecord)
                .filter(HealthRecord.doctor_id.is_(None))
                .filter(HealthRecord.notes.isnot(None))
                .filter(HealthRecord.notes.like("%MEDICATION:%"))
                .order_by(HealthRecord.recorded_at.desc())
                .all()
            )
            # Merge, deduplicate by id
            existing_ids = {r.id for r in my_records}
            for r in null_doc_records:
                if r.id not in existing_ids:
                    my_records.append(r)
            # Re-sort combined list newest first
            my_records.sort(key=lambda r: r.recorded_at or __import__('datetime').datetime.min, reverse=True)

            if not my_records:
                html("""
                <div class="medical-card" style="text-align:center; padding:40px;
                     border: 2px dashed rgba(255,255,255,0.1);">
                    <div style="font-size:3rem;">💊</div>
                    <div style="color:#9ca3af; margin-top:12px; font-size:0.95rem; font-weight:600;">No prescriptions issued yet.</div>
                    <div style="color:#64748b; font-size:0.82rem; margin-top:6px;">Issue prescriptions via the &ldquo;Prescribe &amp; Clinical Notes&rdquo; tab.</div>
                </div>""")
            else:
                # ── Search / filter bar ────────────────────────────────────────
                rx_search = st.text_input(
                    "Search prescriptions (patient name or medication)",
                    placeholder="e.g. Amoxicillin, John Doe…",
                    key="rx_hist_search"
                ).strip().lower()

                # Build a lookup of all patients for display
                all_patients = {p.id: p for p in db.query(User).filter(User.role == 'Patient').all()}

                # ── Helper: parse pipe-separated notes ──────────────────────────
                def _parse_rx_notes(notes_str):
                    parsed = {"medication": "", "dosage": "", "frequency": "",
                              "timing": "", "duration": "", "instructions": ""}
                    for part in (notes_str or "").split(" | "):
                        part = part.strip()
                        if ":" in part:
                            k, v = part.split(":", 1)
                            key = k.strip().lower()
                            val = v.strip()
                            if key == "medication":    parsed["medication"]    = val
                            elif key == "dosage":     parsed["dosage"]       = val
                            elif key == "frequency":  parsed["frequency"]    = val
                            elif key == "timing":     parsed["timing"]       = val
                            elif key == "duration":   parsed["duration"]     = val
                            elif key == "instructions": parsed["instructions"] = val
                    return parsed

                # ── Filter records ───────────────────────────────────────────
                filtered_records = []
                for rec in my_records:
                    patient = all_patients.get(rec.patient_id)
                    pname = (patient.full_name if patient else "Unknown").lower()
                    parsed = _parse_rx_notes(rec.notes)
                    if rx_search:
                        if rx_search not in pname and rx_search not in parsed["medication"].lower():
                            continue
                    filtered_records.append((rec, patient, parsed))

                st.markdown(f"**{len(filtered_records)} prescription(s) found**")
                st.markdown("---")

                # ── Edit / Delete state ─────────────────────────────────────────
                if "rx_edit_id" not in st.session_state:
                    st.session_state.rx_edit_id = None

                freq_opts_rx = [
                    "Once daily", "Twice daily", "Three times daily",
                    "Four times daily", "Every 6 hours", "Every 8 hours",
                    "Once weekly", "As needed (PRN)"
                ]
                timing_opts_rx = [
                    "After food", "Before food", "At bedtime",
                    "In the morning", "With food", "Empty stomach"
                ]

                for rec, patient, parsed in filtered_records:
                    pname = patient.full_name if patient else "Unknown Patient"
                    rec_date = rec.recorded_at.strftime("%d %b %Y, %I:%M %p") if rec.recorded_at else "N/A"
                    is_editing = (st.session_state.rx_edit_id == rec.id)
                    is_confirming_del = st.session_state.get(f"rx_confirm_del_{rec.id}", False)

                    # ── Card header (always visible) ───────────────────────────
                    html(f"""
                    <div style="background:rgba(30,58,138,0.25); border:1px solid rgba(59,130,246,0.3);
                                border-radius:14px; padding:16px 20px; margin-bottom:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                            <div>
                                <span style="font-size:1.05rem; font-weight:800; color:#ffffff;">
                                    💊 {parsed['medication'] or 'Prescription'}
                                </span>
                                <span style="margin-left:10px; font-size:0.8rem; color:#94a3b8;">
                                    &nbsp;👤 {pname} &nbsp;|&nbsp; 🗓 {rec_date}
                                </span>
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-top:12px;">
                            <div style="background:rgba(59,130,246,0.12); border-radius:8px; padding:8px 12px;">
                                <div style="font-size:0.68rem; color:#94a3b8; text-transform:uppercase; margin-bottom:3px;">Dosage</div>
                                <div style="font-weight:700; color:#e2e8f0;">{parsed['dosage'] or '—'}</div>
                            </div>
                            <div style="background:rgba(59,130,246,0.12); border-radius:8px; padding:8px 12px;">
                                <div style="font-size:0.68rem; color:#94a3b8; text-transform:uppercase; margin-bottom:3px;">Frequency</div>
                                <div style="font-weight:700; color:#e2e8f0;">{parsed['frequency'] or '—'}</div>
                            </div>
                            <div style="background:rgba(59,130,246,0.12); border-radius:8px; padding:8px 12px;">
                                <div style="font-size:0.68rem; color:#94a3b8; text-transform:uppercase; margin-bottom:3px;">Timing</div>
                                <div style="font-weight:700; color:#e2e8f0;">{parsed['timing'] or '—'}</div>
                            </div>
                            <div style="background:rgba(59,130,246,0.12); border-radius:8px; padding:8px 12px;">
                                <div style="font-size:0.68rem; color:#94a3b8; text-transform:uppercase; margin-bottom:3px;">Duration</div>
                                <div style="font-weight:700; color:#e2e8f0;">{parsed['duration'] or '—'}</div>
                            </div>
                        </div>
                        {f'<div style="margin-top:8px; font-size:0.82rem; color:#94a3b8;"><b>Diagnosis:</b> {rec.diagnosis}</div>' if rec.diagnosis else ''}
                        {f'<div style="margin-top:4px; font-size:0.82rem; color:#94a3b8;"><b>Instructions:</b> {parsed["instructions"]}</div>' if parsed["instructions"] else ''}
                    </div>
                    """)

                    # ── Action buttons (always rendered flat, not inside expander) ─
                    if not is_editing and not is_confirming_del:
                        act_col1, act_col2, _ = st.columns([1.2, 1.2, 4])
                        with act_col1:
                            if st.button(f"✏️ Edit", key=f"rx_edit_btn_{rec.id}"):
                                st.session_state.rx_edit_id = rec.id
                                st.rerun()
                        with act_col2:
                            if st.button(f"🗑️ Delete", key=f"rx_del_btn_{rec.id}"):
                                st.session_state[f"rx_confirm_del_{rec.id}"] = True
                                st.rerun()

                    # ── Delete confirmation ────────────────────────────────────
                    if is_confirming_del:
                        st.warning(f"⚠️ Delete prescription for **{pname}** ({parsed['medication'] or 'this record'})? This cannot be undone.")
                        yes_col, no_col, _ = st.columns([1, 1, 4])
                        with yes_col:
                            if st.button("✅ Yes, Delete", key=f"rx_del_yes_{rec.id}", type="primary"):
                                db.query(HealthRecord).filter(HealthRecord.id == rec.id).delete()
                                db.commit()
                                st.session_state.pop(f"rx_confirm_del_{rec.id}", None)
                                st.success("Prescription deleted successfully.")
                                st.rerun()
                        with no_col:
                            if st.button("❌ Cancel", key=f"rx_del_no_{rec.id}"):
                                st.session_state.pop(f"rx_confirm_del_{rec.id}", None)
                                st.rerun()

                    # ── Inline edit form ───────────────────────────────────────
                    if is_editing:
                        with st.container():
                            st.markdown("##### ✏️ Edit Prescription Details")
                            e_med = st.text_input("Medication Name", value=parsed["medication"], key=f"e_med_{rec.id}")
                            e_col1, e_col2 = st.columns(2)
                            with e_col1:
                                e_dosage   = st.text_input("Dosage", value=parsed["dosage"], key=f"e_dos_{rec.id}")
                                e_duration = st.text_input("Duration", value=parsed["duration"], key=f"e_dur_{rec.id}")
                            with e_col2:
                                freq_idx = freq_opts_rx.index(parsed["frequency"]) if parsed["frequency"] in freq_opts_rx else 0
                                e_freq = st.selectbox("Frequency", freq_opts_rx, index=freq_idx, key=f"e_frq_{rec.id}")
                                tim_idx = timing_opts_rx.index(parsed["timing"]) if parsed["timing"] in timing_opts_rx else 0
                                e_timing = st.selectbox("Timing", timing_opts_rx, index=tim_idx, key=f"e_tim_{rec.id}")
                            e_diag = st.text_input("Diagnosis", value=rec.diagnosis or "", key=f"e_diag_{rec.id}")
                            e_inst = st.text_area("Instructions", value=parsed["instructions"], key=f"e_inst_{rec.id}")

                            sv_col, cn_col, _ = st.columns([1.2, 1.2, 4])
                            with sv_col:
                                if st.button("💾 Save Changes", key=f"rx_save_{rec.id}", type="primary"):
                                    rx_parts = [f"MEDICATION: {e_med.strip()}"]
                                    if e_dosage.strip():   rx_parts.append(f"DOSAGE: {e_dosage.strip()}")
                                    if e_freq:             rx_parts.append(f"FREQUENCY: {e_freq}")
                                    if e_timing:           rx_parts.append(f"TIMING: {e_timing}")
                                    if e_duration.strip(): rx_parts.append(f"DURATION: {e_duration.strip()}")
                                    if e_inst.strip():     rx_parts.append(f"INSTRUCTIONS: {e_inst.strip()}")
                                    db.query(HealthRecord).filter(HealthRecord.id == rec.id).update({
                                        "notes":     " | ".join(rx_parts),
                                        "diagnosis": e_diag.strip() or rec.diagnosis
                                    })
                                    db.commit()
                                    st.session_state.rx_edit_id = None
                                    st.success("✅ Prescription updated successfully!")
                                    st.rerun()
                            with cn_col:
                                if st.button("Cancel", key=f"rx_cancel_{rec.id}"):
                                    st.session_state.rx_edit_id = None
                                    st.rerun()

                    st.markdown("---")

        # ── Tab 4: My Profile ──────────────────────────────────────────────────
        with tab4:
            st.write("### 👨‍⚕️ My Professional Profile")
            doctor_profile = db.query(Doctor).filter(Doctor.user_id == user["id"]).first()
            specialties = db.query(Specialty).all()

            if specialties:
                spec_map = {s.name: s.id for s in specialties}
                spec_list = list(spec_map.keys())

                default_spec_name = None
                if doctor_profile and doctor_profile.specialty:
                    default_spec_name = doctor_profile.specialty.name
                default_idx = spec_list.index(default_spec_name) if default_spec_name in spec_list else 0

                sel_spec_name = st.selectbox("Specialty Position", spec_list, index=default_idx)
                sel_spec_id = spec_map[sel_spec_name]

                exp_val = doctor_profile.experience_years if doctor_profile else 5
                fee_val = float(doctor_profile.consultation_fee) if (doctor_profile and doctor_profile.consultation_fee) else 75.0
                bio_val = doctor_profile.bio if doctor_profile else ""

                experience = st.number_input("Years of Experience", min_value=0, max_value=60, value=int(exp_val))
                fee = st.number_input("Consultation Fee (₹)", min_value=0.0, max_value=10000.0, value=float(fee_val), step=50.0)
                bio = st.text_area("Biography & Professional Background", value=bio_val, placeholder="Detail your clinical background, subspecialties, achievements...")

                if st.button("💾 Save Profile", use_container_width=True):
                    add_doctor_profile(db, user["id"], sel_spec_id, bio, int(experience), float(fee))
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
            else:
                st.warning("No specialties configured. Contact the system administrator.")

    finally:
        db.close()

