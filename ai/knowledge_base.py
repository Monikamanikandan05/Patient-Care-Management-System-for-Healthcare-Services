from ai.vectorstore import get_vectorstore

CARDIAC_KNOWLEDGE = [
    "Heart Attack Symptoms: Chest pain or discomfort, upper body pain (arms, back, neck, jaw), shortness of breath, cold sweat, fatigue, lightheadedness.",
    "Arrhythmia Guidelines: Arrhythmia is an irregular heartbeat. It can be sinus tachycardia (too fast), bradycardia (too slow), or atrial fibrillation. Treatments include medications, lifestyle changes, or pacemakers.",
    "Healthy Blood Pressure Levels: Normal: Less than 120/80 mmHg. Elevated: Systolic between 120-129 and diastolic less than 80. Hypertension Stage 1: Systolic 130-139 or diastolic 80-89.",
    "Troponin Test Info: Troponin is a protein released into the blood when heart muscle is damaged (like during a heart attack). Normal levels are typically below 0.04 ng/mL. Levels above this indicate potential myocardial injury.",
    "Ejection Fraction (EF): Ejection fraction measures the percentage of blood leaving the heart each time it contracts. Normal EF ranges from 50% to 70%. Below 40% may indicate heart failure or cardiomyopathy.",
    "Cardiac Output: Cardiac output is the volume of blood pumped by the heart per minute (typically 4 to 8 L/min at rest). It equals heart rate multiplied by stroke volume.",
    "Cardio-Healthy Diet: Low sodium (less than 2000mg/day), rich in leafy greens, whole grains, berries, fish (omega-3), and limited processed fats or refined sugars."
]

def load_knowledge_base():
    vs = get_vectorstore()
    if not vs.documents:
        vs.add_texts(CARDIAC_KNOWLEDGE)

# Load immediately
load_knowledge_base()
