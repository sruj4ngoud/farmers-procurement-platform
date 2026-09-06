#!/usr/bin/env python3
"""Comprehensive Telangana 33-district demo seed script.

Creates a realistic demo environment representing ALL 33 districts of Telangana.

Usage:
    cd backend
    python seed_telangana.py

Requirements:
    DATABASE_URL must be set in .env or environment to a PostgreSQL database.
    The database must have all tables created (run alembic upgrade head first).

Features:
    - 33 Telangana districts
    - ~3-8 mandals per district
    - 2-3 procurement centres per district (~80 total)
    - Slots for each centre
    - ~500 farmers distributed across districts
    - Cultivation records, bookings (various statuses), queue tokens
    - Procurement records with realistic mismatches
    - Bank details and payment records
    - 33 district admin accounts (one per district)
    - Full idempotency (safe to run multiple times)
"""

import sys
import os
import uuid
import random
import hashlib
from datetime import date, time, datetime, timedelta, timezone
from decimal import Decimal
from itertools import cycle

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, delete
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.core.admin_security import hash_password
from app.models import (
    Farmer, LandRecord, CultivationRecord, ProcurementCentre, Slot,
    Booking, QueueToken, ProcurementRecord, Payment, User,
    District, Mandal, Crop, BankDetails, Notification,
)

# ── Stable ID generation ─────────────────────────────────────────────────────

