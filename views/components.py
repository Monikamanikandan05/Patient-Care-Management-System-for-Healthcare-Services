import os
import streamlit as st

def load_global_css():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        css_path = os.path.join(base_dir, "assets", "styles.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load custom stylesheet: {e}")

def load_login_bg_css():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_path = os.path.join(base_dir, "assets", "login_bg.png")
        if os.path.exists(img_path):
            import base64
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            bg_css = f"""
            <style>
            html, body, [data-testid="stAppViewContainer"], .stApp {{
                background-image: linear-gradient(rgba(11, 13, 16, 0.40), rgba(11, 13, 16, 0.60)), url("data:image/png;base64,{img_data}") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}

            [data-testid="stSidebar"] {{
                background-image: linear-gradient(rgba(11, 13, 16, 0.40), rgba(11, 13, 16, 0.60)), url("data:image/png;base64,{img_data}") !important;
                background-size: cover !important;
                background-position: left center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
                border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
                box-shadow: none !important;
            }}

            [data-testid="stSidebar"] * {{
                color: #ffffff !important;
            }}

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stWidgetLabel {{
                color: #ffffff !important;
                font-weight: 600 !important;
            }}

            [data-testid="stSidebar"] div[data-baseweb="select"] > div {{
                background-color: rgba(16, 24, 39, 0.75) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                color: #ffffff !important;
                border-radius: 8px !important;
            }}

            [data-testid="stSidebarCollapseButton"] *,
            [data-testid="collapsedControl"] *,
            [data-testid="stSidebar"] button[data-testid="baseButton-header"] * {{
                font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
            }}
            </style>
            """
            st.markdown(bg_css, unsafe_allow_html=True)
    except Exception:
        pass

def load_dashboard_bg_css(role: str = "Patient"):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_name = "dashboard_bg.jpg"
        if role == "Doctor":
            img_name = "doctor_bg.jpg"
        elif role == "Patient":
            img_name = "patient_bg.jpg"
        elif role == "Admin":
            img_name = "admin_bg.jpg"
            
        img_path = os.path.join(base_dir, "assets", img_name)
        if os.path.exists(img_path):
            import base64
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            bg_css = f"""
            <style>
            html, body, [data-testid="stAppViewContainer"], .stApp {{
                background-image: linear-gradient(rgba(11, 13, 16, 0.70), rgba(11, 13, 16, 0.85)), url("data:image/jpeg;base64,{img_data}") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}

            [data-testid="stSidebar"] {{
                background-image: linear-gradient(rgba(11, 13, 16, 0.65), rgba(11, 13, 16, 0.82)), url("data:image/jpeg;base64,{img_data}") !important;
                background-size: cover !important;
                background-position: left center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
                border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
                box-shadow: 4px 0 25px rgba(0, 0, 0, 0.4) !important;
            }}

            [data-testid="stSidebar"] * {{
                color: #f1f5f9 !important;
            }}

            [data-testid="stSidebar"] .sidebar-section-title {{
                color: #94a3b8 !important;
            }}

            [data-testid="stSidebar"] .sidebar-divider {{
                background-color: rgba(255, 255, 255, 0.12) !important;
            }}

            [data-testid="stSidebar"] div[data-testid="stTextInput"] input {{
                background-color: rgba(22, 25, 30, 0.8) !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                color: #ffffff !important;
            }}

            [data-testid="stSidebar"] button[kind="primary"] {{
                background: linear-gradient(135deg, rgba(37, 99, 235, 0.35) 0%, rgba(29, 78, 216, 0.45) 100%) !important;
                color: #60a5fa !important;
                border: none !important;
                border-left: 4px solid #3b82f6 !important;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25) !important;
                font-weight: 700 !important;
            }}

            [data-testid="stSidebar"] button[kind="secondary"] {{
                background-color: rgba(255, 255, 255, 0.03) !important;
                color: #cbd5e1 !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
            }}

            [data-testid="stSidebar"] button[kind="secondary"]:hover {{
                background-color: rgba(59, 130, 246, 0.18) !important;
                color: #60a5fa !important;
                border-color: rgba(59, 130, 246, 0.3) !important;
            }}

            [data-testid="stSidebarCollapseButton"] *,
            [data-testid="collapsedControl"] *,
            [data-testid="stSidebar"] button[data-testid="baseButton-header"] * {{
                font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
            }}
            </style>
            """
            st.markdown(bg_css, unsafe_allow_html=True)
    except Exception:
        pass



