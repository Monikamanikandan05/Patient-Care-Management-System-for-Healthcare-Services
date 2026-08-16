import os
import re
import streamlit as st
import streamlit.components.v1 as components
import json
from core.database import SessionLocal
from models.models import ChatMessage, Doctor, User, Specialty, OCRDocument, PharmacyMedicine
from services.ocr_service import process_document
from ai.smartcare_agent import ask
from ai.booking_flow import render_booking_wizard
from ai.chatbot_flows import (
    render_appointment_flow, render_pharmacy_flow,
    start_appointment_flow, start_pharmacy_flow,
    is_appointment_flow_active, is_pharmacy_flow_active,
    APPT_STEP_KEY, PHARMA_STEP_KEY,
)

# ── Register the custom voice-input component ──────────────────────────────────
_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "voice_input_component")
_voice_input = components.declare_component("voice_chat_input", path=_COMPONENT_DIR)

# ── Supported languages ────────────────────────────────────────────────────────
LANG_MAP = {
    "English":           "en-US",
    "Tamil (தமிழ்)":     "ta-IN",
    "Hindi (हिन्दी)":    "hi-IN",
    "Telugu (తెలుగు)":   "te-IN",
    "Kannada (ಕನ್ನಡ)":   "kn-IN",
    "Malayalam (മലയാളം)":"ml-IN",
}

# ── Quick-reply suggestion sets (keyed by trigger keyword) ─────────────────────
QUICK_REPLY_SETS = {
    "feeling": {
        "en-US": ["😊 Good","🤒 Sick","😔 Tired","😣 Pain","🤧 Cold/Cough","🤢 Nausea","😰 Anxious"],
        "ta-IN": ["😊 நலமாக","🤒 உடல் சரியில்லை","😔 சோர்வாக","😣 வலி","🤧 சளி/இருமல்","🤢 குமட்டல்"],
        "hi-IN": ["😊 अच्छा","🤒 बीमार","😔 थका हुआ","😣 दर्द","🤧 सर्दी","🤢 जी मिचलाना"],
        "te-IN": ["😊 బాగున్నాను","🤒 జబ్బు","😔 అలసట","😣 నొప్పి","🤧 జలుబు","🤢 వికారం"],
        "kn-IN": ["😊 ಚೆನ್ನಾಗಿದ್ದೇನೆ","🤒 ಅಸ್ವಸ್ಥ","😔 ದಣಿದಿದ್ದೇನೆ","😣 ನೋವು","🤧 ಶೀತ","🤢 ವಾಕರಿಕೆ"],
        "ml-IN": ["😊 സുഖം","🤒 അസ്വസ്ഥത","😔 ക്ഷീണം","😣 വേദന","🤧 ജലദോഷം","🤢 ഓക്കാനം"],
    },
    "location": {
        "en-US": ["Head","Chest","Stomach","Back","Leg","Hand","Throat","Neck","Other"],
        "ta-IN": ["தலை","நெஞ்சு","வயிறு","முதுகு","கால்","கை","தொண்டை","கழுத்து","மற்றவை"],
        "hi-IN": ["सिर","सीना","पेट","पीठ","पैर","हाथ","गला","गर्दन","अन्य"],
        "te-IN": ["తల","ఛాతీ","కడుపు","వీపు","కాలు","చెయ్యి","గొంతు","మెడ","ఇతర"],
        "kn-IN": ["ತಲೆ","ಎದೆ","ಹೊಟ್ಟೆ","ಬೆನ್ನು","ಕಾಲು","ಕೈ","ಗಂಟಲು","ಕೊರಳು","ಇತರ"],
        "ml-IN": ["തല","നെഞ്ച്","വയർ","മുതുക്","കാൽ","കൈ","തൊണ്ട","കഴുത്ത്","മറ്റ്"],
    },
    "pain_scale": {
        "en-US": ["1 (Mild)","2","3","4","5 (Moderate)","6","7","8","9","10 (Severe)"],
        "ta-IN": ["1 (மிகவும் குறைவு)","2","3","4","5 (மிதமான)","6","7","8","9","10 (மிகவும் அதிகம்)"],
        "hi-IN": ["1 (हल्का)","2","3","4","5 (मध्यम)","6","7","8","9","10 (बहुत तेज)"],
        "te-IN": ["1 (తేలికగా)","2","3","4","5 (మధ్యస్తంగా)","6","7","8","9","10 (తీవ్రంగా)"],
        "kn-IN": ["1 (ಸ್ವಲ್ಪ)","2","3","4","5 (ಮಧ್ಯಮ)","6","7","8","9","10 (ತೀವ್ರ)"],
        "ml-IN": ["1 (ചെറിയ)","2","3","4","5 (മിതമായ)","6","7","8","9","10 (കഠിനമായ)"],
    },
    "duration": {
        "en-US": ["Just now","Few hours","Since yesterday","2-3 days","A week","More than a week"],
        "ta-IN": ["இப்போதுதான்","சில மணி நேரம்","நேற்று முதல்","2-3 நாட்கள்","ஒரு வாரம்","ஒரு வாரத்திற்கும் மேல்"],
        "hi-IN": ["अभी-अभी","कुछ घंटे","कल से","2-3 दिन","एक हफ्ते से","एक हफ्ते से ज्यादा"],
        "te-IN": ["இప్పుడే","కొన్ని గంటలు","నిన్న నుండి","2-3 రోజులు","ఒక వారం","ఒక వారంకన్నా ఎక్కువ"],
        "kn-IN": ["ಈಗ ತಾನೆ","ಕೆಲವು ಗಂಟೆಗಳಿಂದ","ನಿನ್ನೆಯಿಂದ","2-3 ದಿನ","ಒಂದು ವಾರ","ಒಂದು ವಾರಕ್ಕೂ ಹೆಚ್ಚು"],
        "ml-IN": ["ഇപ്പോൾ","ചില മണിക്കൂർ","ഇന്നലെ മുതൽ","2-3 ദിവസം","ഒരാഴ്ച","ഒരാഴ്ചയിൽ കൂടുതൽ"],
    },
    "yesno": {
        "en-US": ["✅ Yes","❌ No","🤔 Not Sure"],
        "ta-IN": ["✅ ஆம்","❌ இல்லை","🤔 தெரியவில்லை"],
        "hi-IN": ["✅ हाँ","❌ नहीं","🤔 पता नहीं"],
        "te-IN": ["✅ అవును","❌ లేదు","🤔 తెలియదు"],
        "kn-IN": ["✅ ಹೌದು","❌ இல்லை","🤔 ಗೊತ್ತಿಲ್ಲ"],
        "ml-IN": ["✅ அതെ","❌ ഇല്ല","🤔 അറിയില്ല"],
    },
}


