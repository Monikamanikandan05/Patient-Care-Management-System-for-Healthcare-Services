import streamlit as st
import streamlit.components.v1 as components
from core.database import SessionLocal
from models.models import User, HealthRecord, Doctor
from views.components import format_doctor_name


def _parse_rx_field(notes: str, field: str) -> str:
    """Extract a field like 'MEDICATION:' or 'PRESCRIBED:' from a structured notes string."""
    if not notes:
        return ""
    target = field.upper() + ":"
    aliases = [target]
    if field.upper() == "MEDICATION":
        aliases.extend(["PRESCRIBED:", "MEDICINE:", "TABLET:"])
    elif field.upper() == "INSTRUCTIONS":
        aliases.extend(["INSTRUCTIONS:", "FOLLOW-UP:"])
    elif field.upper() == "TIMING":
        aliases.append("TIMING:")

    for part in notes.split("|"):
        part = part.strip()
        for alias in aliases:
            if part.upper().startswith(alias):
                return part[len(alias):].strip()
    return ""


def _is_real_prescription(rec) -> bool:
    notes = (rec.notes or "").upper()
    return any(k in notes for k in ["MEDICATION:", "PRESCRIBED:", "DOSAGE:", "MEDICINE:", "TABLET:"])


def _render_prescription_card(rec, doc_name: str, index: int):
    notes = rec.notes or ""
    medication = _parse_rx_field(notes, "MEDICATION")
    dosage     = _parse_rx_field(notes, "DOSAGE")
    frequency  = _parse_rx_field(notes, "FREQUENCY")
    timing     = _parse_rx_field(notes, "TIMING")
    instructions = _parse_rx_field(notes, "INSTRUCTIONS")
    duration   = _parse_rx_field(notes, "DURATION")
    followup   = _parse_rx_field(notes, "FOLLOW-UP")

    date_str = rec.recorded_at.strftime('%d %b %Y, %I:%M %p') if rec.recorded_at else "N/A"
    dept = rec.specialty_type or "General"

    # Fix double Dr. prefix
    clean_doc = doc_name.strip()
    if clean_doc.lower().startswith("dr. "):
        clean_doc = clean_doc[4:]

    dept_colors = {
        "Cardiology":           "#ef4444",
        "Dentistry":            "#3b82f6",
        "Ophthalmology":        "#10b981",
        "Pulmonology (Chest)":  "#a855f7",
        "Orthopedics (Injury)": "#f59e0b",
        "General":              "#6b7280",
    }
    border_color = dept_colors.get(dept, "#6b7280")

    # Build medication pill
    med_html = f"""
      <div style="margin:8px 0;">
        <span style="background:#0d2b1f;color:#34d399;padding:5px 14px;
                     border-radius:20px;font-weight:700;font-size:0.9rem;
                     border:1px solid #065f46;">
          💊 {medication}
        </span>
      </div>""" if medication else ""

    # Build detail rows
    detail_rows = ""
    if dosage:
        detail_rows += f"<div style='margin:4px 0;font-size:0.85rem;color:#cbd5e1;'><b>Dosage:</b> {dosage}</div>"
    if frequency:
        detail_rows += f"<div style='margin:4px 0;font-size:0.85rem;color:#cbd5e1;'><b>Frequency:</b> {frequency}</div>"
    if timing:
        detail_rows += f"<div style='margin:4px 0;font-size:0.85rem;color:#cbd5e1;'><b>Timing:</b> {timing}</div>"
    if instructions and instructions != followup:
        detail_rows += f"<div style='margin:4px 0;font-size:0.85rem;color:#cbd5e1;'><b>Instructions:</b> {instructions}</div>"
    if duration:
        detail_rows += f"<div style='margin:4px 0;font-size:0.85rem;color:#cbd5e1;'><b>Duration:</b> {duration}</div>"
    if followup:
        detail_rows += f"<div style='margin:8px 0 0;font-size:0.83rem;color:#94a3b8;font-style:italic;'><b>Follow-up:</b> {followup}</div>"

    diag_html = ""
    if rec.diagnosis:
        safe_diag = str(rec.diagnosis)
        diag_html = f"<div style='font-size:0.8rem;color:#6b7280;margin-top:8px;'>🩺 {safe_diag}</div>"

    card_html = f"""
    <div style="font-family:Arial,sans-serif;
                background:linear-gradient(135deg,#111827,#1a2332);
                border-radius:14px;padding:18px 20px;margin-bottom:12px;
                border-left:5px solid {border_color};
                box-shadow:0 4px 18px rgba(0,0,0,0.35);">

      <!-- Header Row -->
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
        <div style="flex:1;">
          <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.09em;color:{border_color};margin-bottom:6px;">
            {dept} &nbsp;·&nbsp; Prescription #{index}
          </div>
          {med_html}
          {detail_rows}
          {diag_html}
        </div>
        <div style="text-align:right;min-width:120px;flex-shrink:0;">
          <div style="font-size:0.73rem;color:#4b5563;margin-bottom:4px;">{date_str}</div>
          <div style="font-size:0.8rem;color:#94a3b8;margin-top:4px;">
            👨‍⚕️ {format_doctor_name(clean_doc)}
          </div>
        </div>
      </div>
    </div>
    """
    return card_html


