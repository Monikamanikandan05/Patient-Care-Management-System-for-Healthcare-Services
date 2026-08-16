import sys
sys.path.insert(0, ".")
from services.email_service import send_doctor_credentials_email

print("Testing email sending...")
result = send_doctor_credentials_email("Test Doctor", "ipcmssmartcare@gmail.com", "TestPass123")
print(f"Result: {result}")