def _strip_markdown(text: str) -> str:
    """Remove markdown and symbols so TTS reads naturally."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*",     r"\1", text)
    text = re.sub(r"`(.*?)`",       r"\1", text)
    text = re.sub(r"#+\s*",         "",    text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    
    # Replace slashes with spaces so TTS doesn't say "slash"
    text = text.replace("/", " ")
    
    # Remove bullet dashes and asterisks
    text = re.sub(r"[-•*]\s+", " ", text)
    
    # Remove all emojis and obscure symbols, leaving only words, spaces, and basic punctuation
    text = re.sub(r"[^\w\s.,;:!?()'\"$₹€£%&@+-]", " ", text)
    
    # Collapse multiple spaces and clean up
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_text_for_lang(text: str, lang_code: str) -> str:
    """When a non-English voice is active, strip ASCII-only English words so the
    browser TTS engine doesn't fall back to English mid-sentence."""
    cleaned = _strip_markdown(text)
    if lang_code.startswith("en"):
        return cleaned
    import re
    # Remove standalone ASCII alphabet words (keeps numbers and native-script chars)
    cleaned = re.sub(r'\b[a-zA-Z][a-zA-Z0-9_\-]*[a-zA-Z0-9]+\b', ' ', cleaned)
    cleaned = re.sub(r'\b[a-zA-Z]\b', ' ', cleaned)  # single letters
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # If almost nothing native-script remains, fall back to full stripped text
    import unicodedata
    native_chars = sum(1 for c in cleaned if ord(c) > 127)
    if native_chars < 3:
        return _strip_markdown(text)
    return cleaned


def _detect_lang_code(text: str, preferred_lang: str = "English") -> str:
    """Return BCP-47 code for TTS, auto-detecting script when preferred is English."""
    code = LANG_MAP.get(preferred_lang, "en-US")
    if preferred_lang != "English":
        return code
    if re.search(r"[\u0B80-\u0BFF]", text): return "ta-IN"
    if re.search(r"[\u0900-\u097F]", text): return "hi-IN"
    if re.search(r"[\u0D00-\u0D7F]", text): return "ml-IN"
    if re.search(r"[\u0C00-\u0C7F]", text): return "te-IN"
    if re.search(r"[\u0C80-\u0CFF]", text): return "kn-IN"
    return "en-US"


def _detect_quick_reply_set(ai_text: str) -> str | None:
    """Return the quick-reply set key that best matches the last AI question."""
    t = ai_text.lower()
    if any(k in t for k in ["select a doctor", "which doctor", "choose a doctor", "available doctor", "list of doctor", "doctor credentials", "book an appointment with", "மருத்துவர்", "डॉक्टर", "డాక్టర్", "ഡോക്ടർ"]):
        return "doctor"
    if any(k in t for k in ["select a time", "choose a slot", "what time", "which slot", "appointment date", "time slot", "நேரம்", "समय", "సమయం", "<ctrl42>సమಯ"]):
        return "slot"
    if any(k in t for k in ["reason for appointment", "purpose of visit", "why are you visiting", "reason for visit", "காரணம்", "कारण", "<ctrl42>కారణం"]):
        return "reason"
    if any(k in t for k in ["feeling today","how are you","how do you feel","உணர்கிறீர்","महसूस","ఎలా ఉన్నారు","<ctrl42>സുഖം"]):
        return "feeling"
    if any(k in t for k in ["where is","location","point","located","எங்கு","कहाँ","<ctrl42>ఎక్కడ","<ctrl42><ctrl42>","<ctrl42>എവിടെ","pain located","வலி எங்கு"]):
        return "location"
    if any(k in t for k in ["scale of","1 to 10","pain level","rate your","severity","வலி அளவு","दर्द का स्तर","నొప్పి స్థాయి","<ctrl42>ಮಟ್ಟ","<ctrl42>തീവ്രത"]):
        return "pain_scale"
    if any(k in t for k in ["how long","when did","started","begin","எப்போது","कब से","<ctrl42>ఎప్పటి","<ctrl42>ಯಾವಾಗ","<ctrl42><ctrl42>","duration"]):
        return "duration"
    if any(k in t for k in ["do you have","are you","have you","did you","experiencing","உள்ளதா","क्या आपको","<ctrl42>ఉందా","இதேயே","<ctrl42>உண்டோ"]):
        return "yesno"
    return None


def _tts_js(text: str, lang_code: str, rate: float = 0.92, pitch: float = 1.1) -> str:
    """Return the JavaScript snippet for auto-speaking text with a sweet female voice."""
    # Use language-aware cleaning before passing to TTS
    cleaned_for_lang = _clean_text_for_lang(text, lang_code)
    safe = cleaned_for_lang.replace("`","'").replace('"',"'").replace("\n"," ")[:1400]
    return f"""
    (function(){{
      if (!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance("{safe}");
      u.lang  = "{lang_code}";
      u.rate  = {rate};
      u.pitch = {pitch};
      function findVoice(voices) {{
        var prefix = "{lang_code}".split('-')[0];
        var normLang = "{lang_code}".replace('_','-').toLowerCase();
        var isMaleFn = function(n) {{ return /\\bmale\\b|\\bdavid\\b|\\bmark\\b|\\bgeorge\\b|\\bravi\\b|\\bbrian\\b|\\bguy\\b/.test(n); }};
        return voices.find(function(v) {{
          var n=v.name.toLowerCase(); var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl===normLang&&/female|siri|zira|samantha|victoria|heera|raveena|hazel|karen|natural/.test(n);
        }})||voices.find(function(v) {{
          var n=v.name.toLowerCase(); var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl.startsWith(prefix)&&/female|siri|zira|samantha|victoria|heera|raveena|hazel|karen|natural/.test(n);
        }})||voices.find(function(v) {{
          var n=v.name.toLowerCase(); var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl===normLang;
        }})||voices.find(function(v) {{
          var n=v.name.toLowerCase(); var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl.startsWith(prefix);
        }})||voices.find(function(v) {{
          var vl=v.lang.replace('_','-').toLowerCase();
          return vl===normLang||vl.startsWith(prefix);
        }});
      }}
      function speak() {{
        var voices = window.speechSynthesis.getVoices();
        var match = findVoice(voices);
        if (match) {{ u.voice = match; u.lang = match.lang; }}
        window.speechSynthesis.speak(u);
      }}
      if (window.speechSynthesis.getVoices().length > 0) speak();
      else {{ window.speechSynthesis.onvoiceschanged = speak; setTimeout(speak, 300); }}
    }})();
    """


