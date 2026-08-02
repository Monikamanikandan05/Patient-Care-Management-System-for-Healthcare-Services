import streamlit as st
from core.database import SessionLocal
from models.models import ChatMessage
from ai.smartcare_agent import ask
from ai.booking_flow import render_booking_wizard

def render_chatbot_view():
    st.write("### 🤖 SMART CARE AI Health Assistant")
    st.write("Ask me anything — doctor availability, health summaries, appointments, or type **'create an appointment'** to book one.")

    if "show_booking_wizard" not in st.session_state:
        st.session_state.show_booking_wizard = False

    user = st.session_state.user

    db = SessionLocal()
    try:
        if "chat_history" not in st.session_state:
            db_msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user["id"]).order_by(ChatMessage.created_at.asc()).all()
            st.session_state.chat_history = [{"role": msg.role, "content": msg.content} for msg in db_msgs]

            if not st.session_state.chat_history:
                welcome_msg = (
                    f"Hello **{user['full_name']}**! 👋 I am your **SMART CARE AI** ({user['role']} Portal).\n\n"
                    "Here's what I can help you with:\n"
                    "- 📋 **Patient & Doctor Directory** — *'List doctors'*, *'Show patients'*\n"
                    "- 📅 **Appointments** — *'Create an appointment'*, *'Show upcoming appointments'*\n"
                    "- 💊 **Health Info** — *'What is my health condition?'*\n"
                    "- 📊 **Clinic Stats** — *'Show clinic summary'*\n\n"
                    "Just type your question below! 👇"
                )
                st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
                db_msg = ChatMessage(user_id=user["id"], role="assistant", content=welcome_msg)
                db.add(db_msg)
                db.commit()

        # Render chat message history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Always render booking wizard if active (appears right after chat messages)
        if st.session_state.show_booking_wizard:
            st.markdown("---")
            if user.get("role") == "Patient":
                render_booking_wizard(user)
            else:
                st.info("ℹ️ Appointment booking via chat is available to Patients only. Use the **Appointments** tab instead.")
                if st.button("Close"):
                    st.session_state.show_booking_wizard = False
                    st.rerun()

        # Chat input at bottom
        if prompt := st.chat_input("Message SmartCare AI…"):
            # Show user message immediately
            with st.chat_message("user"):
                st.markdown(prompt)

            st.session_state.chat_history.append({"role": "user", "content": prompt})
            db_msg = ChatMessage(user_id=user["id"], role="user", content=prompt)
            db.add(db_msg)
            db.commit()

            with st.spinner("SmartCare AI is thinking…"):
                response_text, signals = ask(user, prompt, st.session_state.chat_history[:-1])

            # Save assistant response
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            db_res = ChatMessage(user_id=user["id"], role="assistant", content=response_text)
            db.add(db_res)
            db.commit()

            # If booking wizard was triggered, set flag and rerun so wizard renders immediately
            booking_triggered = signals.get("start_booking") or "booking wizard" in response_text.lower()
            if booking_triggered:
                st.session_state.show_booking_wizard = True
                st.rerun()  # Rerun so wizard appears right after the assistant message

            # If no booking, just rerun to show the assistant message cleanly
            st.rerun()

    finally:
        db.close()
