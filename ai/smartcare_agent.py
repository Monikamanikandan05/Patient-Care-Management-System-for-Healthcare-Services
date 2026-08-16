import logging
import datetime
import re
import json as _json
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.errors import GraphRecursionError

from ai.llm import get_llm, OfflineMockLLM
from ai.vectorstore import get_vectorstore
from core.database import session_scope
from models.models import User, Doctor, Specialty, DoctorSlot, Appointment, HealthRecord
from services import doctor_service, appointment_service, health_service, analytics_service

log = logging.getLogger("smartcare.agent")

_RECURSION_LIMIT = 6

ROLE_PATIENT = "Patient"
ROLE_DOCTOR  = "Doctor"
ROLE_ADMIN   = "Admin"

# ── Multilingual keyword sets ─────────────────────────────────────────────────
# Every set includes English + Tamil + Malayalam + Hindi + Telugu keywords

_KW_BOOKING = [
    # English
    "book appointment","create an appointment","create appointment",
    "schedule appointment","make an appointment","arrange appointment",
    "need an appointment","i want to book","book a doctor",
    "book now","set an appointment","fix an appointment",
    "book consultation","book visit",
    # Tamil (தமிழ்)
    "சந்திப்பு பதிவு","அப்பாயின்ட்மென்ட்","டாக்டர் பதிவு","சந்திப்பு வேண்டும்",
    # Malayalam (മലയാളം)
    "അപ്പോയിന്റ്മെന്റ്","ഡോക്ടറെ കാണണം","ബുക്ക് ചെയ്യണം","കൂടിക്കാഴ്ച",
    # Hindi (हिन्दी)
    "अपॉइंटमेंट बुक","डॉक्टर से मिलना","बुकिंग करें","मुलाकात बुक",
    # Telugu (తెలుగు)
    "అపాయింట్మెంట్ బుక్","డాక్టర్ అపాయింట్మెంట్","బుక్ చేయండి",
]

_KW_REPORT = [
    # English
    "download report","download health report","download my report",
    "generate report","generate health report","health report",
    "medical report","download medical report","complete report",
    "my report","get my report","download pdf","export report",
    "ai report","ai health report","create report",
    # Tamil
    "அறிக்கை","ஆரோக்கிய அறிக்கை","என் அறிக்கை","மருத்துவ அறிக்கை",
    # Malayalam
    "റിപ്പോർട്ട്","ആരോഗ്യ റിപ്പോർട്ട്","എന്റെ റിപ്പോർട്ട്",
    # Hindi
    "रिपोर्ट","स्वास्थ्य रिपोर्ट","मेरी रिपोर्ट","डाउनलोड रिपोर्ट",
    # Telugu
    "నివేదిక","ఆరోగ్య నివేదిక","నా నివేదిక",
]

_KW_PHARMACY_ORDER = [
    # English
    "pharmacy order","my pharmacy order","my orders","order history",
    "pharmacy history","show my orders",
    # Tamil
    "என் ஆர்டர்","மருந்தகம் ஆர்டர்",
    # Malayalam
    "എന്റെ ഓർഡർ","ഫാർമസി ഓർഡർ",
    # Hindi
    "मेरा ऑर्डर","दवाई ऑर्डर",
    # Telugu
    "నా ఆర్డర్","ఫార్మసీ ఆర్డర్",
]

_KW_PHARMACY = [
    # English
    "pharmacy","medicine","tablets","in stock","stock of","price of",
    "available medicine","buy medicine","order medicine","drug list",
    "pharmacy inventory","paracetamol","amoxicillin","amlodipine","insulin",
    "metformin","atorvastatin","cough syrup","eye drops","hydrocortisone",
    # Tamil
    "மருந்து","மாத்திரை","மருந்தகம்","மருந்து பட்டியல்",
    # Malayalam
    "മരുന്ന്","ഫാർമസി","ഗുളിക","മരുന്ന് ലഭ്യത",
    # Hindi
    "दवाई","दवा","फार्मेसी","गोलियां","दवाइयां",
    # Telugu
    "మందులు","ఫార్మసీ","మాత్రలు","మందు జాబితా",
]

_KW_HEALTH = [
    # English
    "health condition","my health","how is my health",
    # Tamil
    "உடல்நலம்","என் ஆரோக்கியம்","உடல் நிலை",
    # Malayalam
    "ആരോഗ്യം","എന്റെ ആരോഗ്യം","ആരോഗ്യ നില",
    # Hindi
    "स्वास्थ्य","मेरी सेहत","मेरा स्वास्थ्य",
    # Telugu
    "ఆరోగ్యం","నా ఆరోగ్యం","నా ఆరోగ్య స్థితి",
]

_KW_PATIENTS = [
    # English
    "patient list","list patients","show patients","all patients",
    "registered patients","who are the patients",
    # Tamil
    "நோயாளி பட்டியல்","நோயாளிகள்",
    # Malayalam
    "രോഗി ലിസ്റ്റ്","രോഗികൾ",
    # Hindi
    "मरीज सूची","मरीज","रोगी सूची",
    # Telugu
    "రోగి జాబితా","రోగులు",
]

_KW_DOCTORS = [
    # English
    "doctor list","doctors list","list doctors","show doctors",
    "all doctors","find doctors","specialist list","doctor credentials",
    "doctor info","doctor details",
    # Tamil
    "மருத்துவர் பட்டியல்","டாக்டர் பட்டியல்","மருத்துவர்",
    # Malayalam
    "ഡോക്ടർ ലിസ്റ്റ്","ഡോക്ടർ","ഡോക്ടർ വിവരങ്ങൾ",
    # Hindi
    "डॉक्टर सूची","डॉक्टर","चिकित्सक सूची",
    # Telugu
    "డాక్టర్ జాబితా","డాక్టర్","వైద్యుడు జాబితా",
]