def _render_tts_autoplay(text: str, lang_code: str, rate: float = 0.92, pitch: float = 1.1):
    """Inject TTS auto-play script (fires once per response)."""
    components.html(f"<script>{_tts_js(text, lang_code, rate, pitch)}</script>", height=0)


def _render_speaking_indicator(lang_code: str):
    """Animated speaking waveform indicator."""
    components.html("""
    <div id="speaking_anim" style="display:flex;align-items:center;gap:4px;margin:4px 0 8px 0;">
      <span style="color:#a78bfa;font-size:12px;margin-right:6px;">🔊 AI Speaking Response Aloud…</span>
      """ + "".join([f'<div style="width:4px;height:{h}px;background:#8b5cf6;border-radius:4px;animation:wave 0.8s ease-in-out {d}s infinite alternate;"></div>'
                     for h,d in [(12,0),(20,0.1),(28,0.2),(20,0.3),(12,0.4)]]) + """
    </div>
    <style>
      @keyframes wave {from{transform:scaleY(0.4)}to{transform:scaleY(1)}}
    </style>
    """, height=36)


def _render_doctor_cards(db):
    """Render interactive click cards for Doctor Selection."""
    docs = db.query(Doctor).join(User, Doctor.user_id == User.id).all()
    if not docs:
        st.info("No doctor profiles currently listed.")
        return

    st.markdown("<div style='margin:10px 0 6px;'><b style='color:#a5b4fc;font-size:13px;'>👨‍⚕️ Click a Doctor to Book / Consult:</b></div>", unsafe_allow_html=True)
    cols = st.columns(min(len(docs), 3))
    for i, d in enumerate(docs):
        doc_name = f"Dr. {d.user.full_name}" if d.user else "Doctor"
        spec_name = d.specialty.name if d.specialty else "General"
        fee = int(d.consultation_fee or 0)
        btn_label = f"🩺 {doc_name}\n({spec_name} • ₹{fee})"
        col = cols[i % 3]
        btn_key = f"doc_btn_{d.id}_{st.session_state.get('_qr_generation', 0)}"
        if col.button(btn_label, key=btn_key, use_container_width=True, type="primary"):
            st.session_state["_quick_reply_value"] = f"I select {doc_name} ({spec_name}) for my appointment"
            st.rerun()


def _render_slot_cards():
    """Render interactive click buttons for Time Slots."""
    slots = [
        "📅 Today at 10:00 AM",
        "📅 Today at 02:30 PM",
        "📅 Tomorrow at 11:00 AM",
        "📅 Tomorrow at 04:00 PM",
        "📅 Day After Tomorrow at 10:30 AM"
    ]
    st.markdown("<div style='margin:10px 0 6px;'><b style='color:#a5b4fc;font-size:13px;'>⏰ Click an Available Time Slot:</b></div>", unsafe_allow_html=True)
    cols = st.columns(min(len(slots), 3))
    for i, slot_str in enumerate(slots):
        col = cols[i % 3]
        btn_key = f"slot_btn_{i}_{st.session_state.get('_qr_generation', 0)}"
        if col.button(slot_str, key=btn_key, use_container_width=True):
            st.session_state["_quick_reply_value"] = f"I select the time slot: {slot_str}"
            st.rerun()


def _render_reason_cards():
    """Render interactive click buttons for Appointment Reasons."""
    reasons = [
        "🩺 Routine Health Checkup",
        "💔 Cardiac Consultation",
        "💊 Prescription Renewal",
        "🧪 Lab Test Follow-up",
        "🤒 Symptom Consultation"
    ]
    st.markdown("<div style='margin:10px 0 6px;'><b style='color:#a5b4fc;font-size:13px;'>📋 Click Reason for Appointment:</b></div>", unsafe_allow_html=True)
    cols = st.columns(min(len(reasons), 3))
    for i, reason_str in enumerate(reasons):
        col = cols[i % 3]
        btn_key = f"reason_btn_{i}_{st.session_state.get('_qr_generation', 0)}"
        if col.button(reason_str, key=btn_key, use_container_width=True):
            st.session_state["_quick_reply_value"] = f"Reason for my visit: {reason_str}"
            st.rerun()


def _render_quick_replies(set_key: str, lang_code: str, db=None):
    """Render dynamic quick-reply options / cards based on set_key."""
    if set_key == "doctor" and db is not None:
        _render_doctor_cards(db)
        return
    elif set_key == "slot":
        _render_slot_cards()
        return
    elif set_key == "reason":
        _render_reason_cards()
        return

    lang = lang_code if lang_code in QUICK_REPLY_SETS.get(set_key, {}) else "en-US"
    buttons = QUICK_REPLY_SETS.get(set_key, {}).get(lang, [])
    if not buttons:
        return

    cols_per_row = 5 if set_key == "pain_scale" else 4
    cols = st.columns(min(len(buttons), cols_per_row))
    for i, btn_text in enumerate(buttons):
        col = cols[i % cols_per_row]
        btn_key = f"qr_{set_key}_{i}_{st.session_state.get('_qr_generation', 0)}"
        if col.button(btn_text, key=btn_key, use_container_width=True):
            st.session_state["_quick_reply_value"] = btn_text
            st.rerun()


