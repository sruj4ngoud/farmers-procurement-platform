"""Quick demo seeder: populates the PostgreSQL database with demo data.

Run from backend/:
    python demo_seed.py

Then start the backend with:
    python -m uvicorn app.main:app --port 8000

Requires DATABASE_URL in .env pointing to PostgreSQL.
"""
import uuid
import sys
import os
from decimal import Decimal
from datetime import date, time, datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.core.admin_security import hash_password
from app.models import (
    Farmer, LandRecord, CultivationRecord, ProcurementCentre, Slot,
    Booking, QueueToken, ProcurementRecord, Payment, User,
    District, Mandal, Crop,
)
from app.config.msp import MSP_DATA

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///demo.db")
connect_args = {"check_samethread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, **connect_args)

# Create all tables
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

def uid(name):
    return uuid.uuid5(uuid.NAMESPACE_URL, f"demo-seed-{name}")

# --- Districts ---
districts_data = [
    {"name": "Sangareddy", "state": "Telangana"},
    {"name": "Medchal-Malkajgiri", "state": "Telangana"},
    {"name": "Ranga Reddy", "state": "Telangana"},
]

district_objs = {}
for d in districts_data:
    dist = District(
        district_id=uid(f"district-{d['name']}"),
        name=d["name"],
        state=d["state"],
    )
    db.merge(dist)
    district_objs[d["name"]] = dist

# --- Mandals ---
mandals_data = [
    {"name": "Tandoor", "district": "Sangareddy"},
    {"name": "Patancheru", "district": "Sangareddy"},
    {"name": "Zaheerabad", "district": "Sangareddy"},
    {"name": "Medchal", "district": "Medchal-Malkajgiri"},
    {"name": "Mominpet", "district": "Ranga Reddy"},
]

for m in mandals_data:
    mandal = Mandal(
        mandal_id=uid(f"mandal-{m['name']}"),
        name=m["name"],
        district_id=uid(f"district-{m['district']}"),
    )
    db.merge(mandal)

# --- Crops (89 from MSP data) ---
crop_categories = {
    "Paddy": "Cereal", "Wheat": "Cereal", "Maize": "Cereal", "Barley": "Cereal",
    "Sorghum (Jowar)": "Cereal", "Pearl Millet (Bajra)": "Cereal", "Finger Millet (Ragi)": "Cereal",
    "Foxtail Millet": "Cereal", "Little Millet": "Cereal", "Kodo Millet": "Cereal",
    "Barnyard Millet": "Cereal", "Proso Millet": "Cereal", "Browntop Millet": "Cereal",
    "Oat": "Cereal", "Buckwheat": "Cereal",
    "Red Gram (Tur/Arhar)": "Pulse", "Black Gram (Urad)": "Pulse", "Green Gram (Moong)": "Pulse",
    "Bengal Gram (Chickpea/Chana)": "Pulse", "Lentil (Masoor)": "Pulse", "Field Pea": "Pulse",
    "Cowpea (Lobia)": "Pulse", "Horse Gram": "Pulse", "Moth Bean": "Pulse",
    "Soybean": "Oilseed", "Groundnut": "Oilseed", "Sunflower": "Oilseed",
    "Sesame": "Oilseed", "Mustard": "Oilseed", "Safflower": "Oilseed",
    "Castor": "Oilseed", "Linseed": "Oilseed", "Niger Seed": "Oilseed",
    "Cotton": "Cash Crop", "Sugarcane": "Cash Crop", "Tobacco": "Cash Crop",
    "Jute": "Fiber Crop", "Mesta": "Fiber Crop",
    "Tea": "Plantation", "Coffee": "Plantation", "Coconut": "Plantation",
    "Arecanut": "Plantation", "Rubber": "Plantation",
    "Pepper": "Spice", "Cardamom": "Spice", "Turmeric": "Spice", "Cumin": "Spice",
    "Coriander": "Spice", "Chilli": "Spice", "Fenugreek": "Spice", "Ginger": "Spice",
    "Garlic": "Spice", "Tamarind": "Spice",
    "Potato": "Vegetable", "Tomato": "Vegetable", "Onion": "Vegetable",
    "Brinjal (Eggplant)": "Vegetable", "Okra (Lady's Finger)": "Vegetable",
    "Cabbage": "Vegetable", "Cauliflower": "Vegetable", "Carrot": "Vegetable",
    "Radish": "Vegetable", "Beetroot": "Vegetable", "Bottle Gourd": "Vegetable",
    "Bitter Gourd": "Vegetable", "Ridge Gourd": "Vegetable", "Pumpkin": "Vegetable",
    "Cucumber": "Vegetable", "Green Peas": "Vegetable", "French Bean": "Vegetable",
    "Drumstick": "Vegetable", "Sweet Potato": "Vegetable",
    "Tapioca (Cassava)": "Tuber",
    "Banana": "Fruit", "Mango": "Fruit", "Guava": "Fruit", "Papaya": "Fruit",
    "Pomegranate": "Fruit", "Grapes": "Fruit", "Orange": "Fruit",
    "Sweet Lime (Mosambi)": "Fruit", "Lemon": "Fruit", "Watermelon": "Fruit",
    "Muskmelon": "Fruit", "Pineapple": "Fruit", "Apple": "Fruit",
    "Sapota (Chikoo)": "Fruit", "Jackfruit": "Fruit", "Custard Apple": "Fruit",
}

for crop_name, msp_value in MSP_DATA.items():
    crop = Crop(
        crop_id=uid(f"crop-{crop_name}"),
        crop_name=crop_name,
        crop_category=crop_categories.get(crop_name, "Other"),
        is_active=True,
        msp_per_quintal=Decimal(str(msp_value)),
        msp_effective_date=date(2025, 1, 1),
    )
    db.merge(crop)

db.commit()

# --- Farmers ---
farmers_data = [
    {"passbook": "PB-2024-001", "name": "Ramesh Kumar", "mobile": "9876543210", "village": "Hariharnagar", "mandal": "Tandoor", "district": "Sangareddy", "survey": "101-A", "land": "5.50", "lat": "17.358333", "lon": "78.433333"},
    {"passbook": "PB-2024-002", "name": "Suresh Reddy", "mobile": "9876543211", "village": "Patancheru", "mandal": "Patancheru", "district": "Sangareddy", "survey": "202-B", "land": "8.00", "lat": "17.500000", "lon": "78.500000"},
    {"passbook": "PB-2024-003", "name": "Lakshmi Devi", "mobile": "9876543212", "village": "Zaheerabad", "mandal": "Zaheerabad", "district": "Sangareddy", "survey": "303-C", "land": "3.25", "lat": "17.680000", "lon": "77.610000"},
    {"passbook": "PB-2024-004", "name": "Venkatesh Rao", "mobile": "9876543213", "village": "Bollaram", "mandal": "Medchal", "district": "Medchal-Malkajgiri", "survey": "404-D", "land": "12.00", "lat": "17.480000", "lon": "78.350000"},
    {"passbook": "PB-2024-005", "name": "Anita Bai", "mobile": "9876543214", "village": "Mominpet", "mandal": "Mominpet", "district": "Ranga Reddy", "survey": "505-E", "land": "4.75", "lat": "17.250000", "lon": "78.150000"},
]

for f in farmers_data:
    farmer = Farmer(
        farmer_id=uid(f["passbook"]),
        passbook_number=f["passbook"],
        farmer_name=f["name"],
        mobile_number=f["mobile"],
        village=f["village"],
        mandal=f["mandal"],
        district=f["district"],
        survey_number=f["survey"],
        total_land_acres=Decimal(f["land"]),
        latitude=Decimal(f["lat"]),
        longitude=Decimal(f["lon"]),
    )
    db.merge(farmer)

# --- Land Records ---
for f in farmers_data:
    land = LandRecord(
        land_id=uid(f"land-{f['passbook']}"),
        farmer_id=uid(f["passbook"]),
        survey_number=f["survey"],
        land_area_acres=Decimal(f["land"]),
        land_type="AGRICULTURAL",
        ownership_status="ACTIVE",
    )
    db.merge(land)

# --- Cultivations ---
cultivations_data = [
    {"passbook": "PB-2024-001", "season": "Rabi-2024", "area": "4.50", "crop": "Maize", "produced": "90.00", "to_sell": "75.00"},
    {"passbook": "PB-2024-001", "season": "Kharif-2024", "area": "3.00", "crop": "Cotton", "produced": "45.00", "to_sell": "40.00"},
    {"passbook": "PB-2024-002", "season": "Rabi-2024", "area": "6.00", "crop": "Paddy", "produced": "150.00", "to_sell": "120.00"},
    {"passbook": "PB-2024-002", "season": "Kharif-2024", "area": "4.00", "crop": "Groundnut", "produced": "60.00", "to_sell": "50.00"},
    {"passbook": "PB-2024-003", "season": "Rabi-2024", "area": "2.50", "crop": "Tur Dal", "produced": "35.00", "to_sell": "30.00"},
    {"passbook": "PB-2024-004", "season": "Rabi-2024", "area": "8.00", "crop": "Paddy", "produced": "200.00", "to_sell": "180.00"},
    {"passbook": "PB-2024-005", "season": "Kharif-2024", "area": "3.50", "crop": "Soybean", "produced": "50.00", "to_sell": "45.00"},
]

for c in cultivations_data:
    cult = CultivationRecord(
        cultivation_id=uid(f"cult-{c['passbook']}-{c['crop']}"),
        farmer_id=uid(c["passbook"]),
        season=c["season"],
        cultivated_area_acres=Decimal(c["area"]),
        crop=c["crop"],
        quantity_produced_quintals=Decimal(c["produced"]),
        quantity_to_sell_quintals=Decimal(c["to_sell"]),
    )
    db.merge(cult)

# --- Procurement Centres ---
centres_data = [
    {"code": "PC-HYD-001", "name": "Tandoor Procurement Centre", "agency": "NAFED", "village": "Tandoor", "mandal": "Tandoor", "district": "Sangareddy", "lat": "17.360000", "lon": "78.440000", "capacity": 50, "status": "ACTIVE"},
    {"code": "PC-HYD-002", "name": "Patancheru Agri Hub", "agency": "Government", "village": "Patancheru", "mandal": "Patancheru", "district": "Sangareddy", "lat": "17.510000", "lon": "78.510000", "capacity": 80, "status": "ACTIVE"},
    {"code": "PC-HYD-003", "name": "Zaheerabad Market Yard", "agency": "FCI", "village": "Zaheerabad", "mandal": "Zaheerabad", "district": "Sangareddy", "lat": "17.685000", "lon": "77.615000", "capacity": 40, "status": "LIMITED"},
    {"code": "PC-HYD-004", "name": "Medchal Procurement Point", "agency": "Government", "village": "Medchal", "mandal": "Medchal", "district": "Medchal-Malkajgiri", "lat": "17.630000", "lon": "78.480000", "capacity": 60, "status": "ACTIVE"},
]

for c in centres_data:
    centre = ProcurementCentre(
        centre_id=uid(c["code"]),
        centre_code=c["code"],
        centre_name=c["name"],
        agency=c["agency"],
        village=c["village"],
        mandal=c["mandal"],
        district=c["district"],
        latitude=Decimal(c["lat"]),
        longitude=Decimal(c["lon"]),
        capacity=c["capacity"],
        current_status=c["status"],
    )
    db.merge(centre)

# --- Slots (3 days, multiple time slots per centre) ---
slots = []
slot_id_counter = 0
for day_offset in range(3):
    slot_date = date(2025, 10, 1 + day_offset)
    for hour in [9, 10, 11, 14, 15]:
        for c in centres_data:
            slot_id_counter += 1
            slot = Slot(
                slot_id=uid(f"slot-{c['code']}-{slot_date}-{hour}"),
                centre_id=uid(c["code"]),
                slot_date=slot_date,
                start_time=time(hour, 0),
                end_time=time(hour, 30),
                maximum_farmers=10,
                booked_farmers=0,
                is_active=True,
            )
            db.merge(slot)
            slots.append({"centre_code": c["code"], "date": slot_date, "hour": hour, "slot_id": uid(f"slot-{c['code']}-{slot_date}-{hour}")})

# --- A sample booking for PB-2024-001 ---
first_slot = slots[0]
booking = Booking(
    booking_id=uid("booking-demo-001"),
    booking_number="BK-2024-DEMO-001",
    farmer_id=uid("PB-2024-001"),
    cultivation_id=uid("cult-PB-2024-001-Maize"),
    centre_id=uid(first_slot["centre_code"]),
    slot_id=first_slot["slot_id"],
    quantity_to_sell_quintals=Decimal("30.00"),
    booking_status="CONFIRMED",
)
db.merge(booking)

# Update slot booked count
slot_obj = db.get(Slot, first_slot["slot_id"])
if slot_obj:
    slot_obj.booked_farmers = 1

# Queue token for the booking
token = QueueToken(
    queue_id=uid("queue-demo-001"),
    booking_id=uid("booking-demo-001"),
    token_number=1,
    queue_status="WAITING",
)
db.merge(token)

db.commit()

# --- Admin Users (one per district) ---
admin_data = [
    {"username": "admin_sangareddy", "password": "admin123", "district": "Sangareddy"},
    {"username": "admin_medchal", "password": "admin123", "district": "Medchal-Malkajgiri"},
    {"username": "admin_rangareddy", "password": "admin123", "district": "Ranga Reddy"},
]

for a in admin_data:
    admin_user = User(
        user_id=uid(f"admin-{a['district']}"),
        username=a["username"],
        password_hash=hash_password(a["password"]),
        role="DISTRICT_ADMIN",
        district=a["district"],
        is_active=True,
    )
    db.merge(admin_user)

db.commit()
db.close()

print("Demo data seeded successfully!")
print()
print("=" * 50)
print("LOGIN CREDENTIALS")
print("=" * 50)
print()
for f in farmers_data:
    print(f"  Passbook: {f['passbook']}  |  Mobile: {f['mobile']}  |  Name: {f['name']}")
print()
print("ADMIN LOGIN CREDENTIALS")
print("=" * 50)
print()
for a in admin_data:
    print(f"  Username: {a['username']}  |  Password: {a['password']}  |  District: {a['district']}")
print()
print("Start the backend with:")
print(f"  cd backend")
print(f"  .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