def stable_uuid(namespace: str, name: str) -> uuid.UUID:
    """Generate a deterministic UUID from a namespace and name."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"telangana-seed/{namespace}/{name}")


# ── Telangana 33 Districts Data ──────────────────────────────────────────────

TELANGANA_DISTRICTS = [
    {"name": "Adilabad", "lat": 19.6641, "lon": 78.5320},
    {"name": "Bhadradri Kothagudem", "lat": 17.5574, "lon": 80.6172},
    {"name": "Hanumakonda", "lat": 17.9904, "lon": 79.5633},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"name": "Jagtial", "lat": 18.7917, "lon": 78.9144},
    {"name": "Jangaon", "lat": 17.7272, "lon": 79.1518},
    {"name": "Jayashankar Bhupalpally", "lat": 18.1785, "lon": 79.9505},
    {"name": "Jogulamba Gadwal", "lat": 16.2355, "lon": 77.8557},
    {"name": "Kamareddy", "lat": 18.3218, "lon": 78.3342},
    {"name": "Karimnagar", "lat": 18.4386, "lon": 79.1288},
    {"name": "Khammam", "lat": 17.2473, "lon": 80.1514},
    {"name": "Kumuram Bheem", "lat": 19.3592, "lon": 79.4663},
    {"name": "Mahabubabad", "lat": 17.5973, "lon": 80.0017},
    {"name": "Mahabubnagar", "lat": 16.7488, "lon": 77.9853},
    {"name": "Mancherial", "lat": 18.8716, "lon": 79.4463},
    {"name": "Medak", "lat": 18.0522, "lon": 78.2631},
    {"name": "Medchal-Malkajgiri", "lat": 17.5063, "lon": 78.5436},
    {"name": "Mulugu", "lat": 18.1873, "lon": 80.5556},
    {"name": "Nagarkurnool", "lat": 16.4833, "lon": 78.3167},
    {"name": "Nalgonda", "lat": 17.0575, "lon": 79.2671},
    {"name": "Narayanpet", "lat": 16.7448, "lon": 77.4946},
    {"name": "Nirmal", "lat": 19.0960, "lon": 78.3440},
    {"name": "Nizamabad", "lat": 18.6725, "lon": 78.0940},
    {"name": "Peddapalli", "lat": 18.6176, "lon": 79.3843},
    {"name": "Rajanna Sircilla", "lat": 18.3863, "lon": 78.8111},
    {"name": "Rangareddy", "lat": 17.2324, "lon": 78.2141},
    {"name": "Sangareddy", "lat": 17.6292, "lon": 78.0870},
    {"name": "Siddipet", "lat": 18.1019, "lon": 78.8491},
    {"name": "Suryapet", "lat": 17.1415, "lon": 79.6291},
    {"name": "Vikarabad", "lat": 17.3381, "lon": 77.9050},
    {"name": "Wanaparthy", "lat": 16.3622, "lon": 78.0629},
    {"name": "Warangal", "lat": 17.9784, "lon": 79.5941},
    {"name": "Yadadri Bhuvanagiri", "lat": 17.5932, "lon": 78.9497},
]

# ── Mandals per district ─────────────────────────────────────────────────────

TELANGANA_MANDALS = {
    "Adilabad": ["Adilabad", "Boath", "Belapur", "Ichoda", "Jannaram", "Kaddamped"],
    "Bhadradri Kothagudem": ["Kothagudem", "Palwancha", "Yellandu", "Bhadrachalam", "Dummugudem"],
    "Hanumakonda": ["Hanumakonda", "Wardhannapet", "Shayampet", "Duggondi", "Parvathagiri"],
    "Hyderabad": ["Ameerpet", "Secunderabad", "Charminar", "Tolichowki", "LB Nagar"],
    "Jagtial": ["Jagtial", "Korutla", "Metpally", "Raikal", "Dharmapuri"],
    "Jangaon": ["Jangaon", "Station Ghanpur", "Duddeda", "Raghunathpally", "Lingalaghanpur"],
    "Jayashankar Bhupalpally": ["Bhupalpally", "Mallaram", "Regonda", "Tekubothur", "Chityal"],
    "Jogulamba Gadwal": ["Gadwal", "Alampur", "Ieeja", "Maldakal", "Waddepally"],
    "Kamareddy": ["Kamareddy", "Banswada", "Yellareddy", "Nizamsagar", "Bichkunda"],
    "Karimnagar": ["Karimnagar", "Huzurabad", "Manakondur", "Vemulawada", "Gangadhara"],
    "Khammam": ["Khammam", "Kusumanchi", "Yerrupalem", "Tallada", "Mudigal"],
    "Kumuram Bheem": ["Asifabad", "Kagaznagar", "Kerameri", "Wankidi", "Jannaram"],
    "Mahabubabad": ["Mahabubabad", "Dornakal", "Kesamudram", "Nellikudur", "Maripeda"],
    "Mahabubnagar": ["Mahabubnagar", "Kollapur", "Achampet", "Shadnagar", "Codavelly"],
    "Mancherial": ["Mancherial", "Mallapur", "Kotapally", "Chennur", "Dandepally"],
    "Medak": ["Medak", "Narsingi", "Chegunta", "Masaipet", "Regode"],
    "Medchal-Malkajgiri": ["Medchal", "Kukatpally", "Ghatkesar", "Uppal", "Malkajgiri"],
    "Mulugu": ["Mulugu", "Wajidabad", "Venkatapur", "Eturnagaram", "Tadvai"],
    "Nagarkurnool": ["Nagarkurnool", "Achampet", "Thimmajipet", "Kollapur", "Kalwakurthy"],
    "Nalgonda": ["Nalgonda", "Miryalaguda", "Devarakonda", "Munugode", "Chityal"],
    "Narayanpet": ["Narayanpet", "Makthal", "Kosgi", "Damaragidgi", "Utkoor"],
    "Nirmal": ["Nirmal", "Khanapur", "Bhainsa", "Mudhole", "Laxmanchanda"],
    "Nizamabad": ["Nizamabad", "Armoor", "Bodhan", "Balkonda", "Mortad"],
    "Peddapalli": ["Peddapalli", "Manthani", "Sultanabad", "Julapalli", "Odela"],
    "Rajanna Sircilla": ["Sircilla", "Kondapaka", "Vemulawada", "Yellareddy", "Thimmapur"],
    "Rangareddy": ["Ibrahimpatnam", "Chevella", "Shamshabad", "Shamirpet", "Medipally"],
    "Sangareddy": ["Sangareddy", "Patancheru", "Zaheerabad", "Kandi", "Ramchandrapuram"],
    "Siddipet": ["Siddipet", "Dubbak", "Gajwel", "Cheriyal", "Nangnoor"],
    "Suryapet": ["Suryapet", "Huzurnagar", "Kodad", "Thirumalagiri", "Mothey"],
    "Vikarabad": ["Vikarabad", "Tandur", "Pargi", "Basheerabad", "Damaracherla"],
    "Wanaparthy": ["Wanaparthy", "Amarchintamani", "Peddakothapally", "Marikal", "Balmoor"],
    "Warangal": ["Warangal", "Hanamkonda", "Kazipet", "Parkal", "Narsampet"],
    "Yadadri Bhuvanagiri": ["Bhongir", "Aler", "Mothisila", "Yadadri", "Turkapally"],
}

# ── Centre name templates per district ────────────────────────────────────────

CENTRE_AGENCIES = ["NAFED", "FCI", "Government", "NAFED", "FCI"]

def generate_centre_data(district_name: str, district_lat: float, district_lon: float,
                         mandals: list[str], dist_idx: int) -> list[dict]:
    """Generate 2-3 procurement centres per district."""
    centres = []
    num_centres = 2 + (dist_idx % 2)  # 2 or 3 centres
    for i in range(num_centres):
        mandal = mandals[i % len(mandals)]
        # Slight offset from district centre for realistic coordinates
        lat_offset = random.uniform(-0.05, 0.05)
        lon_offset = random.uniform(-0.05, 0.05)
        agency = CENTRE_AGENCIES[(dist_idx + i) % len(CENTRE_AGENCIES)]
        code_suffix = f"TS-{dist_idx+1:02d}-{i+1:02d}"
        centres.append({
            "code": f"PC-{code_suffix}",
            "name": f"{mandal} Procurement Centre",
            "agency": agency,
            "village": mandal,
            "mandal": mandal,
            "district": district_name,
            "lat": round(district_lat + lat_offset, 6),
            "lon": round(district_lon + lon_offset, 6),
            "capacity": random.choice([40, 50, 60, 70, 80]),
            "status": "ACTIVE",
        })
    return centres


# ── Farmer Name Pools ────────────────────────────────────────────────────────

FARMER_FIRST_NAMES = [
    "Ramesh", "Suresh", "Rajesh", "Mahesh", "Dinesh", "Ganesh", "Ravindra",
    "Srinivas", "Venkatesh", "Nagaraju", "Kishore", "Prakash", "Srinivas",
    "Anil", "Naresh", "Sunil", "Vijay", "Raj", "Kumar", "Ravi",
    "Sita", "Lakshmi", "Anita", "Saroja", "Latha", "Padma", "Rani",
    "Geeta", "Sumathi", "Usha", "Kavitha", "Sujatha", "Nirmala", "Parvathi",
    "Ramana", "Sambhu", "Durga", "Prasad", "Krishna", "Mohan", "Madhav",
    "Harish", "Pavan", "Teja", "Kiran", "Santosh", "Jagadish", "Bapu",
    "Sharada", "Vasantha", "Nagamani", "Sunitha", "Jyothi", "Padmavathi",
    "Lalitha", "Devamma", "Amrutha", "Chandramma", "Yellamma",
    "Krishnaiah", "Subbamma", "Rajam", "Sarojini", "Bhavani",
]

FARMER_LAST_NAMES = [
    "Kumar", "Reddy", "Naidu", "Goud", "Yadav", "Rao", "Nayak",
    "Devi", "Bai", "Lakshmi", "Rani", "Amma", "Joshi", "Sharma",
    "Patel", "Singh", "Das", "Dasari", "Nambula", "Kurma", "Prasad",
    "Varma", "Prasad", "Naik", "Hegde", "Kamal", "Rao", "Shankar",
    "Babu", "Srinivas", "Sarma", "Murthy", "Kotaiah", "Laxmaiah",
    "Srinu", "Rajula", "Subbamma", "Savitri", "Kavitha", "Rajini",
    "Surekha", "Nagalakshmi", "Chandrika", "Padmavathi", "Shyamala",
]

VILLAGE_NAMES = [
    "Rampur", "Chinnapuram", "Peddapuram", "Kommireddy", "Gollapally",
    "Narsingapuram", "Gandhinagar", "Venkatapur", "Rajupet", "Malkapur",
    "Sultanpur", "Nagulapadu", "Bhairavaram", "Konapuram", "Yerragudi",
    "Komatipalli", "Thimmapur", "Chilakalapudi", "Pallegudem", "Vempalli",
    "Kodavatipadu", "Bodduvari", "Nakkapalli", "Nizamabad", "Vajrakarur",
    "Gadwal", "Dwaraka Tirumala", "Bobbili", "Yellammapalem", "Pedapadu",
    "Chintalapudi", "Nuzvid", "Vissannapet", "Chatrai", "Musunuru",
    "Jaggayyapeta", "Nandigama", "Ibrahimpatnam", "Kankipadu", "Gannavaram",
]

# ── MSP Crops (subset for cultivation) ──────────────────────────────────────

CULTIVATION_CROPS = [
    ("Paddy", "Cereal", 2320),
    ("Maize", "Cereal", 2090),
    ("Cotton", "Cash Crop", 7121),
    ("Groundnut", "Oilseed", 6540),
    ("Red Gram (Tur/Arhar)", "Pulse", 7300),
    ("Black Gram (Urad)", "Pulse", 7400),
    ("Green Gram (Moong)", "Pulse", 8550),
    ("Turmeric", "Spice", 12500),
    ("Chilli", "Spice", 14000),
    ("Soybean", "Oilseed", 4892),
    ("Sugarcane", "Cash Crop", 3150),
    ("Bengal Gram (Chickpea/Chana)", "Pulse", 5450),
]

SEASONS = ["Rabi-2024", "Kharif-2024", "Rabi-2025", "Kharif-2025"]

BOOKING_STATUSES_DISTRIBUTION = [
    "PENDING_ADMIN_REVIEW",
    "PENDING_ADMIN_REVIEW",
    "PENDING_ADMIN_REVIEW",
    "ACCEPTED",
    "ACCEPTED",
    "ACCEPTED",
    "AUTO_ACCEPTED",
    "COMPLETED",
    "COMPLETED",
    "COMPLETED",
    "REJECTED",
    "CANCELLED",
]

AGENCIES = ["NAFED", "FCI", "Government", "NAFED", "FCI"]

IFSC_CODES = [
    "SBIN0001234", "HDFC0004567", "ICIC0007890", "UBIN0512345",
    "PUNB0006789", "CNRB0001234", "BKID0004567", "ANDB0007890",
    "IDIB0001234", "CBIN0004567",
]


# ── Main Seed Logic ──────────────────────────────────────────────────────────

def main():
    db_url = os.getenv("DATABASE_URL", "sqlite:///demo_telangana.db")
    is_postgres = "postgresql" in db_url.lower() or "psycopg" in db_url.lower()

    engine_kwargs = {}
    if not is_postgres:
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(db_url, **engine_kwargs)

    if is_postgres:
        # Enable UUID generation for PostgreSQL
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\""))
            conn.commit()

    Session = sessionmaker(bind=engine)
    db = Session()

    print("=" * 60)
    print("TELANGANA 33-DISTRICT DEMO SEED")
    print("=" * 60)
    print(f"Database: {db_url}")
    print()

    # Ensure all tables exist
    Base.metadata.create_all(engine)
    print("[OK] Tables created/verified")

    # ── Step 1: Clean ALL data first (for idempotency) ──
    print()
    print("[CLEAN] Deleting ALL existing data...")

    # Delete in dependency order (respecting FK constraints)
    db.execute(delete(Notification))
    db.execute(delete(QueueToken))
    db.execute(delete(Payment))
    db.execute(delete(ProcurementRecord))
    db.execute(delete(BankDetails))
    db.execute(delete(Booking))
    db.execute(delete(Slot))
    db.execute(delete(CultivationRecord))
    db.execute(delete(LandRecord))
    db.execute(delete(Farmer))
    db.execute(delete(ProcurementCentre))
    db.commit()
    print("[OK] Transactional data cleaned")

    # ── Step 1.5: Delete ALL remaining data (including crops, districts, mandals, users)
    # This ensures idempotency — we recreate everything from scratch.
    print("[CLEAN] Deleting ALL remaining data for full fresh seed...")
    from app.models import AuditLog, Issue
    db.execute(delete(AuditLog))
    db.execute(delete(Issue))
    db.execute(delete(User))
    db.execute(delete(Crop))
    db.execute(delete(Mandal))
    db.execute(delete(District))
    db.commit()
    print("[OK] All data cleaned")

    # ── Step 2: Seed Crops (89 crops from MSP data) ──
    print()
    print("[CROPS] Seeding crop master data...")

    # Use the full MSP data from the app
    from app.config.msp import MSP_DATA

    crop_categories = {
        "Paddy": "Cereal", "Wheat": "Cereal", "Maize": "Cereal", "Barley": "Cereal",
        "Sorghum (Jowar)": "Cereal", "Pearl Millet (Bajra)": "Cereal",
        "Finger Millet (Ragi)": "Cereal", "Foxtail Millet": "Cereal",
        "Little Millet": "Cereal", "Kodo Millet": "Cereal",
        "Barnyard Millet": "Cereal", "Proso Millet": "Cereal",
        "Browntop Millet": "Cereal", "Oat": "Cereal", "Buckwheat": "Cereal",
        "Red Gram (Tur/Arhar)": "Pulse", "Black Gram (Urad)": "Pulse",
        "Green Gram (Moong)": "Pulse", "Bengal Gram (Chickpea/Chana)": "Pulse",
        "Lentil (Masoor)": "Pulse", "Field Pea": "Pulse", "Cowpea (Lobia)": "Pulse",
        "Horse Gram": "Pulse", "Moth Bean": "Pulse",
        "Soybean": "Oilseed", "Groundnut": "Oilseed", "Sunflower": "Oilseed",
        "Sesame": "Oilseed", "Mustard": "Oilseed", "Safflower": "Oilseed",
        "Castor": "Oilseed", "Linseed": "Oilseed", "Niger Seed": "Oilseed",
        "Cotton": "Cash Crop", "Sugarcane": "Cash Crop", "Tobacco": "Cash Crop",
        "Jute": "Fiber Crop", "Mesta": "Fiber Crop",
        "Tea": "Plantation", "Coffee": "Plantation", "Coconut": "Plantation",
        "Arecanut": "Plantation", "Rubber": "Plantation",
        "Pepper": "Spice", "Cardamom": "Spice", "Turmeric": "Spice",
        "Cumin": "Spice", "Coriander": "Spice", "Chilli": "Spice",
        "Fenugreek": "Spice", "Ginger": "Spice", "Garlic": "Spice", "Tamarind": "Spice",
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

    crop_count = 0
    for crop_name, msp_value in MSP_DATA.items():
        crop = Crop(
            crop_id=stable_uuid("crop", crop_name),
            crop_name=crop_name,
            crop_category=crop_categories.get(crop_name, "Other"),
            is_active=True,
            msp_per_quintal=Decimal(str(msp_value)),
            msp_effective_date=date(2025, 1, 1),
        )
        db.add(crop)
        crop_count += 1
    db.commit()
    print(f"[OK] {crop_count} crops seeded")

    # ── Step 3: Seed 33 Districts ──
    print()
    print("[DISTRICTS] Seeding 33 Telangana districts...")

    district_objs = {}
    for d in TELANGANA_DISTRICTS:
        dist = District(
            district_id=stable_uuid("district", d["name"]),
            name=d["name"],
            state="Telangana",
        )
        db.add(dist)
        district_objs[d["name"]] = dist
    db.commit()
    print(f"[OK] {len(TELANGANA_DISTRICTS)} districts seeded")

    # ── Step 4: Seed Mandals ──
    print()
    print("[MANDALS] Seeding mandals for all districts...")

    mandal_count = 0
    all_mandals = {}  # district_name -> [mandal_name, ...]
    for d in TELANGANA_DISTRICTS:
        district_name = d["name"]
        mandals = TELANGANA_MANDALS.get(district_name, [])
        if not mandals:
            mandals = [f"{district_name} Rural", f"{district_name} Town"]
        all_mandals[district_name] = mandals
        for m in mandals:
            mandal = Mandal(
                mandal_id=stable_uuid("mandal", f"{district_name}/{m}"),
                name=m,
                district_id=stable_uuid("district", district_name),
            )
            db.add(mandal)
            mandal_count += 1
    db.commit()
    print(f"[OK] {mandal_count} mandals seeded")

    # ── Step 5: Seed Procurement Centres ──
    print()
    print("[CENTRES] Seeding procurement centres...")

    all_centres = []  # list of dicts
    for idx, d in enumerate(TELANGANA_DISTRICTS):
        centres = generate_centre_data(
            d["name"], d["lat"], d["lon"],
            all_mandals[d["name"]], idx
        )
        all_centres.extend(centres)

    centre_objs = {}
    for c in all_centres:
        centre = ProcurementCentre(
            centre_id=stable_uuid("centre", c["code"]),
            centre_code=c["code"],
            centre_name=c["name"],
            agency=c["agency"],
            village=c["village"],
            mandal=c["mandal"],
            district=c["district"],
            latitude=Decimal(str(c["lat"])),
            longitude=Decimal(str(c["lon"])),
            capacity=c["capacity"],
            current_status=c["status"],
        )
        db.add(centre)
        centre_objs[c["code"]] = centre
    db.commit()
    print(f"[OK] {len(all_centres)} procurement centres seeded")

    # ── Step 6: Seed Slots ──
    print()
    print("[SLOTS] Seeding slots for each centre...")

    slot_objs_by_centre = {}  # centre_code -> [Slot obj]
    slot_count = 0
    for c in all_centres:
        centre_code = c["code"]
        slots = []
        # Create 5 days of slots, 3 time slots per day
        for day_offset in range(5):
            slot_date = date(2025, 10, 6 + day_offset)
            for hour in [9, 11, 14]:
                slot_id = stable_uuid("slot", f"{centre_code}-{slot_date}-{hour}")
                slot = Slot(
                    slot_id=slot_id,
                    centre_id=stable_uuid("centre", centre_code),
                    slot_date=slot_date,
                    start_time=time(hour, 0),
                    end_time=time(hour + 1, 0),
                    maximum_farmers=random.choice([20, 25, 30, 40]),
                    booked_farmers=0,
                    is_active=True,
                )
                db.add(slot)
                slots.append(slot)
                slot_count += 1
        slot_objs_by_centre[centre_code] = slots
    db.commit()
    print(f"[OK] {slot_count} slots seeded")

    # ── Step 7: Seed ~500 Farmers ──
    print()
    print("[FARMERS] Seeding ~500 farmers across 33 districts...")

    # Target: ~500 farmers, distributed ~15 per district
    # 33 * 15 = 495, add a few more to some districts
    farmer_targets = {}
    total_target = 500
    base_per_district = total_target // 33  # = 15
    remainder = total_target - (base_per_district * 33)  # = 5
    for d in TELANGANA_DISTRICTS:
        farmer_targets[d["name"]] = base_per_district
    # Distribute remainder to first few districts
    for i in range(remainder):
        farmer_targets[TELANGANA_DISTRICTS[i]["name"]] += 1

    all_farmers = []  # list of (Farmer obj, district_name)
    farmer_counter = 1
    used_mobiles = set()
    used_passbooks = set()

    random.seed(42)  # Reproducible

    for d in TELANGANA_DISTRICTS:
        district_name = d["name"]
        district_lat = d["lat"]
        district_lon = d["lon"]
        num_farmers = farmer_targets[district_name]
        mandals = all_mandals[district_name]

        for i in range(num_farmers):
            # Unique passbook number
            passbook = f"PB-TS-{farmer_counter:06d}"
            while passbook in used_passbooks:
                farmer_counter += 1
                passbook = f"PB-TS-{farmer_counter:06d}"
            used_passbooks.add(passbook)

            # Unique mobile
            mobile_base = 9000000000 + farmer_counter
            mobile = str(mobile_base)
            while mobile in used_mobiles:
                mobile_base += 1
                mobile = str(mobile_base)
            used_mobiles.add(mobile)

            first_name = random.choice(FARMER_FIRST_NAMES)
            last_name = random.choice(FARMER_LAST_NAMES)
            farmer_name = f"{first_name} {last_name}"

            mandal = random.choice(mandals)
            village = random.choice(VILLAGE_NAMES) + " " + str(random.randint(1, 50))

            # Spread coordinates within district
            lat = round(district_lat + random.uniform(-0.08, 0.08), 6)
            lon = round(district_lon + random.uniform(-0.08, 0.08), 6)

            land_acres = round(random.uniform(1.0, 15.0), 2)
            survey_num = f"{random.randint(10, 999)}-{random.choice('ABCDE')}{random.randint(1, 9)}"

            farmer = Farmer(
                farmer_id=stable_uuid("farmer", passbook),
                passbook_number=passbook,
                farmer_name=farmer_name,
                mobile_number=mobile,
                village=village,
                mandal=mandal,
                district=district_name,
                state="Telangana",
                survey_number=survey_num,
                total_land_acres=Decimal(str(land_acres)),
                pan_number=f"DEMO{farmer_counter:04d}X",
                latitude=Decimal(str(lat)),
                longitude=Decimal(str(lon)),
            )
            db.add(farmer)
            all_farmers.append((farmer, district_name))
            farmer_counter += 1

    db.commit()
    print(f"[OK] {len(all_farmers)} farmers seeded")

    # ── Step 8: Seed Land Records ──
    print()
    print("[LAND RECORDS] Seeding land records for all farmers...")

    land_count = 0
    for farmer, district_name in all_farmers:
        land = LandRecord(
            land_id=stable_uuid("land", farmer.passbook_number),
            farmer_id=farmer.farmer_id,
            survey_number=farmer.survey_number,
            land_area_acres=farmer.total_land_acres,
            land_type="AGRICULTURAL",
            ownership_status="ACTIVE",
        )
        db.add(land)
        land_count += 1
    db.commit()
    print(f"[OK] {land_count} land records seeded")

    # ── Step 9: Seed Cultivation Records ──
    print()
    print("[CULTIVATION] Seeding cultivation records...")

    cultivations = []  # (CultivationRecord obj, farmer, district_name)
    cultivations_by_farmer = {}  # farmer_id -> [CultivationRecord]
    cult_count = 0

    for farmer, district_name in all_farmers:
        num_crops = random.choice([1, 2, 2, 3])
        available_crops = random.sample(CULTIVATION_CROPS, min(num_crops, len(CULTIVATION_CROPS)))
        farmer_cults = []

        for crop_name, crop_category, msp in available_crops:
            season = random.choice(SEASONS)
            cultivated_area = round(random.uniform(0.5, float(farmer.total_land_acres) * 0.6), 2)
            cultivated_area = min(cultivated_area, float(farmer.total_land_acres))

            # Yield depends on crop type
            base_yield = {
                "Cereal": 20, "Pulse": 6, "Oilseed": 8, "Spice": 5,
                "Cash Crop": 12, "Vegetable": 15, "Fruit": 10,
            }.get(crop_category, 10)

            quantity_produced = round(cultivated_area * base_yield * random.uniform(0.7, 1.3), 2)
            quantity_to_sell = round(quantity_produced * random.uniform(0.5, 0.9), 2)

            cult_id = stable_uuid("cult", f"{farmer.passbook_number}-{crop_name}-{season}")
            cult = CultivationRecord(
                cultivation_id=cult_id,
                farmer_id=farmer.farmer_id,
                season=season,
                cultivated_area_acres=Decimal(str(cultivated_area)),
                crop=crop_name,
                quantity_produced_quintals=Decimal(str(quantity_produced)),
                quantity_to_sell_quintals=Decimal(str(quantity_to_sell)),
            )
            db.add(cult)
            cultivations.append((cult, farmer, district_name))
            farmer_cults.append(cult)
            cult_count += 1

        cultivations_by_farmer[farmer.farmer_id] = farmer_cults

    db.commit()
    print(f"[OK] {cult_count} cultivation records seeded")

    # ── Step 10: Seed Bank Details ──
    print()
    print("[BANK DETAILS] Seeding bank details for farmers...")

    bank_count = 0
    verification_statuses = ["VERIFIED", "VERIFIED", "VERIFIED", "PENDING_VERIFICATION", "PENDING_VERIFICATION", "REJECTED"]

    for farmer, district_name in all_farmers:
        account_number = f"{random.randint(1000000000, 9999999999)}"
        ifsc = random.choice(IFSC_CODES)
        v_status = random.choice(verification_statuses)

        bank = BankDetails(
            bank_detail_id=stable_uuid("bank", farmer.passbook_number),
            farmer_id=farmer.farmer_id,
            account_holder_name=farmer.farmer_name,
            account_number=account_number,
            ifsc_code=ifsc,
            verification_status=v_status,
        )
        db.add(bank)
        bank_count += 1
    db.commit()
    print(f"[OK] {bank_count} bank detail records seeded")

    # ── Step 11: Seed Bookings ──
    print()
    print("[BOOKINGS] Seeding bookings with realistic status distribution...")

    all_bookings = []  # (Booking obj, farmer, district_name)
    booking_counter = 1
    bookings_by_district = {}  # district_name -> [Booking]

    for farmer, district_name in all_farmers:
        farmer_cults = cultivations_by_farmer.get(farmer.farmer_id, [])
        if not farmer_cults:
            continue

        # ~70% of farmers get a booking
        if random.random() > 0.70:
            continue

        cult = random.choice(farmer_cults)

        # Pick a centre in the same district
        district_centres = [c for c in all_centres if c["district"] == district_name]
        if not district_centres:
            continue

        centre = random.choice(district_centres)
        centre_slots = slot_objs_by_centre.get(centre["code"], [])
        if not centre_slots:
            continue

        slot = random.choice(centre_slots)
        status = random.choice(BOOKING_STATUSES_DISTRIBUTION)

        booking_number = f"BK-TS-{booking_counter:06d}"
        quantity = min(
            float(cult.quantity_to_sell_quintals),
            round(random.uniform(5.0, 30.0), 2)
        )

        booking = Booking(
            booking_id=stable_uuid("booking", booking_number),
            booking_number=booking_number,
            farmer_id=farmer.farmer_id,
            cultivation_id=cult.cultivation_id,
            centre_id=stable_uuid("centre", centre["code"]),
            slot_id=slot.slot_id,
            quantity_to_sell_quintals=Decimal(str(max(1.0, quantity))),
            booking_status=status,
        )
        db.add(booking)
        all_bookings.append((booking, farmer, district_name))

        if district_name not in bookings_by_district:
            bookings_by_district[district_name] = []
        bookings_by_district[district_name].append(booking)

        booking_counter += 1

    db.commit()
    print(f"[OK] {len(all_bookings)} bookings seeded")

    # Update slot booked counts
    print("[SLOTS] Updating slot booked counts...")
    slot_booked = {}
    for booking, farmer, district_name in all_bookings:
        slot_key = str(booking.slot_id)
        slot_booked[slot_key] = slot_booked.get(slot_key, 0) + 1

    for slot_key, count in slot_booked.items():
        slot = db.get(Slot, uuid.UUID(slot_key))
        if slot:
            slot.booked_farmers = min(count, slot.maximum_farmers)
    db.commit()
    print("[OK] Slot booked counts updated")

    # ── Step 12: Seed Queue Tokens ──
    print()
    print("[QUEUE] Seeding queue tokens for active bookings...")

    queue_statuses = ["WAITING", "CALLED", "PROCESSING", "COMPLETED"]
    queue_count = 0
    token_counter = 1

    for booking, farmer, district_name in all_bookings:
        if booking.booking_status in ("ACCEPTED", "AUTO_ACCEPTED", "CONFIRMED", "COMPLETED"):
            queue_status = random.choice(queue_statuses)
            token = QueueToken(
                queue_id=stable_uuid("queue", booking.booking_number),
                booking_id=booking.booking_id,
                token_number=token_counter,
                queue_status=queue_status,
            )
            if queue_status in ("CALLED", "PROCESSING", "COMPLETED"):
                token.called_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
            if queue_status in ("PROCESSING", "COMPLETED"):
                token.processing_started_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 12))
            if queue_status == "COMPLETED":
                token.completed_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 6))

            db.add(token)
            queue_count += 1
            token_counter += 1
    db.commit()
    print(f"[OK] {queue_count} queue tokens seeded")

    # ── Step 13: Seed Procurement Records ──
    print()
    print("[PROCUREMENT] Seeding procurement records for completed bookings...")

    procurement_count = 0
    procurement_bookings = []

    for booking, farmer, district_name in all_bookings:
        if booking.booking_status in ("COMPLETED", "ACCEPTED", "AUTO_ACCEPTED"):
            # Get MSP for the crop
            cult = db.get(CultivationRecord, booking.cultivation_id)
            if not cult:
                continue

            msp = 0
            for crop_name, crop_category, msp_val in CULTIVATION_CROPS:
                if crop_name == cult.crop:
                    msp = msp_val
                    break
            if msp == 0:
                msp = 2500  # default

            submitted = float(booking.quantity_to_sell_quintals)
            # Some mismatch: 80-100% of submitted
            accepted = round(submitted * random.uniform(0.80, 1.0), 2)

            p_status = "COMPLETED" if booking.booking_status == "COMPLETED" else random.choice(["PENDING", "PROCESSING", "COMPLETED"])

            proc = ProcurementRecord(
                procurement_id=stable_uuid("procurement", booking.booking_number),
                booking_id=booking.booking_id,
                quantity_submitted_quintals=Decimal(str(submitted)),
                quantity_accepted_quintals=Decimal(str(accepted)),
                price_per_quintal=Decimal(str(msp)),
                procurement_status=p_status,
                remarks="Demo seed data" if abs(submitted - accepted) > 1.0 else None,
            )
            db.add(proc)
            procurement_count += 1
            procurement_bookings.append((proc, booking, farmer, district_name, accepted, msp))
    db.commit()
    print(f"[OK] {procurement_count} procurement records seeded")

    # ── Step 14: Seed Payments ──
    print()
    print("[PAYMENTS] Seeding payment records...")

    payment_count = 0
    payment_statuses = ["PENDING", "READY", "PROCESSING", "COMPLETED", "FAILED"]

    for proc, booking, farmer, district_name, accepted, msp in procurement_bookings:
        amount = round(accepted * msp, 2)
        p_status = random.choice(payment_statuses)

        payment = Payment(
            payment_id=stable_uuid("payment", booking.booking_number),
            procurement_id=proc.procurement_id,
            amount_payable=Decimal(str(amount)),
            payment_status=p_status,
            payment_direction="GOVERNMENT_TO_FARMER",
        )
        if p_status == "COMPLETED":
            payment.payment_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10))
        elif p_status in ("READY", "PROCESSING"):
            payment.processed_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 5))

        db.add(payment)
        payment_count += 1
    db.commit()
    print(f"[OK] {payment_count} payment records seeded")

    # ── Step 15: Seed 33 District Admins ──
    print()
    print("[ADMINS] Seeding 33 district admin accounts...")

    admin_password = "admin123"
    admin_count = 0

    for d in TELANGANA_DISTRICTS:
        district_name = d["name"]
        # Generate username from district name (lowercase, hyphens removed)
        username_slug = district_name.lower().replace(" ", "_").replace("-", "")
        username = f"admin_{username_slug}"

        admin_user = User(
            user_id=stable_uuid("admin", district_name),
            username=username,
            password_hash=hash_password(admin_password),
            role="DISTRICT_ADMIN",
            district=district_name,
            is_active=True,
        )
        db.add(admin_user)
        admin_count += 1
    db.commit()
    print(f"[OK] {admin_count} admin accounts seeded")

    # ── Step 16: Seed Notifications ──
    print()
    print("[NOTIFICATIONS] Seeding notifications...")

    notif_count = 0
    for booking, farmer, district_name in all_bookings:
        notif = Notification(
            notification_id=stable_uuid("notif", booking.booking_number),
            farmer_id=farmer.farmer_id,
            booking_id=booking.booking_id,
            notification_type="BOOKING_CONFIRMED",
            title="Booking Created",
            message=f"Your booking {booking.booking_number} has been created successfully.",
            is_read=random.choice([True, False]),
        )
        db.add(notif)
        notif_count += 1
    db.commit()
    print(f"[OK] {notif_count} notifications seeded")

    # ── Final Summary ──
    print()
    print("=" * 60)
    print("SEED COMPLETE — SUMMARY")
    print("=" * 60)

    # Verify counts
    district_actual = db.query(District).count()
    mandal_actual = db.query(Mandal).count()
    crop_actual = db.query(Crop).count()
    centre_actual = db.query(ProcurementCentre).count()
    slot_actual = db.query(Slot).count()
    farmer_actual = db.query(Farmer).count()
    land_actual = db.query(LandRecord).count()
    cult_actual = db.query(CultivationRecord).count()
    bank_actual = db.query(BankDetails).count()
    booking_actual = db.query(Booking).count()
    queue_actual = db.query(QueueToken).count()
    proc_actual = db.query(ProcurementRecord).count()
    payment_actual = db.query(Payment).count()
    admin_actual = db.query(User).filter(User.role == "DISTRICT_ADMIN").count()
    notif_actual = db.query(Notification).count()

    print(f"  Districts:       {district_actual}")
    print(f"  Mandals:         {mandal_actual}")
    print(f"  Crops:           {crop_actual}")
    print(f"  Centres:         {centre_actual}")
    print(f"  Slots:           {slot_actual}")
    print(f"  Farmers:         {farmer_actual}")
    print(f"  Land Records:    {land_actual}")
    print(f"  Cultivations:    {cult_actual}")
    print(f"  Bank Details:    {bank_actual}")
    print(f"  Bookings:        {booking_actual}")
    print(f"  Queue Tokens:    {queue_actual}")
    print(f"  Procurements:    {proc_actual}")
    print(f"  Payments:        {payment_actual}")
    print(f"  District Admins: {admin_actual}")
    print(f"  Notifications:   {notif_actual}")

    # Verify district distribution
    print()
    print("District-wise farmer distribution:")
    for d in TELANGANA_DISTRICTS:
        count = db.query(Farmer).filter(Farmer.district == d["name"]).count()
        admin_u = db.query(User).filter(
            User.role == "DISTRICT_ADMIN", User.district == d["name"]
        ).first()
        admin_str = f"  admin={admin_u.username}" if admin_u else "  NO ADMIN!"
        print(f"  {d['name']:30s} farmers={count:3d}{admin_str}")

    print()
    print("=" * 60)
    print("ADMIN LOGIN CREDENTIALS")
    print("=" * 60)
    print(f"  Password for all admins: {admin_password}")
    print()
    for d in TELANGANA_DISTRICTS:
        username_slug = d["name"].lower().replace(" ", "_").replace("-", "")
        print(f"  District: {d['name']:30s}  Username: admin_{username_slug}")

    print()
    print("=" * 60)
    print("FARMER CREDENTIALS (first 10)")
    print("=" * 60)
    sample_farmers = db.query(Farmer).order_by(Farmer.passbook_number).limit(10).all()
    for f in sample_farmers:
        print(f"  Passbook: {f.passbook_number}  Mobile: {f.mobile_number}  Name: {f.farmer_name}  District: {f.district}")

    print()
    print("Seed completed successfully!")
    print()

    db.close()


if __name__ == "__main__":
    main()