def _render_per_msg_listen_btn(text: str, msg_id: int, lang_code: str, rate: float, pitch: float):
    """Inline listen/stop button per assistant message."""
    # Use language-aware cleaning before TTS
    cleaned_for_lang = _clean_text_for_lang(text, lang_code)
    safe = cleaned_for_lang.replace("`","'").replace('"',"'").replace("\n"," ")[:1400]
    bid = f"spk_{msg_id}"
    sid = f"stp_{msg_id}"
    components.html(f"""
    <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
      <button id="{bid}" onclick="(function(){{
        window.speechSynthesis.cancel();
        var u=new SpeechSynthesisUtterance('{safe}');
        u.lang='{lang_code}'; u.rate={rate}; u.pitch={pitch};
        var voices=window.speechSynthesis.getVoices();
        var prefix='{lang_code}'.split('-')[0];
        var normLang='{lang_code}'.replace('_','-').toLowerCase();
        var isMaleFn=function(n){{return /\\bmale\\b|\\bdavid\\b|\\bmark\\b|\\bgeorge\\b|\\bravi\\b|\\bbrian\\b|\\bguy\\b/.test(n);}};
        var m=voices.find(function(v){{
          var n=v.name.toLowerCase();var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl===normLang&&/female|siri|zira|samantha|victoria|heera|raveena|hazel|karen|natural/.test(n);
        }})||voices.find(function(v){{
          var n=v.name.toLowerCase();var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl.startsWith(prefix)&&/female|siri|zira|samantha|victoria|heera|raveena|hazel|karen|natural/.test(n);
        }})||voices.find(function(v){{
          var n=v.name.toLowerCase();var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl===normLang;
        }})||voices.find(function(v){{
          var n=v.name.toLowerCase();var vl=v.lang.replace('_','-').toLowerCase();
          return !isMaleFn(n)&&vl.startsWith(prefix);
        }})||voices.find(function(v){{
          var vl=v.lang.replace('_','-').toLowerCase();
          return vl===normLang||vl.startsWith(prefix);
        }});
        if(m){{u.voice=m;u.lang=m.lang;}}
        u.onstart=function(){{document.getElementById('{bid}').style.display='none';document.getElementById('{sid}').style.display='inline-flex';}};
        u.onend=u.onerror=function(){{document.getElementById('{bid}').style.display='inline-flex';document.getElementById('{sid}').style.display='none';}};
        window.speechSynthesis.speak(u);
      }})()" style="background:#1e1b4b;border:1px solid #4338ca;color:#c7d2fe;padding:3px 12px;border-radius:14px;font-size:11.5px;cursor:pointer;display:inline-flex;align-items:center;gap:5px;">
        🔊 Listen Aloud
      </button>
      <button id="{sid}" onclick="window.speechSynthesis.cancel();this.style.display='none';document.getElementById('{bid}').style.display='inline-flex';"
        style="background:#450a0a;border:1px solid #dc2626;color:#fca5a5;padding:3px 10px;border-radius:14px;font-size:11.5px;cursor:pointer;display:none;align-items:center;gap:4px;">
        ⏹ Stop Voice
      </button>
    </div>""", height=32)


def _welcome_msg_for_lang(full_name: str, lang: str, role: str = "Patient") -> str:
    first = full_name.split()[0] if full_name else "there"
    
    if role == "Admin":
        assistant_name = "Admin's AI Assistant"
        prompt_en = "How can I assist you with managing the system today?"
        prompt_ta = "இன்று கணினியை நிர்வகிக்க நான் உங்களுக்கு எப்படி உதவ முடியும்?"
        prompt_hi = "आज सिस्टम को प्रबंधित करने में मैं आपकी कैसे मदद कर सकता हूँ?"
        prompt_te = "ఈ రోజు సిస్టమ్‌ని నిర్వహించడంలో నేను మీకు ఎలా సహాయపడగలను?"
        prompt_ka = "ಇಂದು ಸಿಸ್ಟಮ್ ನಿರ್ವಹಿಸಲು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
        prompt_ml = "ഇന്ന് സിസ്റ്റം കൈകാര്യം ചെയ്യാൻ ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കും?"
    elif role == "Doctor":
        assistant_name = "Doctor's AI Assistant"
        prompt_en = "How can I assist you with your patients and schedule today?"
        prompt_ta = "இன்று உங்கள் நோயாளிகள் மற்றும் அட்டவணைக்கு நான் உங்களுக்கு எப்படி உதவ முடியும்?"
        prompt_hi = "आज आपके मरीजों और शेड्यूल में मैं आपकी कैसे मदद कर सकता हूँ?"
        prompt_te = "ఈ రోజు మీ రోగులు మరియు షెడ్యూల్‌తో నేను మీకు ఎలా సహాయపడగలను?"
        prompt_ka = "ಇಂದು ನಿಮ್ಮ ರೋಗಿಗಳು ಮತ್ತು ವೇಳಾಪಟ್ಟಿಯೊಂದಿಗೆ ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
        prompt_ml = "ഇന്ന് നിങ്ങളുടെ രോഗികളുമായും ഷെഡ്യൂളുമായും ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കും?"
    else:
        assistant_name = "AI Health Assistant"
        prompt_en = "How are you feeling today?"
        prompt_ta = "இன்று நீங்கள் எப்படி உணர்கிறீர்கள்?"
        prompt_hi = "आज आप कैसा महसूस कर रहे हैं?"
        prompt_te = "ఈరోజు మీరు ఎలా ఉన్నారు?"
        prompt_ka = "ಇಂದು ನೀವು ಹೇಗಿದ್ದೀರ?"
        prompt_ml = "ഇന്ന് നിങ്ങൾക്ക് എങ്ങനെ തോന്നുന്നു?"

    msgs = {
        "English":            f"Hello {first}! 😊 I'm your **SMART CARE** {assistant_name}. I'm here to help you.\n\n{prompt_en}",
        "Tamil (தமிழ்)":     f"வணக்கம் {first}! 😊 நான் உங்கள் **SMART CARE** {assistant_name}. நான் உங்களுக்கு உதவுவேன்.\n\n{prompt_ta}",
        "Hindi (हिन्दी)":    f"नमस्ते {first}! 😊 मैं आपका **SMART CARE** {assistant_name} हूँ। मैं आपकी मदद के लिए यहाँ हूँ।\n\n{prompt_hi}",
        "Telugu (తెలుగు)":   f"నమస్కారం {first}! 😊 నేను మీ **SMART CARE** {assistant_name}. మీకు సహాయం చేయడానికి ఇక్కడ ఉన్నాను.\n\n{prompt_te}",
        "Kannada (ಕನ್ನಡ)":   f"ನಮಸ್ಕಾರ {first}! 😊 ನಾನು ನಿಮ್ಮ **SMART CARE** {assistant_name}. ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಇಲ್ಲಿದ್ದೇನೆ.\n\n{prompt_ka}",
        "Malayalam (മലയാളം)": f"നമസ്കാരം {first}! 😊 ഞാൻ നിങ്ങളുടെ **SMART CARE** {assistant_name} ആണ്. നിങ്ങളെ സഹായിക്കാൻ ഇവിടെ ഉണ്ട്.\n\n{prompt_ml}",
    }
    return msgs.get(lang, msgs["English"])

UPLOAD_DIR = "assets/uploads/ocr"

