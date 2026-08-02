from sqlalchemy.orm import Session
from models.models import PharmacyMedicine, PharmacyOrder, PharmacyOrderItem
from decimal import Decimal
from datetime import date


# ── Default medicine catalogue to seed on first launch ───────────────────────────
DEFAULT_MEDICINES = [
    {
        "name": "Amlodipine 5mg Tablets",
        "generic_name": "Amlodipine Besylate",
        "category": "Cardiology",
        "description": "Calcium channel blocker used to treat high blood pressure (hypertension) and chest pain (angina). Helps relax blood vessels so the heart doesn't have to work as hard.",
        "price": 8.50,
        "stock_qty": 150,
        "unit": "Tablet (10×10 pack)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/amlodipine_5mg.jpg",
        "color_theme": "#ef4444",
        "manufacture_date": date(2025, 4, 1),
        "expiry_date": date(2027, 4, 30),
    },
    {
        "name": "Clopidogrel 75mg Tablets",
        "generic_name": "Clopidogrel Bisulfate",
        "category": "Cardiology",
        "description": "Antiplatelet medication that prevents blood clots in patients with heart disease, recent heart attack, or stroke. Keeps platelets from sticking together.",
        "price": 12.00,
        "stock_qty": 80,
        "unit": "Tablet (10×10 pack)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/clopidogrel_75mg.jpg",
        "color_theme": "#22c55e",
        "manufacture_date": date(2025, 3, 1),
        "expiry_date": date(2027, 3, 31),
    },
    {
        "name": "Amoxicillin 500mg Capsules",
        "generic_name": "Amoxicillin Trihydrate",
        "category": "Antibiotics",
        "description": "Broad-spectrum penicillin antibiotic used to treat bacterial infections including chest, dental, skin, and urinary infections. Available in 21-capsule packs.",
        "price": 6.50,
        "stock_qty": 200,
        "unit": "Capsule (21 pack)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/amoxicillin_500mg.jpg",
        "color_theme": "#f97316",
        "manufacture_date": date(2025, 1, 1),
        "expiry_date": date(2027, 1, 31),
    },
    {
        "name": "Herbion Cough Syrup 150ml",
        "generic_name": "Herbal Cough Formula",
        "category": "Cough & Cold",
        "description": "Sugar-free herbal cough syrup with stevia. Alcohol-free and non-sedative. Soothes coughs associated with hoarseness, dry throat and irritants. 150ml bottle.",
        "price": 9.00,
        "stock_qty": 60,
        "unit": "Bottle (150ml)",
        "requires_prescription": False,
        "image_path": "assets/pharmacy/herbion_cough_syrup.jpg",
        "color_theme": "#16a34a",
        "manufacture_date": date(2025, 6, 1),
        "expiry_date": date(2026, 12, 31),
    },
    {
        "name": "Atorvastatin 20mg Tablets",
        "generic_name": "Atorvastatin Calcium",
        "category": "Cholesterol",
        "description": "Statin medication used to lower cholesterol and triglycerides in the blood. Reduces the risk of heart attack, stroke, and cardiovascular disease. 3×10 tablet pack.",
        "price": 10.00,
        "stock_qty": 120,
        "unit": "Tablet (3×10 pack)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/atorvastatin_20mg.jpg",
        "color_theme": "#f59e0b",
        "manufacture_date": date(2025, 2, 1),
        "expiry_date": date(2027, 2, 28),
    },
    {
        "name": "Levothyroxine 50mcg Tablets",
        "generic_name": "Levothyroxine Sodium",
        "category": "Thyroid",
        "description": "Synthetic thyroid hormone replacement used to treat hypothyroidism (underactive thyroid). Euthyrox-50, 100 tablets per bottle. Take on empty stomach.",
        "price": 7.50,
        "stock_qty": 90,
        "unit": "Tablet (100 pack)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/levothyroxine_50mcg.jpg",
        "color_theme": "#6366f1",
        "manufacture_date": date(2025, 5, 1),
        "expiry_date": date(2027, 5, 31),
    },
    {
        "name": "Metformin 500mg SR Tablets",
        "generic_name": "Metformin Hydrochloride",
        "category": "Diabetes",
        "description": "Sustained-release biguanide antidiabetic used as first-line treatment for type 2 diabetes. Metsmall-500 by Dr. Reddy's. Controls blood glucose by reducing liver glucose production.",
        "price": 5.00,
        "stock_qty": 180,
        "unit": "Tablet (28 pack)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/metformin_500mg.jpg",
        "color_theme": "#059669",
        "manufacture_date": date(2025, 7, 1),
        "expiry_date": date(2027, 7, 31),
    },
    {
        "name": "Latanoprost 0.005% Eye Drops",
        "generic_name": "Latanoprost Ophthalmic Solution",
        "category": "Ophthalmology",
        "description": "Prostaglandin analogue eye drops used to reduce intraocular pressure (IOP) in open-angle glaucoma and ocular hypertension. 2.5mL sterile bottle. For eye use only.",
        "price": 22.00,
        "stock_qty": 40,
        "unit": "Bottle (2.5mL)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/latanoprost_drops.jpg",
        "color_theme": "#06b6d4",
        "manufacture_date": date(2025, 3, 15),
        "expiry_date": date(2027, 3, 14),
    },
    {
        "name": "Paracetamol 500mg Tablets",
        "generic_name": "Acetaminophen",
        "category": "Pain Relief",
        "description": "Analgesic and antipyretic tablet for relief of mild to moderate pain, headache, toothache, body ache and fever. Pyrostop-500 by Mouliis Pharma.",
        "price": 3.50,
        "stock_qty": 300,
        "unit": "Tablet (15 pack)",
        "requires_prescription": False,
        "image_path": "assets/pharmacy/paracetamol_500mg.jpg",
        "color_theme": "#ec4899",
        "manufacture_date": date(2025, 8, 1),
        "expiry_date": date(2027, 8, 31),
    },
    {
        "name": "Insulin Glargine 100 IU/mL",
        "generic_name": "Insulin Glargine (r-DNA Origin)",
        "category": "Diabetes",
        "description": "Long-acting basal insulin injection for type 1 and type 2 diabetes. Glarinex by Reginix. 10mL vial or 3mL prefilled pen. Administer subcutaneously once daily.",
        "price": 45.00,
        "stock_qty": 35,
        "unit": "Vial (10mL) / Pen (3mL)",
        "requires_prescription": True,
        "image_path": "assets/pharmacy/insulin_glargine.jpg",
        "color_theme": "#8b5cf6",
        "manufacture_date": date(2025, 6, 15),
        "expiry_date": date(2026, 12, 14),
    },
    {
        "name": "Hydrocortisone Cream 1%",
        "generic_name": "Hydrocortisone",
        "category": "Dermatology",
        "description": "Topical corticosteroid cream for relief of minor skin irritations, itching and rashes caused by eczema, insect bites, poison ivy, and contact dermatitis. 28.4g tube by Dynarex.",
        "price": 7.00,
        "stock_qty": 110,
        "unit": "Tube (28.4g)",
        "requires_prescription": False,
        "image_path": "assets/pharmacy/hydrocortisone_cream.jpg",
        "color_theme": "#f59e0b",
        "manufacture_date": date(2025, 5, 10),
        "expiry_date": date(2027, 5, 9),
    },
]


