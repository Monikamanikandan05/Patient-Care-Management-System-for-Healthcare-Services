import streamlit as st
import datetime
from core.database import SessionLocal
from services.auth_service import login_user, register_user
from views.components import render_centered_header, load_login_bg_css

def _calculate_age(dob):
    """Return age in years from a date object, or None if dob is None."""
    if dob is None:
        return None
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

ROLES = ["Patient", "Doctor", "Admin"]

ROLE_META = {
    "Patient": {"icon": "🧑‍⚕️", "color": "#22c55e"},
    "Doctor":  {"icon": "👨‍⚕️", "color": "#3b82f6"},
    "Admin":   {"icon": "🛡️",  "color": "#a855f7"},
}

def _role_selector(state_key: str):
    """Render three role toggle buttons and return the currently selected role."""
    if state_key not in st.session_state:
        st.session_state[state_key] = "Patient"

    cols = st.columns(3)
    for i, role in enumerate(ROLES):
        meta = ROLE_META[role]
        selected = st.session_state[state_key] == role
        # Build styled button HTML
        border_style = f"2px solid {meta['color']}" if selected else "1px solid rgba(255,255,255,0.12)"
        bg_style     = f"rgba({','.join(str(int(meta['color'].lstrip('#')[j:j+2], 16)) for j in (0,2,4))}, 0.22)" if selected else "rgba(255,255,255,0.04)"
        shadow_style = f"0 0 14px {meta['color']}88, 0 4px 12px {meta['color']}44" if selected else "none"
        opacity      = "1" if selected else "0.55"
        checkmark    = " ✓" if selected else ""

        btn_html = f"""
        <div id="role_display_{role}_{state_key}" style="
            background:{bg_style};
            border:{border_style};
            border-radius:12px;
            padding:12px 8px;
            text-align:center;
            box-shadow:{shadow_style};
            opacity:{opacity};
            transition:all .25s ease;
            margin-bottom:6px;
            cursor:pointer;">
            <div style="font-size:1.6rem;">{meta['icon']}</div>
            <div style="color:#fff;font-weight:700;font-size:.9rem;margin-top:4px;">{role}{checkmark}</div>
        </div>
        """
        with cols[i]:
            st.markdown(btn_html, unsafe_allow_html=True)
            if st.button(f"{meta['icon']} {role}", key=f"btn_{state_key}_{role}", use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state[state_key] = role
                st.rerun()

    # Show selected badge
    sel = st.session_state[state_key]
    c = ROLE_META[sel]["color"]
    st.markdown(
        f"<div style='text-align:center;margin:8px 0 16px;'>"
        f"<span style='background:{c}22;color:{c};border:1px solid {c};padding:4px 16px;"
        f"border-radius:20px;font-size:.85rem;font-weight:700;'>"
        f"{ROLE_META[sel]['icon']} Signing in as <b>{sel}</b></span></div>",
        unsafe_allow_html=True,
    )
    return st.session_state[state_key]


# ── PLACEHOLDERS CONFIG ───────────────────────────────────────────────────────
PLACEHOLDERS = {
    "Patient": {
        "email": "Enter your email id",
        "password": "Enter your patient portal password",
        "name": "Enter your name",
        "phone": "e.g., +1 555-019-2834 (Patient)",
    },
    "Doctor": {
        "email": "Enter your email id",
        "password": "Enter your practitioner access code",
        "name": "Enter your name",
        "phone": "e.g., +1 555-014-9988 (Doctor Office)",
    },
    "Admin": {
        "email": "Enter your email id",
        "password": "Enter your security pass key",
        "name": "Enter your name",
        "phone": "e.g., +1 555-017-1122 (Secure Admin Line)",
    }
}

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def render_login_view():
    load_login_bg_css()
    render_centered_header("LOGIN PORTAL")
    
    st.markdown("<h3 style='text-align: center; color: #a5b4fc; font-weight: 600; margin-bottom: 25px;'>Welcome to Smart Care PCMS-HS! 👋</h3>", unsafe_allow_html=True)

    st.markdown("#### Sign in as")
    selected_role = _role_selector("login_role")

    st.markdown("---")

    email    = st.text_input("Email Address", placeholder=PLACEHOLDERS[selected_role]["email"], key="login_email")
    password = st.text_input("Password", type="password", placeholder=PLACEHOLDERS[selected_role]["password"], key="login_password")

    if st.button("🔐 Sign In", key="login_btn", use_container_width=True):
        if not email.strip() or not password.strip():
            st.error("Please fill in both Email and Password fields.")
        else:
            db = SessionLocal()
            try:
                user = login_user(db, email, password)
                if user:
                    if user.role != selected_role:
                        st.error(
                            f"⚠️ This account is registered as **{user.role}**. "
                            f"Please select the **{user.role}** button above."
                        )
                    else:
                        st.session_state.logged_in = True
                        age = _calculate_age(user.dob) if user.role != "Admin" else None
                        st.session_state.user = {
                            "id":        user.id,
                            "full_name": user.full_name,
                            "email":     user.email,
                            "role":      user.role,
                            "gender":    user.gender,
                            "phone":     user.phone,
                            "dob":       user.dob,
                            "age":       age,
                        }
                        st.success(f"✅ Welcome back, {user.full_name}! Redirecting…")
                        st.rerun()
                else:
                    st.error("❌ Invalid Email or Password.")
            except Exception as e:
                st.error(f"Database error during login: {e}")
            finally:
                db.close()


# ── REGISTER ──────────────────────────────────────────────────────────────────
def render_register_view():
    load_login_bg_css()
    render_centered_header("PATIENT REGISTRATION")
    
    st.markdown("<div style='text-align:center; color:#a5b4fc; margin-bottom: 25px;'>Register as a new patient to access our healthcare services.</div>", unsafe_allow_html=True)

    # Only Patients can register. Doctors/Admins must be created by Admin.
    selected_role = "Patient"

    name     = st.text_input("Full Name",      placeholder=PLACEHOLDERS[selected_role]["name"],       key="reg_name")
    email    = st.text_input("Email Address",  placeholder=PLACEHOLDERS[selected_role]["email"],      key="reg_email")
    password = st.text_input("Password",       type="password",
                              placeholder=PLACEHOLDERS[selected_role]["password"],                    key="reg_password")
    gender   = st.selectbox("Gender",          ["Male", "Female", "Other"],                           key="reg_gender")
    phone    = st.text_input("Phone Number",   placeholder=PLACEHOLDERS[selected_role]["phone"],      key="reg_phone")

    # DOB — only for Patient and Doctor
    dob = None
    if selected_role != "Admin":
        max_dob = datetime.date.today() - datetime.timedelta(days=365)  # at least 1 year old
        dob = st.date_input(
            "Date of Birth",
            value=None,
            min_value=datetime.date(1900, 1, 1),
            max_value=max_dob,
            key="reg_dob",
            help="Required for Patient and Doctor accounts."
        )
        if dob:
            age_preview = _calculate_age(dob)
            st.caption(f"🎂 Age: **{age_preview} years**")

    if st.button("📋 Create Account", key="reg_btn", use_container_width=True):
        if not name.strip():
            st.error("Full Name is required.")
        elif not email.strip():
            st.error("Email Address is required.")
        elif not password.strip():
            st.error("Password is required.")
        elif len(password) < 6:
            st.warning("Password must be at least 6 characters long.")
        elif selected_role != "Admin" and dob is None:
            st.error("Date of Birth is required for Patient and Doctor accounts.")
        else:
            db = SessionLocal()
            try:
                register_user(db, name, email, password, selected_role, gender, phone, dob)
                st.success(
                    f"✅ Account created as **{selected_role}**! "
                    "Please go to Sign In to log in."
                )
            except ValueError as ve:
                st.error(str(ve))
            except Exception as e:
                st.error(f"Database error during registration: {e}")
            finally:
                db.close()
