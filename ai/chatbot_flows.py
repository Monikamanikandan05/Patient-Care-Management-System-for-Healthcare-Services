"""
chatbot_flows.py
────────────────
Guided step-by-step chatbot flows for:
  • Appointment booking  (steps: doctor → date → time → reason → confirm)
  • Pharmacy order       (steps: medicine → quantity → confirm)

Each flow is driven by session_state keys so the user goes question-by-question.
All DB writes happen only when the user clicks "Confirm".
"""
import datetime
import streamlit as st
import streamlit.components.v1 as components
from core.database import SessionLocal
from models.models import Doctor, User, Specialty, PharmacyMedicine
from services import appointment_service
from services import pharmacy_service
from decimal import Decimal


# ── Session-State Keys ─────────────────────────────────────────────────────────
APPT_STEP_KEY  = "_appt_flow_step"    # int 0-5
APPT_DATA_KEY  = "_appt_flow_data"    # dict

PHARMA_STEP_KEY  = "_pharma_flow_step"   # int 0-3
PHARMA_DATA_KEY  = "_pharma_flow_data"   # dict

FLOW_GEN_KEY   = "_flow_btn_gen"       # int — bump to force button key uniqueness


# ── Helpers ────────────────────────────────────────────────────────────────────
def _gen() -> int:
    return st.session_state.get(FLOW_GEN_KEY, 0)


def _bump():
    st.session_state[FLOW_GEN_KEY] = _gen() + 1


def _step_header(icon: str, title: str, subtitle: str):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(124,58,237,0.18),rgba(6,182,212,0.10));
                border:1.5px solid rgba(139,92,246,0.45);border-radius:14px;
                padding:14px 18px;margin:8px 0 10px;">
      <div style="font-size:1.05rem;font-weight:800;color:#c4b5fd;margin-bottom:2px;">
        {icon} {title}
      </div>
      <div style="font-size:0.81rem;color:#94a3b8;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def _cancel_btn(flow: str):
    g = _gen()
    if st.button("✖ Cancel", key=f"cancel_{flow}_{g}", type="secondary"):
        if flow == "appt":
            st.session_state.pop(APPT_STEP_KEY, None)
            st.session_state.pop(APPT_DATA_KEY, None)
        else:
            st.session_state.pop(PHARMA_STEP_KEY, None)
            st.session_state.pop(PHARMA_DATA_KEY, None)
        _bump()
        st.rerun()


def _push_chat_msg(msg: str, user_id: int, db):
    from models.models import ChatMessage
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    db.add(ChatMessage(user_id=user_id, role="assistant", content=msg))
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  APPOINTMENT FLOW
# ═══════════════════════════════════════════════════════════════════════════════

TIME_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "12:00 PM",
    "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
    "04:00 PM", "04:30 PM", "05:00 PM",
]

VISIT_REASONS = [
    "🩺 Routine Health Checkup",
    "💔 Cardiac Consultation",
    "💊 Prescription Renewal / Refill",
    "🧪 Lab Test Follow-up",
    "🤒 Fever / Infection",
    "😣 Pain / Discomfort",
    "🧠 Mental Health Consultation",
    "👁️ Eye / ENT Consultation",
    "🦷 Dental Issue",
    "🍼 Child Health / Pediatrics",
]


def start_appointment_flow():
    """Trigger the appointment guided flow from scratch."""
    st.session_state[APPT_STEP_KEY] = 1
    st.session_state[APPT_DATA_KEY] = {}
    _bump()


