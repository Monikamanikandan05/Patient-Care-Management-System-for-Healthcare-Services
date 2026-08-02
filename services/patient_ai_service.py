import json
from ai.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

def get_medicine_explanation(medication_name: str, dosage: str = "", instructions: str = "") -> dict:
    """
    Returns AI-generated explanation for a medicine including purpose,
    dosage context, side effects, precautions, and food interactions.
    """
    llm = get_llm()
    if getattr(llm, "_llm_type", None) == "offline_mock":
        return {
            "purpose": "Used to treat specific medical conditions as prescribed.",
            "dosage": dosage or "As directed by physician.",
            "side_effects": "Common side effects may occur. Consult your doctor if severe.",
            "precautions": "Take exactly as prescribed.",
            "food_interactions": instructions or "No specific food interactions noted."
        }

    sys_msg = SystemMessage(content="You are a helpful AI Medicine Assistant. You provide simple, patient-friendly explanations for medications. Return your response ONLY as a valid JSON object with the following string keys: 'purpose', 'dosage', 'side_effects', 'precautions', 'food_interactions'. Keep explanations concise and easy to understand for elderly patients.")
    human_msg = HumanMessage(content=f"Explain the medication: {medication_name}. Dosage info: {dosage}. Instructions given: {instructions}.")
    
    try:
        response = llm.invoke([sys_msg, human_msg])
        content = response.content.strip()
        # Clean up possible markdown formatting for JSON
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        return json.loads(content)
    except Exception as e:
        return {
            "purpose": "Explanation unavailable.",
            "dosage": dosage,
            "side_effects": "Data unavailable.",
            "precautions": "Please consult your doctor.",
            "food_interactions": "Data unavailable.",
            "error": str(e)
        }

def get_health_summary(records: list) -> dict:
    """
    Generates an AI health summary based on a patient's recent health records.
    Returns a dictionary with summary, abnormal_tests, recovery_progress, 
    lifestyle_tips, and warnings.
    """
    if not records:
        return {
            "summary": "No recent health records available.",
            "abnormal_tests": [],
            "recovery_progress": "N/A",
            "lifestyle_tips": ["Maintain a balanced diet.", "Exercise regularly."],
            "warnings": []
        }

    llm = get_llm()
    if getattr(llm, "_llm_type", None) == "offline_mock":
        return {
            "summary": "Patient is undergoing routine monitoring.",
            "abnormal_tests": ["Mocked test results"],
            "recovery_progress": "Stable",
            "lifestyle_tips": ["Stay hydrated", "Get adequate rest"],
            "warnings": ["Consult your doctor for detailed analysis."]
        }

    # Serialize records for LLM context
    context_data = []
    for r in records[:5]: # Take last 5 records
        context_data.append({
            "date": str(r.recorded_at),
            "department": r.specialty_type,
            "diagnosis": r.diagnosis,
            "vitals": {
                "bp": r.blood_pressure,
                "hr": r.heart_rate,
                "blood_sugar": getattr(r, 'blood_sugar', None),
                "cholesterol": getattr(r, 'cholesterol', None)
            }
        })
    
    sys_msg = SystemMessage(content="You are an AI Health Analyst. Generate an easy-to-understand health summary for a patient based on their recent records. Return your response ONLY as a valid JSON object with these keys: 'summary' (string), 'abnormal_tests' (list of strings), 'recovery_progress' (string), 'lifestyle_tips' (list of strings), 'warnings' (list of strings highlighting medicine interactions or duplicate prescriptions).")
    human_msg = HumanMessage(content=f"Analyze these patient records: {json.dumps(context_data)}")

    try:
        response = llm.invoke([sys_msg, human_msg])
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        return json.loads(content)
    except Exception as e:
        return {
            "summary": "AI summary currently unavailable.",
            "abnormal_tests": [],
            "recovery_progress": "Unknown",
            "lifestyle_tips": [],
            "warnings": []
        }
