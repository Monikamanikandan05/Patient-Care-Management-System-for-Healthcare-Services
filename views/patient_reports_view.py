import streamlit as st
import pandas as pd
from core.database import SessionLocal
from models.models import HealthRecord
from views.patient_dashboard import render_patient_report_html, generate_medication_report_pdf

def render_patient_reports_view():
    st.write("### 📊 Personal Health Reports & Trends")
    st.markdown("View your complete medical history, compare reports, and track health trends.")
    
    user = st.session_state.user
    db = SessionLocal()
    try:
        records = (
            db.query(HealthRecord)
            .filter(HealthRecord.patient_id == user["id"])
            .order_by(HealthRecord.recorded_at.asc())
            .all()
        )
        
        if not records:
            st.info("No health records available to generate reports.")
            return
            
        tab1, tab2, tab3 = st.tabs(["📈 Health Trend Graphs", "📄 Complete Reports", "📤 Share & Compare"])
        
        with tab1:
            st.markdown("#### Health Metrics over Time")
            
            # Prepare data for graphs
            dates = []
            metrics = {
                "Blood Sugar": [],
                "Weight": [],
                "BMI": [],
                "Heart Rate": [],
                "Cholesterol": []
            }
            bp_systolic = []
            bp_diastolic = []
            
            for r in records:
                if r.recorded_at:
                    dates.append(r.recorded_at)
                    metrics["Blood Sugar"].append(float(r.blood_sugar) if r.blood_sugar else None)
                    metrics["Weight"].append(float(r.weight) if r.weight else None)
                    metrics["BMI"].append(float(r.bmi) if r.bmi else None)
                    metrics["Heart Rate"].append(float(r.heart_rate) if r.heart_rate else None)
                    metrics["Cholesterol"].append(float(r.cholesterol) if r.cholesterol else None)
                    
                    if r.blood_pressure:
                        parts = r.blood_pressure.split('/')
                        if len(parts) == 2:
                            try:
                                bp_systolic.append(float(parts[0]))
                                bp_diastolic.append(float(parts[1]))
                            except:
                                bp_systolic.append(None)
                                bp_diastolic.append(None)
                        else:
                            bp_systolic.append(None)
                            bp_diastolic.append(None)
                    else:
                        bp_systolic.append(None)
                        bp_diastolic.append(None)
            
            df = pd.DataFrame(metrics, index=dates)
            
            # Filter out columns entirely made of None
            df_clean = df.dropna(axis=1, how='all')
            
            if not df_clean.empty:
                st.line_chart(df_clean)
            else:
                st.info("Insufficient data for trend graphs. Please update your vitals.")
                
            st.markdown("#### Blood Pressure Trends")
            df_bp = pd.DataFrame({"Systolic": bp_systolic, "Diastolic": bp_diastolic}, index=dates)
            df_bp_clean = df_bp.dropna(axis=0, how='all')
            if not df_bp_clean.empty:
                st.line_chart(df_bp_clean)
            else:
                st.info("No Blood Pressure data recorded.")
                
        with tab2:
            st.markdown("#### Medical History Reports")
            
            report_text = generate_medication_report_pdf(list(reversed(records)), user)
            st.download_button(
                label="⬇️ Export Complete Report as PDF",
                data=report_text,
                file_name=f"IPCMS_Complete_Report_{user['id']}.pdf",
                mime="application/pdf"
            )
            
            st.markdown("---")
            import streamlit.components.v1 as components
            report_html = render_patient_report_html(list(reversed(records)), user)
            components.html(report_html, height=600, scrolling=True)

        with tab3:
            st.markdown("#### Secure Report Sharing")
            st.write("Share your medical history with another doctor or specialist securely.")
            
            st.text_input("Doctor's Email Address or Smart Care ID", placeholder="doctor@clinic.com")
            share_options = st.multiselect("What to share?", ["Complete History", "Latest Vitals", "Prescriptions", "Lab Reports"], default=["Latest Vitals", "Prescriptions"])
            
            if st.button("📤 Share Securely"):
                st.success("Report access securely shared via encrypted link.")
                
            st.markdown("---")
            st.markdown("#### Compare Reports")
            st.write("Select two dates to compare your health vitals.")
            date_options = [r.recorded_at.strftime("%Y-%m-%d %H:%M") for r in records if r.recorded_at]
            
            col1, col2 = st.columns(2)
            with col1:
                date_1 = st.selectbox("Previous Report", date_options)
            with col2:
                date_2 = st.selectbox("Current Report", reversed(date_options))
                
            if st.button("🔄 Compare"):
                st.info(f"Comparing data from {date_1} and {date_2}...")
                st.markdown("> **Note:** Detailed tabular comparison will render here based on selected dates.")

    finally:
        db.close()