_KW_APPOINTMENTS = [
    # English
    "upcoming appointments","appointment list","appointments list",
    "show appointments","all appointments","my appointments",
    "schedule list","do i have","any appointment","booked appointment",
    "scheduled appointment","my schedule","show my",
    # Tamil
    "சந்திப்பு","எனது சந்திப்பு","எனக்கு சந்திப்பு",
    # Malayalam
    "അപ്പോയിന്റ്മെന്റ്","എന്റെ അപ്പോയിന്റ്മെന്റ്","ഷെഡ്യൂൾ",
    # Hindi
    "मेरी अपॉइंटमेंट","मेरा शेड्यूल","आगामी अपॉइंटमेंट",
    # Telugu
    "నా అపాయింట్మెంట్","షెడ్యూల్","నా షెడ్యూల్",
]

_KW_SUMMARY = [
    # English
    "clinic overview","clinic summary","total appointments","clinic stats",
    "system summary","hospital metrics",
    # Tamil
    "கிளினிக் சுருக்கம்","மருத்துவமனை புள்ளிவிவரம்",
    # Malayalam
    "ക്ലിനിക് സംഗ്രഹം","ആശുപത്രി സ്ഥിതി",
    # Hindi
    "क्लिनिक सारांश","अस्पताल सारांश",
    # Telugu
    "క్లినిక్ సారాంశం","ఆసుపత్రి గణాంకాలు",
]

def _parse_date(d_str: str) -> datetime.date:
    if not d_str or str(d_str).strip().lower() in ("today", ""):
        return datetime.date.today()
    s = str(d_str).strip().lower()
    if s == "tomorrow":
        return datetime.date.today() + datetime.timedelta(days=1)
    weekdays = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    if s in weekdays:
        today = datetime.date.today()
        target = weekdays.index(s)
        days_ahead = target - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + datetime.timedelta(days=days_ahead)
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return datetime.date.today()

def _make_callback(user: dict):
    class ToolTracer(BaseCallbackHandler):
        def on_tool_start(self, serialized, input_str, **kwargs):
            name = (serialized or {}).get("name", "?")
            log.info("tool_start user=%s role=%s tool=%s args=%s",
                     user.get("id"), user.get("role"), name, str(input_str)[:200])
        def on_tool_end(self, output, **kwargs):
            log.info("tool_end user=%s output=%s", user.get("id"), str(output)[:200])
        def on_tool_error(self, error, **kwargs):
            log.error("tool_error user=%s error=%s", user.get("id"), str(error))
    return ToolTracer()

# ── Database Fetch Functions ──────────────────────────────────────────────────