def _handle_chatbot_document_upload(file_obj, user, db, selected_lang):
    """Processes document/image upload directly inside the chatbot interface.
    Instantly verifies and describes what is in the image and its medical uses.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{user['id']}_{file_obj.name}")

    with open(file_path, "wb") as f:
        f.write(file_obj.getbuffer())

    try:
        with st.spinner("🤖 AI Vision is verifying and reading your image/document…"):
            from services.ocr_service import analyse_image_with_groq, extract_text_with_paddle
            paddle_text, _ = extract_text_with_paddle(file_path)
            data = analyse_image_with_groq(file_path)

        description = (data.get("description") or "").strip()
        tablet_info = data.get("tabletInfo", {}) or {}
        report_info = data.get("reportInfo", {}) or {}
        full_text = paddle_text or (data.get("fullExtractedText") or "").strip()
        file_clean = file_obj.name.replace(".png","").replace(".jpg","").replace(".jpeg","").replace(".webp","").replace(".pdf","").replace("_"," ")

        # Active pharmacy medicines in clinic
        pharma_meds = db.query(PharmacyMedicine).filter(PharmacyMedicine.is_active == True).all()

        user_msg = f"📸 **Uploaded Image / Document:** `{file_obj.name}`"

        # Check if medication / tablet
        is_med = (
            any(w in file_clean.lower() for w in ["atorvastatin", "paracetamol", "tablet", "pill", "capsule", "mg", "medicine", "medication", "lisinopril", "metformin", "amoxicillin", "aspirin", "ibuprofen"])
            or any(w in description.lower() for w in ["tablet", "pill", "capsule", "atorvastatin", "paracetamol", "mg", "medication", "medicine"])
            or bool(tablet_info.get("name"))
        )

        if is_med:
            t_name = tablet_info.get("name") or file_clean
            t_strength = tablet_info.get("strength") or ("20 mg" if "atorvastatin" in t_name.lower() else "500 mg")
            t_uses = tablet_info.get("uses")
            t_how = tablet_info.get("howToUse")
            t_purpose = tablet_info.get("purpose")
            t_side = tablet_info.get("sideEffects")

            # Knowledge defaults for common medicines if vision description is brief
            if "atorvastatin" in t_name.lower():
                t_name = "Atorvastatin (20 mg)"
                if not t_uses or "complete" in t_uses.lower():
                    t_uses = "Lowers bad cholesterol (LDL) and triglycerides in the blood while increasing good cholesterol (HDL)."
                if not t_purpose:
                    t_purpose = "Used for hyperlipidemia management, preventing cardiovascular disease, and reducing the risk of heart attack or stroke."
                if not t_how:
                    t_how = "Take 1 tablet (20 mg) orally once daily at bedtime, with or without food."
                if not t_side:
                    t_side = "Common side effects include mild muscle ache/pain, headache, nausea, and mild digestive discomfort."
            elif "paracetamol" in t_name.lower():
                t_name = "Paracetamol (500 mg)"
                if not t_uses or "complete" in t_uses.lower():
                    t_uses = "Effective pain reliever (analgesic) and fever reducer (antipyretic)."
                if not t_purpose:
                    t_purpose = "Relieving fever, headache, body aches, toothache, and mild discomfort."
                if not t_how:
                    t_how = "Take 1 tablet every 4 to 6 hours as needed with water. Do not exceed 4000 mg in 24 hours."

            if not t_uses:
                t_uses = "Therapeutic symptom management, infection control, or clinical health maintenance."
            if not t_how:
                t_how = "Take orally with water as directed by your treating physician."

            # Check pharmacy stock
            pharma_match = None
            search_terms = t_name.lower().split()
            for pm in pharma_meds:
                if any(term in pm.name.lower() or (pm.generic_name and term in pm.generic_name.lower()) for term in search_terms if len(term) > 3):
                    pharma_match = pm
                    break

            if pharma_match:
                pharma_status = (
                    f"- **Pharmacy Status:** Available in Our Clinic Pharmacy\n"
                    f"- **Product:** {pharma_match.name}\n"
                    f"- **Unit Price:** ₹{pharma_match.price} per {pharma_match.unit}\n"
                    f"- **Clinic Stock:** {pharma_match.stock_qty} units available"
                )
            else:
                pharma_status = "- **Pharmacy Status:** Not currently in stock in clinic pharmacy inventory."

            side_effects_line = f"- **Common Side Effects:** {t_side}\n" if t_side else ""

            assistant_msg = (
                f"💊 **Medication Verification & Analysis**\n\n"
                f"- **Medication Name:** {t_name}\n"
                f"- **Strength / Dosage:** {t_strength}\n"
                f"- **Primary Uses:** {t_uses}\n"
                f"- **Purpose / Condition:** {t_purpose or 'Therapeutic treatment and symptom management'}\n"
                f"- **How to Use:** {t_how}\n"
                f"{side_effects_line}\n"
                f"🏥 **Clinic Pharmacy Availability:**\n"
                f"{pharma_status}"
            )

        # ── CASE 2: Report / Medical Document ─────────────────────────────────
        else:
            r_summary = report_info.get("reportSummary") or description
            # Strip visual meta phrases if present
            r_summary = r_summary.replace("The image contains ", "").replace("This image shows ", "").replace("The document shows ", "")
            assistant_msg = (
                f"📄 **Medical Document Verification & Analysis**\n\n"
                f"- **Document Content Summary:** {r_summary}\n"
                f"- **Primary Uses:** Provides diagnostic evaluation, clinical findings, and treatment recommendations for patient care."
            )
            if full_text:
                assistant_msg += f"\n- **Extracted Text Snippet:** {full_text[:400].replace(chr(10), ' ')}"

        # Add both messages to chat history session state
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_msg})

        # Persist messages in database ChatMessage table
        db.add(ChatMessage(user_id=user["id"], role="user", content=user_msg))
        db.add(ChatMessage(user_id=user["id"], role="assistant", content=assistant_msg))
        db.commit()

        # NOTE: Do NOT auto-trigger TTS. Output is rendered silently.
        # User will click 🔊 Listen button on the message to hear description out loud.
        st.rerun()

    except Exception as e:
        st.error(f"Failed to process image/document in chatbot: {str(e)}")


def _clean_html_tags(text: str) -> str:
    """Sanitizes any residual raw HTML tags (<br>, <b>, etc.) into clean Markdown formatting."""
    if not text:
        return ""
    return (
        text.replace("<br>", "\n")
            .replace("<br/>", "\n")
            .replace("<br />", "\n")
            .replace("<b>", "**")
            .replace("</b>", "**")
    )

def render_chatbot_view():
    user = st.session_state.user
    role = user["role"] if user else "Patient"
    
    if role == "Admin":
        title_name = "Admin's AI Assistant"
    elif role == "Doctor":
        title_name = "Doctor's AI Assistant"
    else:
        title_name = "AI Health Assistant"
        
    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='text-align:center;margin-bottom:8px;'>
      <div style='font-size:2.2rem;'>🎙️</div>
      <h2 style='margin:0;font-size:1.4rem;background:linear-gradient(135deg,#a78bfa,#ec4899);
         -webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;'>
        {title_name}
      </h2>
      <p style='color:#64748b;font-size:0.82rem;margin:4px 0 0;'>
        Speak to AI • AI Speaks Back Aloud • Hands-Free Conversation
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Prominent Audio Voice Badge & Language Controls ───────────────────────
    st.markdown("""
    <div style="background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.4);
                border-radius: 12px; padding: 10px 16px; margin-bottom: 12px;
                display: flex; align-items: center; justify-content: space-between;">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:1.2rem;">🔊</span>
        <div>
          <b style="color:#c4b5fd; font-size:13px;">AI Voice Response: ACTIVE</b>
          <div style="color:#94a3b8; font-size:11px;">The AI speaks every response out loud in a sweet female voice.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    lang_cols = st.columns([2, 1])
    with lang_cols[0]:
        selected_lang = st.selectbox(
            "🌐 Choose your language",
            options=list(LANG_MAP.keys()),
            index=0,
            key="chat_preferred_language",
            help="The AI will speak and respond in this language."
        )
        
        # Dynamic Voice Availability Checker
        components.html(f"""
        <div id="voice-status" style="font-size:11.5px;color:#94a3b8;font-family:sans-serif;margin-top:2px;line-height:1.3;">
          Checking browser voice compatibility...
        </div>
        <script>
        (function() {{
          function checkVoice() {{
            var voices = window.speechSynthesis.getVoices();
            var langCode = "{LANG_MAP.get(selected_lang, 'en-US')}";
            var prefix = langCode.split('-')[0];
            
            var matchingVoices = voices.filter(function(v) {{
              var vlang = v.lang.replace('_', '-').toLowerCase();
              return vlang === langCode.toLowerCase() || vlang.startsWith(prefix.toLowerCase());
            }});
            
            var el = document.getElementById("voice-status");
            if (matchingVoices.length > 0) {{
              var voiceNames = matchingVoices.map(function(v) {{ return v.name; }}).join(", ");
              el.innerHTML = "🟢 Your browser supports <b>{selected_lang}</b> voice output!<br><span style='font-size:10.5px;opacity:0.8;'>Available: " + voiceNames + "</span>";
              el.style.color = "#10b981";
            }} else {{
              el.innerHTML = "🔴 <b>Warning:</b> No <b>{selected_lang}</b> voice found in your browser/OS. AI speech will fall back to English. Try installing the Tamil voice pack or use Chrome/Edge.";
              el.style.color = "#ef4444";
            }}
          }}
          if (window.speechSynthesis.getVoices().length > 0) {{
            checkVoice();
          }} else {{
            window.speechSynthesis.onvoiceschanged = checkVoice;
          }}
        }})();
        </script>
        """, height=38)


    with lang_cols[1]:
        speaker_on = st.toggle("🔊 Auto-speak responses", value=False, key="tts_toggle")

    lang_code = LANG_MAP.get(selected_lang, "en-US")

    # ── Sidebar — Voice Tuning & Actions ─────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        with st.expander("⚙️ Voice Tuning", expanded=False):
            tts_rate  = st.slider("⚡ Speech Speed",  min_value=0.7, max_value=1.4, value=1.0, step=0.05, key="tts_rate_slider")
            tts_pitch = st.slider("🎼 Voice Pitch",   min_value=0.8, max_value=1.3, value=1.0, step=0.05, key="tts_pitch_slider")

        if st.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
            with SessionLocal() as s:
                s.query(ChatMessage).filter(ChatMessage.user_id == st.session_state.user["id"]).delete()
                s.commit()
            if "chat_history" in st.session_state:
                del st.session_state["chat_history"]
            st.rerun()

    if "show_booking_wizard" not in st.session_state:
        st.session_state.show_booking_wizard = False

    if "_qr_generation" not in st.session_state:
        st.session_state["_qr_generation"] = 0

    user = st.session_state.user
    db = SessionLocal()

    try:
        # ── Load / initialise chat history ──────────────────────────────────────
        lang_changed = st.session_state.get("_chat_lang") != selected_lang
        if "chat_history" not in st.session_state or lang_changed:
            st.session_state["_chat_lang"] = selected_lang
            db_msgs = db.query(ChatMessage).filter(
                ChatMessage.user_id == user["id"]
            ).order_by(ChatMessage.created_at.asc()).all()
            st.session_state.chat_history = [
                {"role": m.role, "content": m.content} for m in db_msgs
            ]

            if not st.session_state.chat_history:
                welcome_msg = _welcome_msg_for_lang(user.get("full_name", ""), selected_lang, user.get("role", "Patient"))
                st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
                db.add(ChatMessage(user_id=user["id"], role="assistant", content=welcome_msg))
                db.commit()
            elif lang_changed:
                # Language changed mid-session: swap the first (welcome) message to the new language
                new_welcome = _welcome_msg_for_lang(user.get("full_name", ""), selected_lang, user.get("role", "Patient"))
                st.session_state.chat_history[0] = {"role": "assistant", "content": new_welcome}

        # ── Check if there is a newly generated AI message to auto-speak ───────
        msg_to_speak = st.session_state.pop("_msg_to_speak", None)
        if msg_to_speak and speaker_on:
            _render_speaking_indicator(msg_to_speak["lang"])
            # TTS is handled inside the _voice_input component to enable the continuous mic loop.

        # ── Handle new prompts from previous run ────────────────────────────────
        prompt_val = st.session_state.get("_pending_prompt")
        if prompt_val:
            st.session_state["_pending_prompt"] = None
            
            with st.chat_message("user"):
                st.markdown(prompt_val)

            st.session_state.chat_history.append({"role": "user", "content": prompt_val})
            db.add(ChatMessage(user_id=user["id"], role="user", content=prompt_val))
            db.commit()

            with st.chat_message("assistant"):
                with st.spinner("💭 AI is processing…"):
                    response_text, signals = ask(
                        user,
                        prompt_val,
                        st.session_state.chat_history[:-1],
                        target_language=selected_lang
                    )
                st.markdown(response_text)

            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            db.add(ChatMessage(user_id=user["id"], role="assistant", content=response_text))
            db.commit()

            # Detect booking intent → start guided appointment flow
            if signals.get("start_booking") or "booking wizard" in response_text.lower():
                start_appointment_flow()
                st.rerun()

            # Detect pharmacy order intent from user prompt
            _prompt_lower = prompt_val.lower()
            _pharma_order_kw = ["order medicine", "buy medicine", "order tablet", "buy tablet",
                                "order from pharmacy", "place order", "i want to order",
                                "medicine order", "மருந்து வாங்க", "மருந்து ஆர்டர்",
                                "दवा ऑर्डर", "दवा खरीदना"]
            if any(kw in _prompt_lower for kw in _pharma_order_kw):
                start_pharmacy_flow()
                st.rerun()

            if signals.get("generate_report") and signals.get("report_pdf_bytes"):
                st.session_state["chat_report_pdf_bytes"] = signals["report_pdf_bytes"]
                st.session_state["chat_report_filename"] = signals.get("report_filename", "IPCMS_AI_Health_Report.pdf")
        # ── Render chat history ─────────────────────────────────────────────────
        for idx, msg in enumerate(st.session_state.chat_history):
            clean_text = _clean_html_tags(msg["content"])
            with st.chat_message(msg["role"]):
                st.markdown(clean_text)
                if msg["role"] == "assistant":
                    msg_lang = _detect_lang_code(clean_text, selected_lang)
                    _render_per_msg_listen_btn(
                        clean_text, idx, msg_lang,
                        st.session_state.get("tts_rate_slider", 0.92),
                        st.session_state.get("tts_pitch_slider", 1.1)
                    )

        # Find latest AI message & ID to pass to ChatGPT Voice Component
        latest_ai_msg = ""
        latest_msg_id = 0
        if st.session_state.chat_history:
            for idx in range(len(st.session_state.chat_history) - 1, -1, -1):
                m = st.session_state.chat_history[idx]
                if m["role"] == "assistant":
                    latest_ai_msg = m["content"]
                    latest_msg_id = idx + 1
                    break

        # ── Guided Step-by-Step Flows (Appointment & Pharmacy) ─────────────────
        if is_appointment_flow_active():
            render_appointment_flow(user)
        elif is_pharmacy_flow_active():
            render_pharmacy_flow(user)
        elif st.session_state.get("show_booking_wizard", False):
            render_booking_wizard(user)

        # ── Document & Image AI Upload inside Chatbot ─────────────────────────
        with st.expander("📷 Upload Medical Document / Prescription / Photo to AI Chatbot", expanded=False):
            st.markdown(
                "<div style='font-size:12px;color:#94a3b8;margin-bottom:8px;'>"
                "Upload a prescription, lab report, insurance card, or pill photo. "
                "AI will analyze it, summarize it directly in chat, and save it to your health record.</div>",
                unsafe_allow_html=True
            )
            up_col1, up_col2 = st.columns([1, 1])
            with up_col1:
                f_val = st.file_uploader(
                    "Upload Image/PDF",
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    key=f"chat_doc_file_{st.session_state._qr_generation}",
                    label_visibility="collapsed"
                )
                if f_val:
                    last_processed = st.session_state.get("_last_uploaded_file_key")
                    current_key = f"{f_val.name}_{f_val.size}"
                    if last_processed != current_key:
                        st.session_state["_last_uploaded_file_key"] = current_key
                        _handle_chatbot_document_upload(f_val, user, db, selected_lang)
            with up_col2:
                c_val = st.camera_input("Take Photo", key=f"chat_doc_cam_{st.session_state._qr_generation}")
                if c_val:
                    last_processed_cam = st.session_state.get("_last_cam_file_key")
                    current_cam_key = f"{c_val.name}_{c_val.size}"
                    if last_processed_cam != current_cam_key:
                        st.session_state["_last_cam_file_key"] = current_cam_key
                        _handle_chatbot_document_upload(c_val, user, db, selected_lang)

        last_ai = latest_ai_msg
        clicked_qr = None

        # ── Role-specific Quick Action Buttons ─────────────────────────────
        gen = st.session_state._qr_generation
        if role == "Admin":
            quick_action_cols = st.columns(4)
            if quick_action_cols[0].button("📊 Low Stock Medicines", key=f"act_a0_{gen}", use_container_width=True):
                clicked_qr = "Show me all low stock medicines in the pharmacy"
            if quick_action_cols[1].button("📅 Today's Appointments", key=f"act_a1_{gen}", use_container_width=True):
                clicked_qr = "Show all appointments scheduled for today"
            if quick_action_cols[2].button("👥 Patient Summary", key=f"act_a2_{gen}", use_container_width=True):
                clicked_qr = "Give me a summary of all registered patients and their status"
            if quick_action_cols[3].button("📊 Clinic Analytics", key=f"act_a3_{gen}", use_container_width=True):
                clicked_qr = "Show clinic analytics: total patients, doctors, appointments and revenue"
        elif role == "Doctor":
            quick_action_cols = st.columns(4)
            if quick_action_cols[0].button("📅 New Appointments", key=f"act_d0_{gen}", use_container_width=True):
                clicked_qr = "Show me my new and upcoming appointments"
            if quick_action_cols[1].button("🫀 My Patients", key=f"act_d1_{gen}", use_container_width=True):
                clicked_qr = "Show a list of my patients and their latest health status"
            if quick_action_cols[2].button("📝 Pending Prescriptions", key=f"act_d2_{gen}", use_container_width=True):
                clicked_qr = "Show me patients who still need prescriptions or follow-ups"
            if quick_action_cols[3].button("🧪 Lab Results", key=f"act_d3_{gen}", use_container_width=True):
                clicked_qr = "Show recent lab results and diagnostic reports for my patients"
        else:  # Patient
            quick_action_cols = st.columns(4)
            if quick_action_cols[0].button("📅 Book Appointment", key=f"act_p0_{gen}", use_container_width=True):
                start_appointment_flow()
                st.rerun()
            if quick_action_cols[1].button("💊 Order Medicine", key=f"act_p1_{gen}", use_container_width=True):
                start_pharmacy_flow()
                st.rerun()
            if quick_action_cols[2].button("📄 AI Health Report", key=f"act_p2_{gen}", use_container_width=True):
                clicked_qr = "Generate my AI health report for download"
            if quick_action_cols[3].button("📊 My Health Summary", key=f"act_p3_{gen}", use_container_width=True):
                clicked_qr = "Show my health summary and recent vitals"

        # ── Interactive click options only for Patient role ─────────────────────
        if role == "Patient":
            qr_key = _detect_quick_reply_set(last_ai)
            if qr_key:
                st.markdown("<div style='margin-top:6px;'><span style='color:#94a3b8;font-size:11px;'>💡 Quick Options:</span></div>", unsafe_allow_html=True)
                _render_quick_replies(qr_key, lang_code, db=db)

        # ── Auto-scroll to bottom ───────────────────────────────────────────────
        components.html("""<script>
          (function(){try{
            var p=window.parent.document;
            var msgs=p.querySelectorAll('[data-testid="stChatMessage"]');
            if(msgs.length>0){msgs[msgs.length-1].scrollIntoView({behavior:'instant',block:'end'});return;}
            var main=p.querySelector('section[data-testid="stMain"]')||p.querySelector('main');
            if(main)main.scrollTop=main.scrollHeight;
          }catch(e){}})()</script>""", height=1)

        # ── Standard Text Chat Input Box (renders as fixed bottom bar) ──────────
        typed_prompt = st.chat_input("Ask anything, @ to mention, / for actions")

        # ── Call Streamlit Voice Component (handles Web Speech permissions) ──
        _voice_input(
            key="voice_chat_input_component",
            ai_lang=lang_code,
            default=None
        )

        # ── Inject: Position Mic inside Chat Input + '+' OCR Button + Speech Text Handler ──
        components.html(f"""
        <script>
        (function() {{
            var doc = window.parent.document;

            // 1. Speech listener: puts recognized text from mic into textarea and updates React state
            if (!window.parent._sc_speech_listener) {{
                window.parent._sc_speech_listener = true;
                window.parent.addEventListener("message", function(e) {{
                    if (e.data && e.data.type === "SMARTCARE_SPEECH_TEXT") {{
                        var ta = doc.querySelector('[data-testid="stChatInput"] textarea');
                        if (ta) {{
                            var cur = ta.value.trim();
                            var newText = cur ? (cur + " " + e.data.text) : e.data.text;
                            try {{
                                var proto = Object.getPrototypeOf(ta);
                                var setter = Object.getOwnPropertyDescriptor(proto, "value")?.set ||
                                             Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, "value")?.set;
                                if (setter) {{
                                    setter.call(ta, newText);
                                }} else {{
                                    ta.value = newText;
                                }}
                            }} catch(err) {{
                                ta.value = newText;
                            }}
                            ta.dispatchEvent(new Event("input", {{ bubbles: true }}));
                            ta.dispatchEvent(new Event("change", {{ bubbles: true }}));
                            ta.focus();
                        }}
                    }}
                }});
            }}

            // 2. Continuous positioner to place +, text, mic, and send icon in a straight line
            var checkCount = 0;
            var posInterval = setInterval(function() {{
                checkCount++;
                if (checkCount > 80) clearInterval(posInterval);

                var chatBox = doc.querySelector('[data-testid="stChatInput"]');
                var voiceIframe = doc.querySelector('iframe[title*="voice_chat_input"]');

                if (chatBox) {{
                    chatBox.style.position = "relative";
                    chatBox.style.width = "100%";

                    var ta = chatBox.querySelector("textarea");
                    if (ta) {{
                        ta.style.paddingLeft   = "46px";
                        ta.style.paddingRight  = "86px";
                        ta.style.borderRadius  = "20px";
                    }}

                    // Inject '+' button on left with matching 32px circle
                    if (!chatBox.querySelector(".sc-plus-btn")) {{
                        var plusBtn = doc.createElement("button");
                        plusBtn.className = "sc-plus-btn";
                        plusBtn.title = "Upload Image / Document for OCR";
                        plusBtn.textContent = "+";
                        plusBtn.style.cssText = [
                            "position:absolute", "left:10px", "bottom:7px",
                            "width:32px", "height:32px", "min-width:32px", "min-height:32px",
                            "border-radius:50%", "border:none",
                            "background:rgba(255,255,255,0.08)", "color:#94a3b8",
                            "font-size:20px", "font-weight:400", "line-height:1",
                            "display:flex", "align-items:center", "justify-content:center",
                            "cursor:pointer", "z-index:9999", "transition:all 0.2s ease"
                        ].join(";");
                        plusBtn.onmouseover = function() {{ plusBtn.style.background = "rgba(255,255,255,0.16)"; plusBtn.style.color = "#f8fafc"; }};
                        plusBtn.onmouseout  = function() {{ plusBtn.style.background = "rgba(255,255,255,0.08)"; plusBtn.style.color = "#94a3b8"; }};
                        plusBtn.onclick = function(ev) {{
                            ev.preventDefault(); ev.stopPropagation();
                            var fi = doc.querySelector('[data-testid="stFileUploader"] input[type="file"]');
                            if (fi) fi.click();
                            else {{
                                var exp = doc.querySelector('[data-testid="stExpander"] summary');
                                if (exp) exp.click();
                            }}
                        }};
                        chatBox.appendChild(plusBtn);
                    }}

                    // Position voice iframe inside chatbox at right: 48px with matching 32px circle
                    if (voiceIframe) {{
                        var wrapper = voiceIframe.closest(".element-container") || voiceIframe;
                        if (!chatBox.contains(wrapper)) {{
                            wrapper.style.position = "absolute";
                            wrapper.style.right = "48px";
                            wrapper.style.bottom = "7px";
                            wrapper.style.width = "32px";
                            wrapper.style.height = "32px";
                            wrapper.style.zIndex = "9999";
                            wrapper.style.margin = "0";
                            wrapper.style.padding = "0";
                            wrapper.style.overflow = "hidden";

                            voiceIframe.style.width = "32px";
                            voiceIframe.style.height = "32px";
                            voiceIframe.style.border = "none";
                            voiceIframe.style.background = "transparent";
                            voiceIframe.style.display = "block";

                            chatBox.appendChild(wrapper);
                        }}
                    }}

                    // Format Streamlit submit button to match 32px size and alignment
                    var submitBtn = chatBox.querySelector('button[data-testid="stChatInputSubmitButton"]') || chatBox.querySelector('[data-testid="stChatInputSubmitButton"] button');
                    if (submitBtn) {{
                        submitBtn.style.width = "32px";
                        submitBtn.style.height = "32px";
                        submitBtn.style.minWidth = "32px";
                        submitBtn.style.minHeight = "32px";
                        submitBtn.style.borderRadius = "50%";
                    }}
                }}
            }}, 120);
        }})();
        </script>
        """, height=0)

        # ── TTS Auto-Speak (hidden, no visible UI) ──────────────────────────────────
        if speaker_on and latest_ai_msg:
            latest_ai_lang = _detect_lang_code(latest_ai_msg, selected_lang)
            safe_ai_msg = _strip_markdown(latest_ai_msg) if latest_ai_msg else ""
            _tts_key = f"tts_{latest_msg_id}"
            if safe_ai_msg and st.session_state.get("_last_tts_key") != _tts_key:
                st.session_state["_last_tts_key"] = _tts_key
                _render_tts_autoplay(
                    safe_ai_msg,
                    latest_ai_lang,
                    st.session_state.get("tts_rate_slider", 1.0),
                    st.session_state.get("tts_pitch_slider", 1.0)
                )

        # Determine if we have a new prompt to process on the next run
        new_prompt = None
        if typed_prompt and typed_prompt.strip():
            new_prompt = typed_prompt.strip()
        elif clicked_qr:
            new_prompt = clicked_qr
            st.session_state["_qr_generation"] += 1
        elif st.session_state.get("_quick_reply_value"):
            new_prompt = st.session_state.pop("_quick_reply_value")
            st.session_state["_qr_generation"] += 1

        if new_prompt:
            st.session_state["_pending_prompt"] = new_prompt
            st.rerun()

    finally:
        db.close()
