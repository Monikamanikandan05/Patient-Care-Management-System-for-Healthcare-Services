import sys
import os
sys.path.insert(0, r"c:\Users\monik\OneDrive\Desktop\integrated_patient_care_management_system")

from core.database import engine
from sqlalchemy import inspect

def inspect_table():
    inspector = inspect(engine)
    columns = inspector.get_columns('pharmacy_order_items')
    print("Columns in pharmacy_order_items:")
    for col in columns:
        print(f" - {col['name']}: {col['type']}")

if __name__ == "__main__":
    inspect_table()
