import os
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysql")
DB_NAME = os.getenv("DB_NAME", "patient_care_db")

# SQLAlchemy MySQL Connection URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