def render_prescriptions_view():
    st.write("### 💊 Prescription & Medication Logs")
    user = st.session_state.user
    db = SessionLocal()
    try:
        if user["role"] == "Patient":
            records = (
                db.query(HealthRecord)
                .filter(HealthRecord.patient_id == user["id"])
                .order_by(HealthRecord.recorded_at.desc())
                .all()
            )

            # Only show structured prescriptions with MEDICATION field
            rx_records = [r for r in records if _is_real_prescription(r)]

            if rx_records:
                st.markdown(f"**{len(rx_records)} prescription(s) on record.**")
                st.markdown("---")

                # Build structured Table view
                table_rows = []
                for rec in rx_records:
                    doc_profile = db.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
                    doc_user = db.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
                    doc_name = format_doctor_name(doc_user.full_name) if doc_user else "Dr. Medical Specialist"
                    doc_spec = doc_profile.specialty.name if (doc_profile and doc_profile.specialty) else (rec.specialty_type or "General Medicine")
                    doc_with_spec = f"{doc_name} ({doc_spec})"

                    notes = rec.notes or ""
                    medication = _parse_rx_field(notes, "MEDICATION") or "N/A"
                    dosage     = _parse_rx_field(notes, "DOSAGE") or "N/A"
                    frequency  = _parse_rx_field(notes, "FREQUENCY") or "N/A"
                    timing     = _parse_rx_field(notes, "TIMING") or "N/A"
                    instructions = _parse_rx_field(notes, "INSTRUCTIONS") or "As directed by physician"
                    duration   = _parse_rx_field(notes, "DURATION") or "N/A"
                    date_str   = rec.recorded_at.strftime('%d %b %Y') if rec.recorded_at else "N/A"

                    table_rows.append({
                        "Medication / Tablet": medication,
                        "Dosage": dosage,
                        "Frequency": frequency,
                        "Timing": timing,
                        "Doctor's Instructions": instructions,
                        "Duration": duration,
                        "Prescribing Doctor": doc_with_spec,
                        "Date Issued": date_str
                    })

                import pandas as pd
                df_rx = pd.DataFrame(table_rows)
                
                # Render clean Streamlit Table
                st.dataframe(
                    df_rx,
                    column_config={
                        "Medication / Tablet": st.column_config.TextColumn("💊 Tablet / Medication", width="medium"),
                        "Dosage": st.column_config.TextColumn("🧪 Dosage", width="small"),
                        "Frequency": st.column_config.TextColumn("🔄 Frequency", width="small"),
                        "Timing": st.column_config.TextColumn("⏰ Timing", width="small"),
                        "Doctor's Instructions": st.column_config.TextColumn("📋 Doctor's Instructions", width="medium"),
                        "Duration": st.column_config.TextColumn("📅 Duration", width="small"),
                        "Prescribing Doctor": st.column_config.TextColumn("👨‍⚕️ Prescribed By", width="medium"),
                        "Date Issued": st.column_config.TextColumn("🗓️ Date", width="small"),
                    },
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📑 Detailed Prescription Cards")

                all_cards_html = """
                <style>
                  * { box-sizing: border-box; }
                  body { margin: 0; padding: 0; background: transparent; }
                </style>
                """
                for idx, rec in enumerate(rx_records, start=1):
                    doc_profile = db.query(Doctor).filter(Doctor.id == rec.doctor_id).first()
                    doc_user    = db.query(User).filter(User.id == doc_profile.user_id).first() if doc_profile else None
                    if not doc_user:
                        doc_user = db.query(User).filter(User.role == 'Doctor').first()
                    doc_name    = doc_user.full_name if doc_user else "Medical Specialist"
                    all_cards_html += _render_prescription_card(rec, doc_name, idx)

                card_height = 160 + len(rx_records) * 145
                components.html(all_cards_html, height=card_height, scrolling=False)

            else:
                components.html("""
                <div style="font-family:Arial,sans-serif;background:#1f2937;border-radius:16px;
                            padding:40px;text-align:center;border:2px dashed rgba(255,255,255,0.08);">
                  <div style="font-size:3rem;margin-bottom:12px;">💊</div>
                  <div style="color:#9ca3af;font-size:1rem;font-weight:600;">No prescriptions found.</div>
                  <div style="color:#4b5563;font-size:0.85rem;margin-top:6px;">
                    Prescriptions issued by your doctor will appear here.
                  </div>
                </div>
                """, height=180)

        else:  # Admin or Doctor
            st.markdown("##### ✍️ Issue Multiple Tablet Prescriptions to Patient")
            patients = db.query(User).filter(User.role == 'Patient').all()
            if patients:
                patient_map = {p.full_name: p.id for p in patients}
                selected_patient = st.selectbox("Select Patient", list(patient_map.keys()), key="presc_patient")
                
                doc_prof = db.query(Doctor).filter(Doctor.user_id == user["id"]).first() if user["role"] == "Doctor" else None
                doc_id = doc_prof.id if doc_prof else None
                spec_name = doc_prof.specialty.name if (doc_prof and doc_prof.specialty) else "General Medicine"

                # Load all pharmacy medicines for autocomplete
                from services.pharmacy_service import get_all_medicines as _get_meds
                pharmacy_medicines = _get_meds(db)
                med_names = [m.name for m in pharmacy_medicines]

                # Multi-tablet support
                if "pv_num_rx_items" not in st.session_state:
                    st.session_state.pv_num_rx_items = 1

                btn_col1, btn_col2, _ = st.columns([1.5, 1.5, 3])
                with btn_col1:
                    if st.button("➕ Add Another Tablet", key="pv_add_rx_btn", use_container_width=True):
                        st.session_state.pv_num_rx_items += 1
                        st.rerun()
                with btn_col2:
                    if st.session_state.pv_num_rx_items > 1:
                        if st.button("❌ Remove Last Tablet", key="pv_rem_rx_btn", use_container_width=True):
                            st.session_state.pv_num_rx_items -= 1
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

                for idx in range(st.session_state.pv_num_rx_items):
                    with st.expander(f"💊 Tablet #{idx + 1} Details", expanded=True):
                        rx_col1, rx_col2 = st.columns(2)
                        with rx_col1:
                            # ── Smart medicine search/autocomplete ──────────────────────
                            med_search_key = f"pv_med_search_{idx}"
                            med_typed = st.text_input(
                                f"💊 Medication / Tablet Name #{idx+1}",
                                placeholder="Type tablet name… e.g. Amoxicillin, Paracetamol, Metformin",
                                key=med_search_key
                            )
                            medication = med_typed.strip()

                            # Show live matching suggestions from pharmacy
                            if med_typed.strip():
                                query = med_typed.strip().lower()
                                matched = [n for n in med_names if query in n.lower()]
                                if matched:
                                    st.markdown(
                                        "<div style='font-size:.8rem;color:#10b981;font-weight:700;margin:4px 0 2px 0;'>"
                                        "📋 <b>Matching pharmacy tablets (click to select):</b></div>",
                                        unsafe_allow_html=True
                                    )
                                    sug_cols = st.columns(min(len(matched), 3))
                                    for m_i, match_val in enumerate(matched[:6]):
                                        with sug_cols[m_i % min(len(matched), 3)]:
                                            if st.button(f"💊 {match_val}", key=f"pv_sug_btn_{idx}_{m_i}", use_container_width=True):
                                                st.session_state[med_search_key] = match_val
                                                st.rerun()

                            dosage = st.text_input(f"Dosage #{idx+1}", placeholder="e.g. 1 capsule", key=f"pv_dosage_{idx}")
                        with rx_col2:
                            frequency = st.selectbox(f"Frequency #{idx+1}", freq_options, key=f"pv_freq_{idx}")
                            duration = st.text_input(f"Duration #{idx+1}", placeholder="e.g. 7 days", key=f"pv_dur_{idx}")
                        timing = st.selectbox(f"Timing #{idx+1}", timing_options, key=f"pv_timing_{idx}")

                        tablets_data.append({
                            "medication": medication,
                            "dosage": dosage.strip(),
                            "frequency": frequency,
                            "duration": duration.strip(),
                            "timing": timing
                        })

                followup = st.text_area("Doctor Instructions & Follow-up Notes", placeholder="e.g. Avoid alcohol. Return in 2 weeks for review.", key="pv_notes")

                if st.button("✍️ Save & Issue All Prescriptions", key="pv_save_all_btn", use_container_width=True):
                    valid_tablets = [t for t in tablets_data if t["medication"]]
                    if not valid_tablets:
                        st.warning("⚠️ Please enter at least one Medication / Tablet name.")
                    else:
                        saved_count = 0
                        for t in valid_tablets:
                            parts = []
                            parts.append(f"MEDICATION: {t['medication']}")
                            if t["dosage"]:    parts.append(f"DOSAGE: {t['dosage']}")
                            if t["frequency"]: parts.append(f"FREQUENCY: {t['frequency']}")
                            if t["timing"]:    parts.append(f"TIMING: {t['timing']}")
                            if t["duration"]:  parts.append(f"DURATION: {t['duration']}")
                            if followup:       parts.append(f"INSTRUCTIONS: {followup}")

                            notes_content = " | ".join(parts)
                            rec = HealthRecord(
                                patient_id=patient_map[selected_patient],
                                doctor_id=doc_id,
                                specialty_type=spec_name,
                                notes=notes_content,
                                diagnosis="Prescription issued"
                            )
                            db.add(rec)
                            saved_count += 1
                        db.commit()
                        st.success(f"✅ Issued **{saved_count} prescription(s)** for **{selected_patient}**!")
                        st.session_state.pv_num_rx_items = 1
                        st.rerun()
            else:
                st.info("No patients registered in the system.")
    finally:
        db.close()
