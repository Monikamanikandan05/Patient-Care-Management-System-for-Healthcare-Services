import logging
import datetime
import re
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

_RECURSION_LIMIT = 30

ROLE_PATIENT = "Patient"
ROLE_DOCTOR = "Doctor"
ROLE_ADMIN = "Admin"

def _parse_date(d_str: str) -> datetime.date:
    """Helper to parse dates like 'today', 'tomorrow', weekday names, or YYYY-MM-DD."""
    if not d_str or str(d_str).strip().lower() in ("today", ""):
        return datetime.date.today()
    s = str(d_str).strip().lower()
    if s == "tomorrow":
        return datetime.date.today() + datetime.timedelta(days=1)
    
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
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
        """Records every tool call so a booking or answer can be traced in terminal logs."""
        def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
            name = (serialized or {}).get("name", "?")
            log.info("tool_start user=%s role=%s tool=%s args=%s",
                     user.get("id"), user.get("role"), name, str(input_str)[:200])

        def on_tool_end(self, output: Any, **kwargs: Any) -> None:
            log.info("tool_end user=%s output=%s", user.get("id"), str(output)[:200])

        def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
            log.error("tool_error user=%s error=%s", user.get("id"), str(error))

    return ToolTracer()

# ── Direct MySQL Retrival Functions ──────────────────────────────────────────