def load_patient_portal_css():
    """Specific CSS for the Patient Portal with a modern blue and white hospital-grade theme."""
    bg_css = f"""
    <style>
    /* Light blue and white modern theme */
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-color: #f0f4f8 !important; /* Soft light blue/grey background */
        background-image: none !important;
        color: #1e293b !important; /* Dark text for contrast */
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.05) !important;
    }}

    [data-testid="stSidebar"] * {{
        color: #334155 !important;
    }}

    [data-testid="stSidebar"] .sidebar-section-title {{
        color: #64748b !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
    }}

    [data-testid="stSidebar"] .sidebar-divider {{
        background-color: #e2e8f0 !important;
    }}

    /* Active Sidebar Button */
    [data-testid="stSidebar"] button[kind="primary"] {{
        background: linear-gradient(135deg, #e0e7ff 0%, #dbeafe 100%) !important;
        color: #1d4ed8 !important;
        border: none !important;
        border-left: 4px solid #2563eb !important;
        box-shadow: 0 2px 5px rgba(37, 99, 235, 0.1) !important;
        font-weight: 700 !important;
    }}

    /* Inactive Sidebar Button */
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background-color: transparent !important;
        color: #475569 !important;
        border: 1px solid transparent !important;
    }}

    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background-color: #f8fafc !important;
        color: #2563eb !important;
    }}

    /* Top Search Bar */
    [data-testid="stSidebar"] div[data-testid="stTextInput"] input {{
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #334155 !important;
    }}

    /* Cards and Containers */
    div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stExpander"] {{
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }}

    /* Text elements inside main container */
    [data-testid="stAppViewContainer"] h1, 
    [data-testid="stAppViewContainer"] h2, 
    [data-testid="stAppViewContainer"] h3, 
    [data-testid="stAppViewContainer"] h4 {{
        color: #0f172a !important;
    }}
    
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label {{
        color: #334155 !important;
    }}
    </style>
    """
    st.markdown(bg_css, unsafe_allow_html=True)

def render_centered_header(badge_text: str):
    html_content = (
        f'<div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid rgba(239, 68, 68, 0.25); padding-bottom: 20px;">'
        f'<h1 style="color: #ffffff; font-weight: 800; font-size: 2.5rem; letter-spacing: 0.1em; margin: 0; text-transform: uppercase; text-shadow: 0 0 10px rgba(239, 68, 68, 0.3);">SMART CARE</h1>'
        f'<span style="background-color: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 4px 15px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.2em; border: 1px solid rgba(239, 68, 68, 0.3); display: inline-block; margin-top: 8px;">{badge_text}</span>'
        f'</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def heartbeat_metric(label: str, value: str):
    """Render a metric with a heartbeat animation for the heart rate.
    The function emits a small HTML snippet that utilizes the `.heartbeat` CSS class.
    """
    html_snippet = f"""
    <div style='display:flex;flex-direction:column;align-items:center'>
        <span style='font-size:0.85rem;color:#9ca3af'>{label}</span>
        <div class='heartbeat' style='font-size:1.5rem;color:#ef4444'>{value}</div>
    </div>
    """
    st.markdown(html_snippet, unsafe_allow_html=True)

def html(content: str):
    import textwrap
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


def format_doctor_name(name: str) -> str:
    """Ensures a doctor's name has exactly ONE 'Dr.' prefix without duplicates like 'Dr. Dr.'"""
    if not name:
        return "Dr. Medical Specialist"
    s = str(name).strip()
    while s.lower().startswith("dr.") or s.lower().startswith("dr "):
        if s.lower().startswith("dr."):
            s = s[3:].strip()
        elif s.lower().startswith("dr "):
            s = s[3:].strip()
    return f"Dr. {s}"