def fetch_patient_list_db() -> str:
    with session_scope() as s:
        patients = s.query(User).filter(User.role == 'Patient').all()
        if not patients:
            return "No patient profiles found."
        lines = [f"### 👥 Registered Patients ({len(patients)} total)\n"]
        lines.append("| ID | Name | Email | Phone | Joined |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for p in patients:
            created = p.created_at.strftime("%Y-%m-%d") if p.created_at else "N/A"
            lines.append(f"| #{p.id} | **{p.full_name}** | `{p.email}` | {p.phone or 'N/A'} | {created} |")
        return "\n".join(lines)

def fetch_doctor_list_db(specialty_filter: str = "") -> str:
    with session_scope() as s:
        query = s.query(Doctor).join(User, Doctor.user_id == User.id)
        if specialty_filter:
            spec = s.query(Specialty).filter(Specialty.name.ilike(f"%{specialty_filter}%")).first()
            if spec:
                query = query.filter(Doctor.specialty_id == spec.id)
        docs = query.all()
        if not docs:
            return f"No doctors found." if not specialty_filter else f"No doctors found for '{specialty_filter}'."
        lines = [f"### 👨‍⚕️ Doctors ({len(docs)} active)\n"]
        lines.append("| Name | Specialty | Experience | Fee | Email |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for d in docs:
            name = d.user.full_name if d.user else "N/A"
            spec = d.specialty.name if d.specialty else "General"
            email = d.user.email if d.user else "N/A"
            lines.append(f"| **Dr. {name}** | `{spec}` | {d.experience_years or 0} yrs | ₹{d.consultation_fee or 0:.0f} | `{email}` |")
        return "\n".join(lines)

def fetch_doctor_credentials_db() -> str:
    """Full doctor profile including bio and credentials."""
    with session_scope() as s:
        docs = s.query(Doctor).join(User, Doctor.user_id == User.id).all()
        if not docs:
            return "No doctor records found."
        lines = [f"### 🩺 Doctor Credentials & Profiles ({len(docs)} doctors)\n"]
        for d in docs:
            name = d.user.full_name if d.user else "N/A"
            email = d.user.email if d.user else "N/A"
            phone = d.user.phone if d.user else "N/A"
            spec = d.specialty.name if d.specialty else "General"
            lines.append(f"#### Dr. {name}")
            lines.append(f"- **Specialty:** {spec}")
            lines.append(f"- **Experience:** {d.experience_years or 0} years")
            lines.append(f"- **Consultation Fee:** ₹{d.consultation_fee or 0:.0f}")
            lines.append(f"- **Email:** `{email}`")
            lines.append(f"- **Phone:** {phone or 'N/A'}")
            if d.bio:
                lines.append(f"- **Bio:** {d.bio}")
            lines.append("")
        return "\n".join(lines)

def fetch_appointments_db(user: dict) -> str:
    role = user.get("role", ROLE_PATIENT)
    u_id = user.get("id")
    with session_scope() as s:
        if role == ROLE_DOCTOR:
            doc = s.query(Doctor).filter(Doctor.user_id == u_id).first()
            if not doc:
                return "Doctor profile not configured."
            appts = s.query(Appointment).filter(Appointment.doctor_id == doc.id).order_by(Appointment.scheduled_date.desc(), Appointment.start_time).all()
        elif role == ROLE_PATIENT:
            appts = s.query(Appointment).filter(Appointment.patient_id == u_id).order_by(Appointment.scheduled_date.desc(), Appointment.start_time).all()
        else:
            appts = s.query(Appointment).order_by(Appointment.scheduled_date.desc(), Appointment.start_time).all()

        if not appts:
            return "No appointments found."
        lines = [f"### 📅 Appointments ({len(appts)} total)\n"]
        lines.append("| # | Date & Time | Patient | Doctor / Specialty | Status | Reason |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for a in appts:
            p_name = a.patient.full_name if a.patient else f"Patient #{a.patient_id}"
            raw_name = a.doctor.user.full_name if (a.doctor and a.doctor.user) else "N/A"
            d_name = raw_name if raw_name.lower().startswith("dr.") else f"Dr. {raw_name}"
            spec = a.doctor.specialty.name if (a.doctor and a.doctor.specialty) else "General"
            dt = f"{a.scheduled_date.strftime('%Y-%m-%d')} {a.start_time.strftime('%H:%M')}"
            lines.append(f"| #{a.id} | {dt} | **{p_name}** | {d_name} ({spec}) | `{a.status}` | {a.reason or 'Checkup'} |")
        return "\n".join(lines)

def fetch_clinic_summary_db() -> str:
    with session_scope() as s:
        total_patients  = s.query(User).filter(User.role == 'Patient').count()
        total_doctors   = s.query(Doctor).count()
        total_users     = s.query(User).count()
        total_appts     = s.query(Appointment).count()
        scheduled_appts = s.query(Appointment).filter(Appointment.status == 'Scheduled').count()
        completed_appts = s.query(Appointment).filter(Appointment.status == 'Completed').count()
        cancelled_appts = s.query(Appointment).filter(Appointment.status == 'Cancelled').count()
        return (
            "### 🏥 Smart Care IPCMS — Live Clinic Summary\n\n"
            f"• **Registered Patients:** {total_patients}\n"
            f"• **Active Doctors:** {total_doctors}\n"
            f"• **Total Users:** {total_users}\n"
            f"• **Total Appointments:** {total_appts}\n"
            f"  - ⏳ Scheduled: {scheduled_appts}\n"
            f"  - ✅ Completed: {completed_appts}\n"
            f"  - ❌ Cancelled: {cancelled_appts}\n"
        )

def fetch_top_doctors_by_fee_db(limit=3) -> str:
    with session_scope() as s:
        docs = s.query(Doctor).join(User).order_by(Doctor.consultation_fee.desc()).limit(limit).all()
        if not docs:
            return "No doctor records found."
        lines = [f"### 🏆 Top {limit} Doctors by Fee\n"]
        lines.append("| Rank | Name | Specialty | Fee |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for i, d in enumerate(docs, 1):
            name = d.user.full_name if d.user else "N/A"
            spec = d.specialty.name if d.specialty else "General"
            lines.append(f"| #{i} | **Dr. {name}** | `{spec}` | ₹{d.consultation_fee or 0:.0f} |")
        return "\n".join(lines)

def fetch_my_health_condition_db(user: dict) -> str:
    if user.get("role") != ROLE_PATIENT:
        return "You must be logged in as a patient to view health records."
    with session_scope() as s:
        records = s.query(HealthRecord).filter(
            HealthRecord.patient_id == user.get("id")
        ).order_by(HealthRecord.recorded_at.desc()).all()

        if not records:
            return "No health records found in your profile."

        record = records[0]
        lines = [f"### 🩺 Your Latest Health Record ({len(records)} total records)\n"]
        lines.append(f"**Recorded:** {record.recorded_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Specialty:** {record.specialty_type or 'General'}")
        lines.append(f"**Diagnosis:** {record.diagnosis or 'N/A'}")
        if record.notes:
            lines.append(f"**Notes:** {record.notes}")

        # General metrics
        gen = []
        if record.weight:       gen.append(f"Weight: {record.weight} kg")
        if record.height:       gen.append(f"Height: {record.height} cm")
        if record.bmi:          gen.append(f"BMI: {record.bmi}")
        if record.blood_sugar:  gen.append(f"Blood Sugar: {record.blood_sugar} mg/dL")
        if record.cholesterol:  gen.append(f"Cholesterol: {record.cholesterol} mg/dL")
        if gen:
            lines.append("\n**General Metrics:**")
            for g in gen: lines.append(f"- {g}")

        # Cardiology
        card = []
        if record.heart_rate:        card.append(f"Heart Rate: {record.heart_rate} bpm")
        if record.blood_pressure:    card.append(f"Blood Pressure: {record.blood_pressure}")
        if record.troponin:          card.append(f"Troponin: {record.troponin}")
        if record.ejection_fraction: card.append(f"Ejection Fraction: {record.ejection_fraction}%")
        if record.cardiac_output:    card.append(f"Cardiac Output: {record.cardiac_output} L/min")
        if record.oxygen_saturation: card.append(f"SpO2: {record.oxygen_saturation}%")
        if record.ecg_note:          card.append(f"ECG: {record.ecg_note}")
        if card:
            lines.append("\n**Cardiology Vitals:**")
            for c in card: lines.append(f"- {c}")

        # Dentistry
        dent = []
        if record.teeth_condition:  dent.append(f"Teeth: {record.teeth_condition}")
        if record.gum_health:       dent.append(f"Gums: {record.gum_health}")
        if record.procedure_done:   dent.append(f"Procedure: {record.procedure_done}")
        if record.xray_finding:     dent.append(f"X-Ray: {record.xray_finding}")
        if dent:
            lines.append("\n**Dentistry:**")
            for d in dent: lines.append(f"- {d}")

        # Ophthalmology
        eye = []
        if record.right_eye_vision: eye.append(f"Right Eye: {record.right_eye_vision}")
        if record.left_eye_vision:  eye.append(f"Left Eye: {record.left_eye_vision}")
        if record.eye_pressure_iop: eye.append(f"Eye Pressure: {record.eye_pressure_iop}")
        if record.eye_condition:    eye.append(f"Condition: {record.eye_condition}")
        if eye:
            lines.append("\n**Ophthalmology:**")
            for e in eye: lines.append(f"- {e}")

        # Pulmonology
        lung = []
        if record.respiratory_rate:  lung.append(f"Respiratory Rate: {record.respiratory_rate} /min")
        if record.fev1:              lung.append(f"FEV1: {record.fev1}")
        if record.chest_xray_finding: lung.append(f"Chest X-Ray: {record.chest_xray_finding}")
        if record.lung_condition:    lung.append(f"Condition: {record.lung_condition}")
        if lung:
            lines.append("\n**Pulmonology:**")
            for l in lung: lines.append(f"- {l}")

        # Orthopedics
        orth = []
        if record.injury_location:  orth.append(f"Injury: {record.injury_location}")
        if record.fracture_type:    orth.append(f"Fracture: {record.fracture_type}")
        if record.mri_xray_finding: orth.append(f"MRI/X-Ray: {record.mri_xray_finding}")
        if record.mobility_score is not None: orth.append(f"Mobility Score: {record.mobility_score}/10")
        if record.treatment_plan:   orth.append(f"Treatment: {record.treatment_plan}")
        if orth:
            lines.append("\n**Orthopedics:**")
            for o in orth: lines.append(f"- {o}")

        if record.surgeries:
            lines.append(f"\n**Surgeries:** {record.surgeries}")
        if record.vaccinations:
            lines.append(f"**Vaccinations:** {record.vaccinations}")

        return "\n".join(lines)

def fetch_appointment_count_db(user: dict, status: str) -> str:
    with session_scope() as s:
        q = s.query(Appointment)
        role = user.get("role")
        u_id = user.get("id")
        if role == ROLE_DOCTOR:
            doc = s.query(Doctor).filter(Doctor.user_id == u_id).first()
            if doc: q = q.filter(Appointment.doctor_id == doc.id)
        elif role == ROLE_PATIENT:
            q = q.filter(Appointment.patient_id == u_id)
        count = q.filter(Appointment.status == status).count()
        return f"You have **{count}** {status.lower()} appointment(s)."

def fetch_pharmacy_medicines_db(keyword: str = "") -> str:
    with session_scope() as s:
        from models.models import PharmacyMedicine
        query = s.query(PharmacyMedicine).filter(PharmacyMedicine.is_active == True)
        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                PharmacyMedicine.name.ilike(kw) |
                PharmacyMedicine.generic_name.ilike(kw) |
                PharmacyMedicine.category.ilike(kw)
            )
        meds = query.order_by(PharmacyMedicine.category, PharmacyMedicine.name).all()
        if not meds:
            return f"No medicines found matching '{keyword}'." if keyword else "No pharmacy medicines found."
        lines = [f"### 💊 Pharmacy Medicines ({len(meds)} items)\n"]
        lines.append("| Name | Category | Generic | Price | Stock | Rx |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for m in meds:
            rx    = "`Rx Required`" if m.requires_prescription else "`OTC`"
            stock = "❌ Out of stock" if m.stock_qty == 0 else (f"⚠️ Low ({m.stock_qty})" if m.stock_qty <= 20 else f"✅ {m.stock_qty}")
            lines.append(f"| **{m.name}** | `{m.category or 'General'}` | {m.generic_name or 'N/A'} | ₹{float(m.price):.2f} | {stock} | {rx} |")
        lines.append("\n💡 Go to **🛒 Pharmacy** tab to place orders.")
        return "\n".join(lines)

def fetch_top_medicines_by_price_db(limit: int = 5, ascending: bool = False) -> str:
    """Fetch the highest or lowest cost medicines / tablets from the pharmacy database."""
    with session_scope() as s:
        from models.models import PharmacyMedicine
        query = s.query(PharmacyMedicine).filter(PharmacyMedicine.is_active == True)
        if ascending:
            meds = query.order_by(PharmacyMedicine.price.asc()).limit(limit).all()
            title = f"### 💊 Lowest Cost / Most Affordable Medicines (Top {len(meds)})\n"
        else:
            meds = query.order_by(PharmacyMedicine.price.desc()).limit(limit).all()
            title = f"### 💊 Highest Cost / Premium Medicines (Top {len(meds)})\n"

        if not meds:
            return "No pharmacy medicines found in the system."

        lines = [title]
        lines.append("| Rank | Medicine Name | Generic Name | Category | Unit Price | Stock Status | Rx |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for i, m in enumerate(meds, 1):
            rx = "`Rx Required`" if m.requires_prescription else "`OTC`"
            stock = "❌ Out of stock" if m.stock_qty == 0 else (f"⚠️ Low ({m.stock_qty})" if m.stock_qty <= 20 else f"✅ In Stock ({m.stock_qty})")
            lines.append(f"| **#{i}** | **{m.name}** | {m.generic_name or 'N/A'} | `{m.category or 'General'}` | **₹{float(m.price):.2f}** / {m.unit or 'Tablet'} | {stock} | {rx} |")
        lines.append("\n💡 Go to **🛒 Pharmacy** tab to purchase or view complete medicine details.")
        return "\n".join(lines)

def fetch_pharmacy_orders_db(user: dict) -> str:
    with session_scope() as s:
        from models.models import PharmacyOrder
        role = user.get("role", ROLE_PATIENT)
        u_id = user.get("id")
        if role == ROLE_PATIENT:
            orders = s.query(PharmacyOrder).filter(PharmacyOrder.patient_id == u_id).order_by(PharmacyOrder.created_at.desc()).all()
        else:
            orders = s.query(PharmacyOrder).order_by(PharmacyOrder.created_at.desc()).all()
        if not orders:
            return "No pharmacy orders found."
        lines = [f"### 📦 Pharmacy Orders ({len(orders)} total)\n"]
        lines.append("| Order ID | Date | Status | Total | Items |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for o in orders:
            dt = o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else "N/A"
            items = len(o.items) if o.items else 0
            lines.append(f"| #{o.id} | {dt} | `{o.status}` | **₹{float(o.total_amount):.2f}** | {items} item(s) |")
        return "\n".join(lines)

def fetch_health_report_for_download(user: dict, signals: dict) -> str:
    if user.get("role") != ROLE_PATIENT:
        return "Health report download is only available for patients."
    with session_scope() as s:
        records = s.query(HealthRecord).filter(
            HealthRecord.patient_id == user.get("id")
        ).order_by(HealthRecord.recorded_at.desc()).all()
        if not records:
            return "No health records found. Please visit a doctor first."
        from services.patient_ai_service import get_health_summary
        summary_data = get_health_summary(records)
        from views.patient_dashboard import generate_medication_report_pdf
        pdf_bytes = generate_medication_report_pdf(list(records), user)
        signals["generate_report"]  = True
        signals["report_pdf_bytes"] = pdf_bytes
        signals["report_filename"]  = f"IPCMS_AI_Health_Report_{user.get('id')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        summary_text = summary_data.get("summary", "Report generated.")
        abnormal = summary_data.get("abnormal_tests", [])
        tips     = summary_data.get("lifestyle_tips", [])
        warnings = summary_data.get("warnings", [])
        recovery = summary_data.get("recovery_progress", "N/A")
        lines = [f"### 📋 AI Health Report — {user.get('full_name', 'Patient')}\n",
                 f"**Overall Status:** {summary_text}\n",
                 f"**Recovery Progress:** {recovery}\n"]
        if abnormal:
            lines.append("**🧪 Abnormal Tests:**")
            for item in abnormal: lines.append(f"- 🔴 {item}")
            lines.append("")
        if tips:
            lines.append("**💡 Lifestyle Tips:**")
            for item in tips: lines.append(f"- 🍏 {item}")
            lines.append("")
        if warnings:
            lines.append("**⚠️ Warnings:**")
            for item in warnings: lines.append(f"- ⚠️ {item}")
            lines.append("")
        lines.append(f"**Total Records Analysed:** {len(records)}")
        lines.append("\n✅ Your PDF report is ready — use the **⬇️ Download** button below!")
        return "\n".join(lines)

# ── Direct Intent Matcher (multilingual) ─────────────────────────────────────

def _query_mysql_directly(message: str, user: dict, signals: dict) -> Optional[str]:
    """Match the user's query (in any supported language) to a direct DB call or instant response."""
    msg = message.lower().strip()

    def _any(kw_list):
        return any(k in msg for k in kw_list)

    # 1. Instant Greetings (< 1ms)
    greetings = ["hi", "hello", "hey", "vanakkam", "namaste", "namaskaram", "வணக்கம்", "नमस्ते", "നമസ്കാരം", "నమస్కారం"]
    if msg in greetings or any(msg == g for g in greetings):
        return (
            f"Hello **{user.get('full_name', 'there')}**! 👋 How can I help you today?\n\n"
            "You can ask me about:\n"
            "- 💊 **Medicines & Stock** (*'Show pharmacy medicines'*)\n"
            "- 📅 **Appointments** (*'Show my appointments'*)\n"
            "- 👨‍⚕️ **Doctors** (*'List doctors'*)\n"
            "- 📋 **Health Reports** (*'Download my report'*)\n"
            "- 🏥 **Clinic Summary** (*'Show clinic stats'*)\n"
            "- 🎤 Voice queries in **English, Tamil, Malayalam, Hindi, or Telugu**!"
        )

    # Booking intent
    if _any(_KW_BOOKING):
        signals["start_booking"] = True
        return (
            "Sure! I've opened the **📅 Appointment Booking Wizard** below.\n\n"
            "Please select your specialty, preferred doctor, date, and time slot."
        )

    # Health report / download
    if _any(_KW_REPORT):
        return fetch_health_report_for_download(user, signals)

    # Pharmacy orders
    if _any(_KW_PHARMACY_ORDER):
        return fetch_pharmacy_orders_db(user)

    # Highest cost / most expensive medicines or tablets
    if any(k in msg for k in [
        "high cost tablet", "highest cost tablet", "high cost medicine", "highest cost medicine",
        "highest price tablet", "highest price medicine", "expensive tablet", "expensive medicine",
        "most expensive tablet", "most expensive medicine", "costliest tablet", "costliest medicine",
        "high price tablet", "high price medicine", "highest cost", "high cost", "most expensive",
        "அதிக விலை மாத்திரை", "அதிக விலை மருந்து", "விலை உயர்ந்த மாத்திரை", "விலை உயர்ந்த மருந்து", "அதிக விலை",
        "महंगी दवा", "सबसे महंगी दवा", "ఎక్కువ ధర గల మందులు", "കൂടിയ விலையுள்ள மருந்து"
    ]) and any(k in msg for k in ["tablet", "medicine", "pharmacy", "drug", "pill", "மாத்திரை", "மருந்து", "दवा", "मందులు", "cost", "price", "expensive"]):
        return fetch_top_medicines_by_price_db(limit=5, ascending=False)

    # Lowest cost / cheapest medicines or tablets
    if any(k in msg for k in [
        "low cost tablet", "lowest cost tablet", "low cost medicine", "lowest cost medicine",
        "lowest price tablet", "lowest price medicine", "cheapest tablet", "cheapest medicine",
        "least expensive tablet", "least expensive medicine", "affordable tablet", "affordable medicine",
        "low price tablet", "low price medicine", "lowest cost", "low cost", "cheapest",
        "குறைந்த விலை மாத்திரை", "குறைந்த விலை மருந்து", "மலிவான மாத்திரை", "மலிவான மருந்து", "குறைந்த விலை",
        "सस्ती दवा", "कम कीमत वाली दवा", "తక్కువ ధర గల మందులు", "കുറഞ്ഞ விலையுள்ள மருந்து"
    ]) and any(k in msg for k in ["tablet", "medicine", "pharmacy", "drug", "pill", "மாத்திரை", "மருந்து", "दवा", "మందులు", "cost", "price", "cheap"]):
        return fetch_top_medicines_by_price_db(limit=5, ascending=True)

    # Pharmacy medicines & stock
    if _any(_KW_PHARMACY):
        kw = ""
        for word in ["paracetamol","amoxicillin","amlodipine","insulin","cough",
                     "antibiotic","diabetes","cardiology","metformin","atorvastatin",
                     "eye drops","cream"]:
            if word in msg:
                kw = word; break
        return fetch_pharmacy_medicines_db(kw)

    # Highest fee / top doctors
    if any(k in msg for k in ["highest fee","top doctors","most expensive doctor"]):
        return fetch_top_doctors_by_fee_db(3)

    # Health condition
    if _any(_KW_HEALTH):
        return fetch_my_health_condition_db(user)

    # Appointment counts
    if "completed" in msg and "appointment" in msg:
        return fetch_appointment_count_db(user, "Completed")
    if "pending" in msg and "appointment" in msg:
        return fetch_appointment_count_db(user, "Scheduled")

    # Doctor credentials
    if any(k in msg for k in ["doctor credentials","doctor info","doctor details",
                               "doctor profile","credentials"]):
        return fetch_doctor_credentials_db()

    # Patient list
    if _any(_KW_PATIENTS):
        return fetch_patient_list_db()

    # Doctor list
    if _any(_KW_DOCTORS):
        return fetch_doctor_list_db()

    # Appointment list
    if _any(_KW_APPOINTMENTS):
        return fetch_appointments_db(user)

    if "how many" in msg and "appointment" in msg:
        return fetch_appointments_db(user)

    # Clinic summary
    if _any(_KW_SUMMARY):
        return fetch_clinic_summary_db()

    # Broad single-word fallbacks for instantaneous response
    if msg in ["doctor", "doctors", "டாக்டர்", "ഡോക്ടർ", "डॉक्टर", "డాక్టర్"]:
        return fetch_doctor_list_db()
    if msg in ["medicine", "medicines", "tablets", "pharmacy", "மருந்து", "മരുന്ന്", "दवा", "మందులు"]:
        return fetch_pharmacy_medicines_db()
    if msg in ["appointment", "appointments", "schedule", "சந்திப்பு", "అపాయింట్మెంట్"]:
        return fetch_appointments_db(user)
    if msg in ["patient", "patients", "நோயாளி", "रोगी", "రోగి"]:
        return fetch_patient_list_db()
    if msg in ["report", "reports", "அறிக்கை", "रिपोर्ट", "నివేదిక"]:
        return fetch_health_report_for_download(user, signals)

    return None

# ── LangChain Tools ────────────────────────────────────────────────────────────

def get_all_agent_tools(user: dict):
    @tool
    def tool_list_all_patients() -> str:
        """Fetch complete directory of registered patients from the database."""
        return fetch_patient_list_db()

    @tool
    def tool_list_all_doctors() -> str:
        """Fetch active doctors, specialties, experience, and fees from the database."""
        return fetch_doctor_list_db()

    @tool
    def tool_doctor_credentials() -> str:
        """Fetch full doctor profiles including bio, email, phone and credentials."""
        return fetch_doctor_credentials_db()

    @tool
    def tool_list_appointments() -> str:
        """Fetch this user's scheduled appointments from the database."""
        return fetch_appointments_db(user)

    @tool
    def tool_my_health() -> str:
        """Fetch this patient's complete health records including all specialty fields."""
        return fetch_my_health_condition_db(user)

    @tool
    def tool_appointment_count_scheduled() -> str:
        """Count how many upcoming scheduled appointments this user has."""
        return fetch_appointment_count_db(user, "Scheduled")

    @tool
    def tool_appointment_count_completed() -> str:
        """Count how many completed appointments this user has."""
        return fetch_appointment_count_db(user, "Completed")

    @tool
    def tool_list_pharmacy_medicines(keyword: str = "") -> str:
        """Fetch available pharmacy medicines, stock levels, prices and categories."""
        return fetch_pharmacy_medicines_db(keyword)

    @tool
    def tool_highest_cost_medicines(limit: int = 5) -> str:
        """Fetch the highest cost / most expensive pharmacy medicines and tablets."""
        return fetch_top_medicines_by_price_db(limit=limit, ascending=False)

    @tool
    def tool_lowest_cost_medicines(limit: int = 5) -> str:
        """Fetch the lowest cost / most affordable pharmacy medicines and tablets."""
        return fetch_top_medicines_by_price_db(limit=limit, ascending=True)

    @tool
    def tool_list_pharmacy_orders() -> str:
        """Fetch pharmacy order history and statuses."""
        return fetch_pharmacy_orders_db(user)

    @tool
    def tool_clinic_summary() -> str:
        """Get live clinic metrics — patient count, doctor count, appointment breakdown."""
        return fetch_clinic_summary_db()

    @tool
    def tool_start_booking() -> str:
        """Open the interactive appointment booking wizard."""
        return "Booking wizard opened."

    @tool
    def tool_generate_health_report() -> str:
        """Generate and prepare a downloadable AI-powered health report PDF for the patient."""
        return "Health report generated. Patient can download it using the button below the chat."

    return [
        tool_list_all_patients,
        tool_list_all_doctors,
        tool_doctor_credentials,
        tool_list_appointments,
        tool_my_health,
        tool_appointment_count_scheduled,
        tool_appointment_count_completed,
        tool_list_pharmacy_medicines,
        tool_highest_cost_medicines,
        tool_lowest_cost_medicines,
        tool_list_pharmacy_orders,
        tool_clinic_summary,
        tool_start_booking,
        tool_generate_health_report,
    ]

# ── Main Entrypoint ────────────────────────────────────────────────────────────

def ask(user: dict, message: str, history: Optional[List[dict]] = None, target_language: Optional[str] = None):
    """Execute chatbot query against live MySQL database and LLM. Never raises."""
    signals = {}

    # 1. Try direct DB intent matching (multilingual, no LLM needed)
    direct_res = _query_mysql_directly(message, user, signals)
    if direct_res and not (target_language and target_language not in ("Auto Detect", "English")):
        return direct_res, signals

    # 2. LLM agent tool loop
    llm   = get_llm()

    try:
        # Pre-gather DB context based on query keywords
        db_context_parts = []
        msg_l = message.lower()

        if any(k in msg_l for k in ["high cost", "highest cost", "highest price", "expensive", "costliest", "அதிக விலை", "விலை உயர்ந்த", "महंगी"]):
            db_context_parts.append(fetch_top_medicines_by_price_db(limit=5, ascending=False))
        elif any(k in msg_l for k in ["low cost", "lowest cost", "lowest price", "cheapest", "affordable", "குறைந்த விலை", "மலிவான", "सस्ती"]):
            db_context_parts.append(fetch_top_medicines_by_price_db(limit=5, ascending=True))
        elif any(k in msg_l for k in ["pharmacy", "medicine", "stock", "price", "tablet", "மருந்து", "दवा", "మందులు", "മരുന്ന്"]):
            kw = ""
            for word in ["paracetamol","amoxicillin","amlodipine","insulin","cough","metformin","atorvastatin"]:
                if word in msg_l: kw = word; break
            db_context_parts.append(fetch_pharmacy_medicines_db(kw))

        if any(k in msg_l for k in ["appointment", "schedule", "book", "சந்திப்பு", "अपॉइंटमेंट", "అపాయింట్మెంట్"]):
            db_context_parts.append(fetch_appointments_db(user))

        if any(k in msg_l for k in ["patient", "user", "profile", "நோயாளி", "रोगी", "రోగి"]):
            db_context_parts.append(fetch_patient_list_db())

        if any(k in msg_l for k in ["health", "condition", "vitals", "diagnosis", "ஆரோக்கியம்", "सेहत"]):
            db_context_parts.append(fetch_my_health_condition_db(user))

        if any(k in msg_l for k in ["stat", "summary", "count", "clinic", "சுருக்கம்", "सारांश", "సారాంశం"]):
            db_context_parts.append(fetch_clinic_summary_db())

        # Fallback context if no specific keywords matched
        if not db_context_parts:
            db_context_parts.append(fetch_clinic_summary_db())
            db_context_parts.append(fetch_doctor_list_db())

        live_db_data = "\n\n".join(db_context_parts)

        # ── Language rule for system prompt ─────────────────────────────────
        if target_language == "English":
            lang_rule = "REQUIRED OUTPUT LANGUAGE: Respond ONLY in English. Do not use any other language."
        elif target_language and target_language not in ("Auto Detect", None):
            lang_rule = (
                f"REQUIRED OUTPUT LANGUAGE: Respond ONLY in {target_language}. "
                f"Translate ALL text, questions and guidance into natural {target_language} using proper native script."
            )
        else:
            lang_rule = (
                "Detect the language of the user's message. "
                "ALWAYS respond in THE EXACT SAME LANGUAGE the user wrote in."
            )

        role = user.get("role", "Patient")

        if role == "Admin":
            persona_block = (
                "## 🤖 Your Role: Admin's AI Assistant\n"
                "You are SMART CARE — a smart, professional AI assistant for hospital administrators at IPCMS.\n"
                f"Current Admin: {user.get('full_name', 'Admin')} | ID: #{user.get('id')}\n\n"

                "## 🎯 Admin Persona & Tone\n"
                "- You are sharp, efficient, and professional — like a smart executive assistant.\n"
                "- Give concise, data-driven answers. No fluff, no health advice.\n"
                "- Focus on: patient counts, doctor schedules, appointments, pharmacy stock, billing, analytics.\n"
                "- NEVER ask 'How are you feeling?'. You are talking to an administrator, not a patient.\n"
                "- Respond conversationally and naturally — like a capable AI co-worker, not a reading machine.\n\n"

                "## 📋 Admin Tasks You Handle\n"
                "- Show patient/doctor summaries, appointment lists, low stock medicines\n"
                "- Provide clinic analytics and revenue summaries\n"
                "- Answer questions about system data and hospital operations\n"
                "- Suggest actions based on data (e.g. 'Medicine X is low, consider restocking')\n\n"

                "## 🗣️ Conversation Style\n"
                "- Keep responses SHORT and direct — 2-4 sentences max unless data is needed.\n"
                "- Use bullet points for lists of data.\n"
                "- End with ONE relevant follow-up only if it helps the admin's next task.\n"
                "- NEVER mention health symptoms, diagnoses, or medical advice.\n\n"
            )
        elif role == "Doctor":
            persona_block = (
                "## 🩺 Your Role: Doctor's AI Assistant\n"
                "You are SMART CARE — a smart, professional AI clinical assistant for doctors at IPCMS.\n"
                f"Current Doctor: {user.get('full_name', 'Doctor')} | ID: #{user.get('id')}\n\n"

                "## 🎯 Doctor Persona & Tone\n"
                "- You are professional, knowledgeable, and precise — like a smart medical secretary.\n"
                "- Help doctors with patient lists, appointments, lab results, and prescriptions.\n"
                "- NEVER ask 'How are you feeling?'. You are talking to a doctor, not a patient.\n"
                "- Do NOT ask symptom-based questions. The doctor is the medical expert.\n"
                "- Respond naturally and conversationally — like a capable AI co-worker.\n\n"

                "## 📋 Doctor Tasks You Handle\n"
                "- Show today's appointments and patient schedule\n"
                "- List patients with pending prescriptions or follow-ups\n"
                "- Provide patient health summaries and lab results\n"
                "- Answer clinical data queries from the hospital system\n"
                "- Help draft clinical notes or reminders\n\n"

                "## 🗣️ Conversation Style\n"
                "- Keep responses SHORT and clinical — 2-4 sentences unless detail is requested.\n"
                "- Use bullet points when listing patient data or appointments.\n"
                "- End with ONE relevant follow-up only if it helps the doctor's next task.\n"
                "- NEVER give health advice to the doctor as if they were a patient.\n\n"
            )
        else:  # Patient
            persona_block = (
                "## 🌸 Your Role: AI Health Assistant\n"
                "You are SMART CARE — a warm, caring, empathetic AI healthcare voice assistant at IPCMS hospital.\n"
                f"Current Patient: {user.get('full_name', 'Patient')} | ID: #{user.get('id')}\n\n"

                "## 🌸 Patient Persona & Tone\n"
                "- You are warm, gentle, caring, and compassionate — like a kind nurse or hospital receptionist.\n"
                "- Speak in short, clear, easy-to-understand sentences suitable for text-to-speech.\n"
                "- Always use the patient's first name warmly.\n"
                "- Encourage patients gently when they seem confused or distressed.\n"
                "- NEVER sound robotic, cold, or like you are reading a list. Be natural and conversational.\n\n"

                "## 🔢 ONE QUESTION RULE (CRITICAL)\n"
                "- Ask ONLY ONE question per response. NEVER ask two questions at once.\n"
                "- Wait for the patient's answer before asking the next question.\n"
                "- Base your next question entirely on what the patient just said.\n\n"

                "## 🏥 Medical Safety Rules\n"
                "- NEVER diagnose diseases or prescribe medications.\n"
                "- Collect symptom information and offer general health guidance only.\n"
                "- Always recommend consulting a qualified doctor.\n"
                "- ⚠️ EMERGENCY: If the patient reports severe chest pain, difficulty breathing, "
                "loss of consciousness, seizures, or heavy bleeding — IMMEDIATELY tell them to call "
                "emergency services or go to the nearest hospital right away.\n\n"

                "## 🗣️ Natural Conversation Flow\n"
                "Guide the conversation naturally. Typical symptom flow:\n"
                "1. Ask: 'How are you feeling today?' only on the FIRST message.\n"
                "2. Ask about symptoms based on their answer.\n"
                "3. Ask when symptoms started.\n"
                "4. Ask about pain (yes/no) → if yes: location → severity 1-10.\n"
                "5. Ask relevant follow-up based on symptoms.\n"
                "6. After enough info, warmly recommend seeing a doctor.\n\n"
            )

        system_prompt = (
            persona_block +
            "## 🌐 Language Rule\n"
            f"{lang_rule}\n\n"

            "## 📊 Live Hospital Data (use ONLY when asked about appointments, doctors, medicines, reports)\n"
            f"{live_db_data}\n\n"

            "## Final Instructions\n"
            "1. Always respond naturally — never like you are reading a script.\n"
            "2. For hospital data queries: answer using Live Hospital Data above.\n"
            "3. Keep responses short, warm, and voice-friendly.\n"
            "4. Match the language and tone to the user's role at all times."
        )

        lc_messages = [SystemMessage(content=system_prompt)]
        if history:
            for h in history[-8:]:
                r, c = h.get("role"), h.get("content", "")
                if r == "user": lc_messages.append(HumanMessage(content=c[:300]))
                elif r == "assistant": lc_messages.append(AIMessage(content=c[:300]))
        lc_messages.append(HumanMessage(content=message))

        res = llm.invoke(lc_messages)
        answer = res.content if hasattr(res, "content") else str(res)
        return (answer or "Here is the information from your Smart Care database."), signals

    except Exception as exc:
        log.exception("Chatbot LLM error: %s", exc)
        msg_l = message.lower()
        if any(k in msg_l for k in ["patient","நோயாளி","रोगी","రోగి"]):
            return fetch_patient_list_db(), signals
        elif any(k in msg_l for k in ["doctor","மருத்துவர்","डॉक्टर","డాక్టర్","ഡോക്ടർ"]):
            return fetch_doctor_list_db(), signals
        elif any(k in msg_l for k in ["appointment","சந்திப்பு","अपॉइंटमेंट","అపాయింట్మెంట్"]):
            return fetch_appointments_db(user), signals
        elif any(k in msg_l for k in ["pharmacy","medicine","tablet","மருந்து","दवा"]):
            return fetch_pharmacy_medicines_db(), signals
        else:
            return fetch_clinic_summary_db(), signals

def get_smartcare_response(query: str, user_id: int) -> str:
    user = {"id": user_id, "role": ROLE_PATIENT}
    ans, _ = ask(user, query)
    return ans