def fetch_patient_list_db() -> str:
    """Query MySQL database for all registered patient profiles."""
    with session_scope() as s:
        patients = s.query(User).filter(User.role == 'Patient').all()
        if not patients:
            return "No patient profiles found in MySQL database."
        lines = [f"### 👥 Registered Patient Directory ({len(patients)} Patients in MySQL)\n"]
        lines.append("| Patient ID | Full Name | Email Address | Phone Number | Account Created |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for p in patients:
            created = p.created_at.strftime("%Y-%m-%d") if p.created_at else "N/A"
            lines.append(f"| #{p.id} | **{p.full_name}** | `{p.email}` | {p.phone or 'N/A'} | {created} |")
        return "\n".join(lines)

def fetch_doctor_list_db(specialty_filter: str = "") -> str:
    """Query MySQL database for all active doctor profiles."""
    with session_scope() as s:
        query = s.query(Doctor).join(User, Doctor.user_id == User.id)
        if specialty_filter:
            spec = s.query(Specialty).filter(Specialty.name.ilike(f"%{specialty_filter}%")).first()
            if spec:
                query = query.filter(Doctor.specialty_id == spec.id)
        docs = query.all()
        if not docs:
            return f"No doctors found matching specialty '{specialty_filter}'." if specialty_filter else "No active doctor records found in MySQL."
        
        lines = [f"### 👨‍⚕️ Active Clinical Practitioners ({len(docs)} Doctors in MySQL)\n"]
        lines.append("| Doctor Name | Specialty | Experience | Consult Fee | Email Contact |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for d in docs:
            name = d.user.full_name if d.user else "Practitioner"
            spec_name = d.specialty.name if d.specialty else "General"
            email = d.user.email if d.user else "N/A"
            lines.append(f"| **Dr. {name}** | `{spec_name}` | {d.experience_years or 0} Years | ₹{d.consultation_fee or 0:.0f} | `{email}` |")
        return "\n".join(lines)

def fetch_appointments_db(user: dict) -> str:
    """Query MySQL database for scheduled consultations."""
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
        else: # Admin
            appts = s.query(Appointment).order_by(Appointment.scheduled_date.desc(), Appointment.start_time).all()

        if not appts:
            return "No appointment records found in MySQL database."

        lines = [f"### 📅 Appointment Bookings ({len(appts)} Total Records in MySQL)\n"]
        lines.append("| Appt ID | Date & Time | Patient Name | Doctor / Specialty | Status | Reason |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for a in appts:
            p_name = a.patient.full_name if a.patient else f"Patient #{a.patient_id}"
            raw_name = a.doctor.user.full_name if (a.doctor and a.doctor.user) else "Practitioner"
            # Avoid double "Dr. Dr." if the name already starts with "Dr."
            if raw_name.lower().startswith("dr."):
                d_name = raw_name
            else:
                d_name = f"Dr. {raw_name}"
            spec_name = a.doctor.specialty.name if (a.doctor and a.doctor.specialty) else "General"
            dt_str = f"{a.scheduled_date.strftime('%Y-%m-%d')} at {a.start_time.strftime('%H:%M')}"
            status_badge = f"`{a.status}`"
            lines.append(f"| #{a.id} | {dt_str} | **{p_name}** | {d_name} ({spec_name}) | {status_badge} | {a.reason or 'Checkup'} |")
        return "\n".join(lines)

def fetch_clinic_summary_db() -> str:
    """Query MySQL for overall clinic status overview."""
    with session_scope() as s:
        total_users = s.query(User).count()
        total_patients = s.query(User).filter(User.role == 'Patient').count()
        total_doctors = s.query(Doctor).count()
        total_appts = s.query(Appointment).count()
        scheduled_appts = s.query(Appointment).filter(Appointment.status == 'Scheduled').count()
        completed_appts = s.query(Appointment).filter(Appointment.status == 'Completed').count()
        cancelled_appts = s.query(Appointment).filter(Appointment.status == 'Cancelled').count()

        return (
            "### 🏥 Smart Care IPCMS — MySQL Live Clinic Metrics\n\n"
            f"• **Registered Patients:** {total_patients} Patients\n"
            f"• **Active Practitioners:** {total_doctors} Doctors\n"
            f"• **Total Account Users:** {total_users} Users\n"
            f"• **Total Consultations Booked:** {total_appts}\n"
            f"  - ⏳ Scheduled: {scheduled_appts}\n"
            f"  - ✅ Completed: {completed_appts}\n"
            f"  - ❌ Cancelled: {cancelled_appts}\n"
        )

def fetch_top_doctors_by_fee_db(limit=3) -> str:
    """Query MySQL database for top doctors by consultation fee."""
    with session_scope() as s:
        docs = s.query(Doctor).join(User).order_by(Doctor.consultation_fee.desc()).limit(limit).all()
        if not docs:
            return "No active doctor records found in MySQL."
        
        lines = [f"### 🏆 Top {limit} Doctors by Consultation Fee\n"]
        lines.append("| Rank | Doctor Name | Specialty | Consult Fee |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for i, d in enumerate(docs, 1):
            name = d.user.full_name if d.user else "Practitioner"
            spec_name = d.specialty.name if d.specialty else "General"
            lines.append(f"| #{i} | **Dr. {name}** | `{spec_name}` | ₹{d.consultation_fee or 0:.0f} |")
        return "\n".join(lines)

def fetch_my_health_condition_db(user: dict) -> str:
    """Query MySQL database for patient's latest health record."""
    if user.get("role") != ROLE_PATIENT:
        return "You must be logged in as a patient to view your health condition."
    
    with session_scope() as s:
        record = s.query(HealthRecord).filter(HealthRecord.patient_id == user.get("id")).order_by(HealthRecord.recorded_at.desc()).first()
        if not record:
            return "No health records found in your profile."
        
        lines = ["### 🩺 Your Latest Health Condition\n"]
        lines.append(f"**Recorded On:** {record.recorded_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Diagnosis:** {record.diagnosis or 'N/A'}")
        if record.notes:
            lines.append(f"**Doctor's Notes:** {record.notes}")
        
        metrics = []
        if record.blood_pressure: metrics.append(f"Blood Pressure: {record.blood_pressure}")
        if record.heart_rate: metrics.append(f"Heart Rate: {record.heart_rate} bpm")
        if record.respiratory_rate: metrics.append(f"Respiratory Rate: {record.respiratory_rate} /min")
        if record.oxygen_saturation: metrics.append(f"SpO2: {record.oxygen_saturation}%")
        
        if metrics:
            lines.append("\n**Key Vitals:**")
            for m in metrics:
                lines.append(f"- {m}")
        
        return "\n".join(lines)

def fetch_appointment_count_db(user: dict, status: str) -> str:
    """Count appointments by status."""
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

# ── Direct Intent Matcher ─────────────────────────────────────────────────────

def _query_mysql_directly(message: str, user: dict, signals: dict) -> Optional[str]:
    """Inspects query text and executes direct SQL queries on MySQL when specific keywords match."""
    msg = message.lower().strip()

    # Booking intent trigger
    if any(k in msg for k in [
        "book appointment", "create an appointment", "create appointment",
        "schedule appointment", "make an appointment", "arrange appointment",
        "need an appointment", "i want to book", "book a doctor",
        "book now", "set an appointment", "fix an appointment",
        "book consultation", "book visit"
    ]):
        signals["start_booking"] = True
        return (
            "Sure! I've opened the **📅 Appointment Booking Wizard** below.\n\n"
            "Please select your **specialty**, preferred **doctor**, **date**, and **time slot** to confirm your appointment."
        )

    # Top fee intent
    if any(k in msg for k in ["highest fee", "top doctors", "most expensive"]):
        return fetch_top_doctors_by_fee_db(3)
        
    # Health condition intent
    if any(k in msg for k in ["health condition", "my health", "how is my health"]):
        return fetch_my_health_condition_db(user)
        
    # Appointment counts intent
    if "completed" in msg and "appointment" in msg:
        return fetch_appointment_count_db(user, "Completed")
        
    if "pending" in msg and "appointment" in msg:
        return fetch_appointment_count_db(user, "Scheduled")

    # Patient list intent
    if any(k in msg for k in ["patient list", "list patients", "show patients", "all patients", "registered patients", "who are the patients"]):
        return fetch_patient_list_db()

    # Doctor list intent
    if any(k in msg for k in ["doctor list", "doctors list", "list doctors", "show doctors", "all doctors", "find doctors", "specialist list"]):
        return fetch_doctor_list_db()

    # Appointment list intent — broad matching so new bookings are always visible
    if any(k in msg for k in [
        "upcoming appointments", "appointment list", "appointments list",
        "show appointments", "all appointments", "my appointments",
        "schedule list", "do i have", "any appointment", "booked appointment",
        "scheduled appointment", "my schedule", "show my"
    ]):
        return fetch_appointments_db(user)

    # Appointment count
    if "how many" in msg and "appointment" in msg:
        return fetch_appointments_db(user)

    # Clinic summary intent
    if any(k in msg for k in ["clinic overview", "clinic summary", "total appointments", "clinic stats", "system summary", "hospital metrics"]):
        return fetch_clinic_summary_db()

    return None

# ── LangChain Tool Definitions ─────────────────────────────────────────────

def get_all_agent_tools(user: dict):
    """Build tools with the actual logged-in user's context baked in so each patient sees their own data."""

    @tool
    def tool_list_all_patients() -> str:
        """Fetch complete directory of registered patients directly from MySQL database."""
        return fetch_patient_list_db()

    @tool
    def tool_list_all_doctors() -> str:
        """Fetch active doctors, specialties, experience, and fees directly from MySQL database."""
        return fetch_doctor_list_db()

    @tool
    def tool_list_appointments() -> str:
        """Fetch this user's scheduled appointments directly from MySQL database. Always use this to check appointments."""
        return fetch_appointments_db(user)

    @tool
    def tool_my_health() -> str:
        """Fetch this patient's latest health record from MySQL database."""
        return fetch_my_health_condition_db(user)

    @tool
    def tool_appointment_count_scheduled() -> str:
        """Count how many scheduled (upcoming) appointments this user has."""
        return fetch_appointment_count_db(user, "Scheduled")

    @tool
    def tool_appointment_count_completed() -> str:
        """Count how many completed appointments this user has."""
        return fetch_appointment_count_db(user, "Completed")

    @tool
    def tool_clinic_summary() -> str:
        """Get high-level MySQL clinic metrics (patient count, doctor count, appointment status breakdown)."""
        return fetch_clinic_summary_db()

    @tool
    def tool_start_booking() -> str:
        """Open the interactive appointment booking wizard for the user."""
        return "Opened the Guided Booking Wizard below for appointment selection."

    return [
        tool_list_all_patients,
        tool_list_all_doctors,
        tool_list_appointments,
        tool_my_health,
        tool_appointment_count_scheduled,
        tool_appointment_count_completed,
        tool_clinic_summary,
        tool_start_booking,
    ]

# ── Main Entrypoint Function ────────────────────────────────────────────────

def ask(user: dict, message: str, history: Optional[List[dict]] = None):
    """Executes chatbot queries against MySQL database & LLM agent. Never raises."""
    signals = {}

    # 1. First, check direct MySQL intent matchers for instant, error-free SQL data retrieval
    direct_res = _query_mysql_directly(message, user, signals)
    if direct_res:
        return direct_res, signals

    # 2. Try LLM agent tool loop
    llm = get_llm()
    # Always pass real user so tools fetch the correct patient's appointments
    tools = get_all_agent_tools(user)

    # If running in offline fallback mode or Groq is unreachable
    if isinstance(llm, OfflineMockLLM):
        # Fallback intelligent database keyword handler
        msg_l = message.lower()
        if "patient" in msg_l:
            return fetch_patient_list_db(), signals
        elif "doctor" in msg_l or "specialty" in msg_l:
            return fetch_doctor_list_db(), signals
        elif "appointment" in msg_l or "schedule" in msg_l:
            return fetch_appointments_db(user), signals
        elif "summary" in msg_l or "stat" in msg_l or "clinic" in msg_l:
            return fetch_clinic_summary_db(), signals
        else:
            return (
                "I am connected to your **MySQL Smart Care Database**. You can ask me for:\n"
                "• **Patient Directory**: *'Show patient list'*\n"
                "• **Doctor Roster**: *'List doctors and specialties'*\n"
                "• **Top Doctors**: *'Which doctor is taking highest fee?'*\n"
                "• **Appointments**: *'Show upcoming appointments', 'how many pending appointments?'*\n"
                "• **Health Status**: *'What is my health condition?'*\n"
                "• **Clinic Metrics**: *'Show clinic summary'*\n"
                "• **Bookings**: *'Create an appointment'*"
            ), signals

    # Standard LangGraph Tool-Calling Agent Execution
    try:
        system_prompt = (
            f"You are SMART CARE AI, an intelligent clinical assistant embedded in a hospital management system.\n"
            f"You are speaking with: {user.get('full_name', 'a user')} (Role: {user.get('role', 'Patient')}, ID: #{user.get('id')}).\n\n"
            "## Your Capabilities\n"
            "You have LIVE access to the Smart Care MySQL hospital database via tools. Always call the right tool before answering.\n"
            "IMPORTANT: The tools are already scoped to the current user. Do NOT pass user IDs manually.\n\n"
            "## Available Tools\n"
            "- `tool_list_all_patients` → Full patient directory from MySQL\n"
            "- `tool_list_all_doctors` → Doctor roster with specialties and consultation fees\n"
            "- `tool_list_appointments` → THIS user's own appointments from MySQL (already filtered to logged-in user)\n"
            "- `tool_my_health` → THIS user's own health records\n"
            "- `tool_appointment_count_scheduled` → Count of upcoming scheduled appointments for this user\n"
            "- `tool_appointment_count_completed` → Count of completed appointments for this user\n"
            "- `tool_clinic_summary` → High-level clinic statistics\n"
            "- `tool_start_booking` → Opens the appointment booking wizard\n\n"
            "## Response Rules\n"
            "1. ALWAYS use tools to get live data - never guess or make up patient/doctor names or counts.\n"
            "2. When a patient asks 'do I have appointments?' or 'show my appointments', ALWAYS call `tool_list_appointments`.\n"
            "3. Format responses clearly using Markdown (tables, bullet points, bold headers).\n"
            "4. Be concise, professional, and medically accurate.\n"
            "5. If the user asks about their health, call `tool_my_health`.\n"
            "6. If the user wants to book an appointment, call `tool_start_booking`.\n"
            "7. Never expose sensitive data unnecessarily.\n"
        )

        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt
        )
        lc_messages = []
        if history:
            for h in history:
                r = h.get("role")
                c = h.get("content", "")
                if r == "user":
                    lc_messages.append(HumanMessage(content=c))
                elif r == "assistant":
                    lc_messages.append(AIMessage(content=c))
        lc_messages.append(HumanMessage(content=message))

        config = {"callbacks": [_make_callback(user)], "recursion_limit": _RECURSION_LIMIT}
        result = agent.invoke({"messages": lc_messages}, config=config)
        messages = result.get("messages", [])
        answer = getattr(messages[-1], "content", "") if messages else ""
        return (answer or "I have processed your request from the Smart Care database."), signals

    except GraphRecursionError:
        return fetch_clinic_summary_db(), signals
    except Exception as exc:
        log.exception("Chatbot agent error: %s", exc)
        # Intelligent fallback to direct DB on any API/model error
        msg_l = message.lower()
        if "patient" in msg_l:
            return fetch_patient_list_db(), signals
        elif "doctor" in msg_l:
            return fetch_doctor_list_db(), signals
        elif "appointment" in msg_l:
            return fetch_appointments_db(user), signals
        else:
            return fetch_clinic_summary_db(), signals

def get_smartcare_response(query: str, user_id: int) -> str:
    user = {"id": user_id, "role": ROLE_PATIENT}
    ans, _ = ask(user, query)
    return ans