def render_appointment_flow(user: dict):
    """Render the current appointment flow step. Call this in the chatbot view."""
    step = st.session_state.get(APPT_STEP_KEY, 0)
    if step == 0:
        return  # Flow not active

    data = st.session_state.setdefault(APPT_DATA_KEY, {})
    g    = _gen()

    # ── STEP 1 — Choose Doctor ─────────────────────────────────────────────────
    if step == 1:
        _step_header("👨‍⚕️", "Step 1 of 4 — Choose Your Doctor",
                     "Tap a doctor card to select. You can also cancel below.")
        db = SessionLocal()
        docs = []
        try:
            from sqlalchemy.orm import joinedload
            raw_docs = (db.query(Doctor)
                    .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
                    .join(User, Doctor.user_id == User.id)
                    .join(Specialty, Doctor.specialty_id == Specialty.id)
                    .filter(User.is_active == True)
                    .all())
            for d in raw_docs:
                docs.append({
                    "id": d.id,
                    "doc_name": f"Dr. {d.user.full_name}" if d.user else "Doctor",
                    "spec_name": d.specialty.name if d.specialty else "General",
                    "exp_text": f"{d.experience_years} yrs exp" if d.experience_years else "",
                    "fee_text": f"₹{int(d.consultation_fee or 0)} / visit",
                    "fee": int(d.consultation_fee or 0)
                })
        finally:
            db.close()

        if not docs:
            st.warning("No doctors available right now. Please try later.")
            _cancel_btn("appt")
            return

        cols = st.columns(min(len(docs), 3))
        for i, d in enumerate(docs):
            doc_id    = d["id"]
            doc_name  = d["doc_name"]
            spec_name = d["spec_name"]
            exp_text  = d["exp_text"]
            fee_text  = d["fee_text"]
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:rgba(30,27,75,0.85);border:1px solid #4338ca;
                            border-radius:12px;padding:10px 12px;margin-bottom:6px;text-align:center;">
                  <div style="font-size:1.5rem">👨‍⚕️</div>
                  <div style="color:#c7d2fe;font-weight:700;font-size:0.9rem;">{doc_name}</div>
                  <div style="color:#818cf8;font-size:0.78rem;">{spec_name}</div>
                  <div style="color:#64748b;font-size:0.74rem;">{exp_text} · {fee_text}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Select", key=f"appt_doc_{doc_id}_{g}", use_container_width=True, type="primary"):
                    data["doctor_id"]   = doc_id
                    data["doctor_name"] = doc_name
                    data["specialty"]   = spec_name
                    data["fee"]         = d["fee"]
                    st.session_state[APPT_STEP_KEY] = 2
                    _bump()
                    st.rerun()
        _cancel_btn("appt")

    # ── STEP 2 — Choose Date ───────────────────────────────────────────────────
    elif step == 2:
        _step_header("📅", f"Step 2 of 4 — Pick a Date",
                     f"Doctor: {data.get('doctor_name','—')} · {data.get('specialty','—')}")
        today = datetime.date.today()

        # Show next 7 days as quick buttons
        date_cols = st.columns(7)
        for i in range(7):
            d_date = today + datetime.timedelta(days=i + 1)
            label  = d_date.strftime("%a\n%d %b")
            with date_cols[i]:
                if st.button(label, key=f"appt_date_{i}_{g}", use_container_width=True):
                    data["date"]       = d_date
                    data["date_label"] = d_date.strftime("%A, %d %B %Y")
                    st.session_state[APPT_STEP_KEY] = 3
                    _bump()
                    st.rerun()

        # Also allow manual date picker
        st.markdown("<div style='margin-top:6px;color:#64748b;font-size:12px;'>Or pick a custom date:</div>", unsafe_allow_html=True)
        custom_col, btn_col = st.columns([2, 1])
        with custom_col:
            picked = st.date_input("Custom date", min_value=today + datetime.timedelta(days=1),
                                   value=today + datetime.timedelta(days=1),
                                   key=f"appt_custom_date_{g}", label_visibility="collapsed")
        with btn_col:
            if st.button("Use this date ➜", key=f"appt_custom_date_ok_{g}", use_container_width=True):
                data["date"]       = picked
                data["date_label"] = picked.strftime("%A, %d %B %Y")
                st.session_state[APPT_STEP_KEY] = 3
                _bump()
                st.rerun()
        _cancel_btn("appt")

    # ── STEP 3 — Choose Time ───────────────────────────────────────────────────
    elif step == 3:
        _step_header("⏰", "Step 3 of 4 — Choose a Time Slot",
                     f"Date: {data.get('date_label','—')}  |  Doctor: {data.get('doctor_name','—')}")
        slot_cols = st.columns(4)
        for i, slot in enumerate(TIME_SLOTS):
            with slot_cols[i % 4]:
                if st.button(f"🕐 {slot}", key=f"appt_slot_{i}_{g}", use_container_width=True):
                    data["time_label"] = slot
                    # parse to time object
                    t_obj = datetime.datetime.strptime(slot, "%I:%M %p").time()
                    data["time_obj"]   = t_obj
                    st.session_state[APPT_STEP_KEY] = 4
                    _bump()
                    st.rerun()
        _cancel_btn("appt")

    # ── STEP 4 — Choose Reason ────────────────────────────────────────────────
    elif step == 4:
        _step_header("💬", "Step 4 of 4 — Reason for Visit",
                     f"{data.get('doctor_name','—')} · {data.get('date_label','—')} · {data.get('time_label','—')}")
        reason_cols = st.columns(2)
        for i, reason in enumerate(VISIT_REASONS):
            with reason_cols[i % 2]:
                if st.button(reason, key=f"appt_reason_{i}_{g}", use_container_width=True):
                    data["reason"] = reason
                    st.session_state[APPT_STEP_KEY] = 5
                    _bump()
                    st.rerun()

        # Custom reason input
        st.markdown("<div style='margin-top:8px;color:#94a3b8;font-size:12px;'>Or type your own reason:</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            custom_reason = st.text_input("Custom reason", placeholder="e.g. Follow-up for diabetes management",
                                          key=f"appt_custom_reason_{g}", label_visibility="collapsed")
        with c2:
            if st.button("Next ➜", key=f"appt_reason_ok_{g}", use_container_width=True) and custom_reason.strip():
                data["reason"] = custom_reason.strip()
                st.session_state[APPT_STEP_KEY] = 5
                _bump()
                st.rerun()
        _cancel_btn("appt")

    # ── STEP 5 — Confirmation ─────────────────────────────────────────────────
    elif step == 5:
        _step_header("✅", "Confirm Your Appointment",
                     "Please review your details below before confirming.")
        st.markdown(f"""
        <div style="background:rgba(16,185,129,0.08);border:1.5px solid rgba(16,185,129,0.4);
                    border-radius:14px;padding:18px 22px;margin:8px 0;">
          <table style="width:100%;border-collapse:collapse;color:#e2e8f0;font-size:0.92rem;">
            <tr><td style="padding:5px 0;color:#94a3b8;">👨‍⚕️ Doctor</td>
                <td style="padding:5px 0;font-weight:700;color:#a5f3fc;">{data.get('doctor_name','—')}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">🏥 Specialty</td>
                <td style="padding:5px 0;">{data.get('specialty','—')}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">📅 Date</td>
                <td style="padding:5px 0;">{data.get('date_label','—')}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">⏰ Time</td>
                <td style="padding:5px 0;">{data.get('time_label','—')}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">💬 Reason</td>
                <td style="padding:5px 0;">{data.get('reason','—')}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">💰 Fee</td>
                <td style="padding:5px 0;color:#fde68a;">₹{data.get('fee', 0)} / consultation</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

        ok_col, cancel_col = st.columns([1, 1])
        with ok_col:
            if st.button("✅ Confirm & Book Appointment", key=f"appt_confirm_{g}",
                         use_container_width=True, type="primary"):
                _do_book_appointment(data, user)
        with cancel_col:
            _cancel_btn("appt")


def _do_book_appointment(data: dict, user: dict):
    """Actually save the appointment to the DB and show success."""
    db = SessionLocal()
    try:
        appt = appointment_service.book_appointment(
            db=db,
            patient_id=user["id"],
            doctor_id=data["doctor_id"],
            date=data["date"],
            start_time=data["time_obj"],
            reason=data.get("reason", "Booked via SmartCare AI"),
            source="chatbot_flow"
        )
        success_msg = (
            f"🎉 **Appointment Confirmed!**\n\n"
            f"Your appointment has been successfully booked. Here are your details:\n\n"
            f"- 👨‍⚕️ **Doctor:** {data['doctor_name']}\n"
            f"- 🏥 **Specialty:** {data.get('specialty', '')}\n"
            f"- 📅 **Date:** {data['date_label']}\n"
            f"- ⏰ **Time:** {data['time_label']}\n"
            f"- 💬 **Reason:** {data.get('reason', 'General Consultation')}\n"
            f"- 🔖 **Appointment ID:** #{appt.id}\n\n"
            f"Please arrive **10 minutes early** and bring any previous reports. "
            f"You can view and manage your appointment in the **📅 Appointments** tab. "
            f"Take care and see you soon! 😊"
        )
        _push_chat_msg(success_msg, user["id"], db)

        # Reset flow
        st.session_state.pop(APPT_STEP_KEY, None)
        st.session_state.pop(APPT_DATA_KEY, None)
        _bump()
        st.success("🎉 Appointment booked successfully!")
        st.rerun()

    except ValueError as ve:
        st.error(f"⚠️ Booking conflict: {ve}")
    except Exception as exc:
        st.error(f"❌ Could not complete booking: {exc}")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  PHARMACY ORDER FLOW
# ═══════════════════════════════════════════════════════════════════════════════

PHARMA_QUANTITIES = [1, 2, 3, 5, 10, 15, 20, 30]


def start_pharmacy_flow():
    """Trigger the pharmacy order guided flow from scratch."""
    st.session_state[PHARMA_STEP_KEY] = 1
    st.session_state[PHARMA_DATA_KEY] = {}
    _bump()


def render_pharmacy_flow(user: dict):
    """Render the current pharmacy order flow step. Call this in the chatbot view."""
    step = st.session_state.get(PHARMA_STEP_KEY, 0)
    if step == 0:
        return

    data = st.session_state.setdefault(PHARMA_DATA_KEY, {})
    g    = _gen()

    # ── STEP 1 — Choose Medicine ───────────────────────────────────────────────
    if step == 1:
        _step_header("💊", "Step 1 of 2 — Choose a Medicine",
                     "Select the medicine you want to order from our pharmacy.")
        db = SessionLocal()
        meds_data = []
        try:
            meds = pharmacy_service.get_all_medicines(db)
            for m in meds:
                meds_data.append({
                    "id": m.id,
                    "name": m.name,
                    "generic_name": m.generic_name,
                    "category": m.category or "General",
                    "price": float(m.price),
                    "unit": m.unit,
                    "stock_qty": m.stock_qty
                })
        finally:
            db.close()

        if not meds_data:
            st.warning("No medicines available in pharmacy right now.")
            _cancel_btn("pharma")
            return

        # Group by category for cleaner UX
        cats = {}
        for m in meds_data:
            cats.setdefault(m["category"], []).append(m)

        for cat_name, cat_meds in cats.items():
            st.markdown(f"<div style='color:#818cf8;font-size:11.5px;font-weight:700;margin:8px 0 4px;letter-spacing:0.04em;text-transform:uppercase;'>{cat_name}</div>", unsafe_allow_html=True)
            med_cols = st.columns(min(len(cat_meds), 3))
            for i, m in enumerate(cat_meds):
                with med_cols[i % 3]:
                    stock_color = "#10b981" if m["stock_qty"] > 20 else "#f59e0b" if m["stock_qty"] > 0 else "#ef4444"
                    stock_label = f"✅ {m['stock_qty']} in stock" if m["stock_qty"] > 0 else "❌ Out of stock"
                    st.markdown(f"""
                    <div style="background:rgba(15,23,42,0.85);border:1px solid #334155;
                                border-radius:11px;padding:10px;margin-bottom:6px;text-align:center;">
                      <div style="font-size:1.3rem">💊</div>
                      <div style="color:#e2e8f0;font-weight:700;font-size:0.82rem;margin:3px 0;">{m['name']}</div>
                      <div style="color:#94a3b8;font-size:0.74rem;">{m['generic_name'] or ''}</div>
                      <div style="color:#fde68a;font-weight:700;font-size:0.85rem;margin:3px 0;">₹{m['price']:.2f} / {m['unit']}</div>
                      <div style="color:{stock_color};font-size:0.72rem;">{stock_label}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    disabled = m["stock_qty"] == 0
                    if st.button("Order", key=f"pharma_med_{m['id']}_{g}",
                                 use_container_width=True, type="primary", disabled=disabled):
                        data["medicine_id"]   = m["id"]
                        data["medicine_name"] = m["name"]
                        data["unit_price"]    = m["price"]
                        data["unit"]          = m["unit"]
                        data["max_stock"]     = m["stock_qty"]
                        st.session_state[PHARMA_STEP_KEY] = 2
                        _bump()
                        st.rerun()
        _cancel_btn("pharma")

    # ── STEP 2 — Choose Quantity ───────────────────────────────────────────────
    elif step == 2:
        med_name = data.get("medicine_name", "Medicine")
        unit_price = data.get("unit_price", 0)
        max_stock  = data.get("max_stock", 99)

        _step_header("🔢", f"Step 2 of 2 — How Many Units?",
                     f"Medicine: {med_name}  ·  ₹{unit_price:.2f} per unit")

        valid_qtys = [q for q in PHARMA_QUANTITIES if q <= max_stock]
        if not valid_qtys:
            valid_qtys = list(range(1, max_stock + 1))

        qty_cols = st.columns(min(len(valid_qtys), 4))
        for i, qty in enumerate(valid_qtys):
            total = unit_price * qty
            with qty_cols[i % 4]:
                if st.button(f"{qty} unit{'s' if qty > 1 else ''}\n₹{total:.0f}",
                             key=f"pharma_qty_{qty}_{g}", use_container_width=True, type="primary"):
                    data["quantity"]    = qty
                    data["total_price"] = total
                    st.session_state[PHARMA_STEP_KEY] = 3
                    _bump()
                    st.rerun()

        # Custom quantity
        st.markdown("<div style='margin-top:8px;color:#94a3b8;font-size:12px;'>Or enter a custom quantity:</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            custom_qty = st.number_input("Custom Qty", min_value=1, max_value=max_stock,
                                         value=1, key=f"pharma_custom_qty_{g}", label_visibility="collapsed")
        with c2:
            if st.button("Next ➜", key=f"pharma_custom_qty_ok_{g}", use_container_width=True):
                data["quantity"]    = int(custom_qty)
                data["total_price"] = unit_price * int(custom_qty)
                st.session_state[PHARMA_STEP_KEY] = 3
                _bump()
                st.rerun()
        _cancel_btn("pharma")

    # ── STEP 3 — Confirmation ─────────────────────────────────────────────────
    elif step == 3:
        _step_header("🛒", "Confirm Your Order",
                     "Review your order below and click Confirm to place it.")
        qty        = data.get("quantity", 1)
        med_name   = data.get("medicine_name", "Medicine")
        unit_price = data.get("unit_price", 0)
        total      = data.get("total_price", 0)
        unit_label = data.get("unit", "unit")

        st.markdown(f"""
        <div style="background:rgba(6,182,212,0.07);border:1.5px solid rgba(6,182,212,0.35);
                    border-radius:14px;padding:18px 22px;margin:8px 0;">
          <table style="width:100%;border-collapse:collapse;color:#e2e8f0;font-size:0.92rem;">
            <tr><td style="padding:5px 0;color:#94a3b8;">💊 Medicine</td>
                <td style="padding:5px 0;font-weight:700;color:#a5f3fc;">{med_name}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">📦 Unit</td>
                <td style="padding:5px 0;">{unit_label}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">🔢 Quantity</td>
                <td style="padding:5px 0;">{qty} unit{'s' if qty > 1 else ''}</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;">💵 Unit Price</td>
                <td style="padding:5px 0;">₹{unit_price:.2f} per unit</td></tr>
            <tr><td style="padding:5px 0;color:#94a3b8;font-weight:700;">💰 Total</td>
                <td style="padding:5px 0;font-weight:800;color:#fde68a;font-size:1.05rem;">₹{total:.2f}</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

        ok_col, cancel_col = st.columns([1, 1])
        with ok_col:
            if st.button("✅ Confirm & Place Order", key=f"pharma_confirm_{g}",
                         use_container_width=True, type="primary"):
                _do_place_order(data, user)
        with cancel_col:
            _cancel_btn("pharma")


def _do_place_order(data: dict, user: dict):
    """Actually save the pharmacy order to the DB and show success."""
    db = SessionLocal()
    try:
        cart = [{"medicine_id": data["medicine_id"], "quantity": data["quantity"]}]
        order = pharmacy_service.place_order(db=db, patient_id=user["id"], cart=cart)

        success_msg = (
            f"🛒 **Order Placed Successfully!**\n\n"
            f"Your pharmacy order has been confirmed and is being prepared.\n\n"
            f"- 💊 **Medicine:** {data['medicine_name']}\n"
            f"- 📦 **Quantity:** {data['quantity']} unit{'s' if data['quantity'] > 1 else ''}\n"
            f"- 💰 **Total Amount:** ₹{data['total_price']:.2f}\n"
            f"- 🔖 **Order ID:** #{order.id}\n"
            f"- 📋 **Status:** Pending — Being prepared\n\n"
            f"👉 Please visit the **💊 Pharmacy** tab to track your order status. "
            f"Our pharmacist will have it ready for you shortly. Take care! 😊"
        )
        _push_chat_msg(success_msg, user["id"], db)

        # Reset flow
        st.session_state.pop(PHARMA_STEP_KEY, None)
        st.session_state.pop(PHARMA_DATA_KEY, None)
        _bump()
        st.success(f"✅ Order #{order.id} placed! Go check the Pharmacy tab.")
        st.rerun()

    except ValueError as ve:
        st.error(f"⚠️ Order issue: {ve}")
    except Exception as exc:
        st.error(f"❌ Could not place order: {exc}")
    finally:
        db.close()


# ── Active Flow Checker ───────────────────────────────────────────────────────
def is_appointment_flow_active() -> bool:
    return st.session_state.get(APPT_STEP_KEY, 0) > 0


def is_pharmacy_flow_active() -> bool:
    return st.session_state.get(PHARMA_STEP_KEY, 0) > 0