def seed_medicines(db: Session):
    """Seed default medicines — add missing ones and sync empty fields on existing ones."""
    existing_map = {m.name: m for m in db.query(PharmacyMedicine).all()}
    modified = False
    for med_data in DEFAULT_MEDICINES:
        name = med_data["name"]
        if name not in existing_map:
            db.add(PharmacyMedicine(**med_data))
            modified = True
        else:
            med = existing_map[name]
            # Sync any empty or missing fields
            for field, val in med_data.items():
                curr = getattr(med, field, None)
                if curr is None or (field == "price" and (curr == 0 or str(curr).strip() == "")):
                    setattr(med, field, val)
                    modified = True
    if modified:
        db.commit()


def get_all_medicines(db: Session, include_inactive: bool = False):
    q = db.query(PharmacyMedicine)
    if not include_inactive:
        q = q.filter(PharmacyMedicine.is_active == True)
    return q.order_by(PharmacyMedicine.category, PharmacyMedicine.name).all()


def get_medicine(db: Session, med_id: int):
    return db.query(PharmacyMedicine).filter(PharmacyMedicine.id == med_id).first()


def add_medicine(db: Session, name, generic_name, category, description,
                 price, stock_qty, unit, requires_prescription, image_path,
                 color_theme, manufacture_date=None, expiry_date=None):
    med = PharmacyMedicine(
        name=name, generic_name=generic_name, category=category,
        description=description, price=price, stock_qty=stock_qty,
        unit=unit, requires_prescription=requires_prescription,
        image_path=image_path, color_theme=color_theme,
        manufacture_date=manufacture_date, expiry_date=expiry_date,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


def update_medicine(db: Session, med_id: int, **kwargs):
    med = get_medicine(db, med_id)
    if med:
        for k, v in kwargs.items():
            setattr(med, k, v)
        db.commit()
        db.refresh(med)
    return med


def update_stock(db: Session, med_id: int, new_qty: int):
    med = get_medicine(db, med_id)
    if med:
        med.stock_qty = new_qty
        db.commit()
    return med


def deactivate_medicine(db: Session, med_id: int):
    return update_medicine(db, med_id, is_active=False)


def reactivate_medicine(db: Session, med_id: int):
    return update_medicine(db, med_id, is_active=True)


def place_order(db: Session, patient_id: int, cart: list[dict]) -> PharmacyOrder:
    """
    cart: list of {"medicine_id": int, "quantity": int}
    Returns the created PharmacyOrder.
    Raises ValueError if stock is insufficient.
    """
    total = Decimal("0.00")
    items_to_add = []

    for item in cart:
        med = get_medicine(db, item["medicine_id"])
        if not med or not med.is_active:
            raise ValueError(f"Medicine ID {item['medicine_id']} not found or inactive.")
        if med.stock_qty < item["quantity"]:
            raise ValueError(f"Insufficient stock for {med.name}. Available: {med.stock_qty}")
        unit_price = Decimal(str(med.price))
        total += unit_price * item["quantity"]
        items_to_add.append((med, item["quantity"], unit_price))

    order = PharmacyOrder(patient_id=patient_id, total_amount=total, status="Pending")
    db.add(order)
    db.flush()  # get order.id

    for med, qty, unit_price in items_to_add:
        db.add(PharmacyOrderItem(
            order_id=order.id,
            medicine_id=med.id,
            quantity=qty,
            unit_price=unit_price,
        ))
        med.stock_qty -= qty  # reduce stock

    db.commit()
    db.refresh(order)
    return order


def get_patient_orders(db: Session, patient_id: int):
    return (db.query(PharmacyOrder)
            .filter(PharmacyOrder.patient_id == patient_id)
            .order_by(PharmacyOrder.created_at.desc())
            .all())


def get_all_orders(db: Session):
    return (db.query(PharmacyOrder)
            .order_by(PharmacyOrder.created_at.desc())
            .all())


def update_order_status(db: Session, order_id: int, status: str):
    order = db.query(PharmacyOrder).filter(PharmacyOrder.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return order


def get_categories(db: Session):
    rows = db.query(PharmacyMedicine.category).filter(
        PharmacyMedicine.is_active == True
    ).distinct().all()
    return sorted([r[0] for r in rows if r[0]])
