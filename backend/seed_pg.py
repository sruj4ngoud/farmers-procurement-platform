"""Seed PostgreSQL with demo farmer data for the Farmer Procurement Platform.

Run from backend/:
    python seed_pg.py
"""
import sys
import os
import uuid
from decimal import Decimal
from datetime import date, time

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker
from app.database.connection import engine
from app.models import (
    Farmer, LandRecord, CultivationRecord, ProcurementCentre, Slot,
    Booking, QueueToken, ProcurementRecord, Payment, User
)

from app.config.settings import settings

Session = sessionmaker(bind=engine)
db = Session()

def uid(name):
    return uuid.uuid5(uuid.NAMESPACE_URL, f"demo-seed-{name}")

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
for day_offset in range(3):
    slot_date = date(2025, 10, 1 + day_offset)
    for hour in [9, 10, 11, 14, 15]:
        for c in centres_data:
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
db.close()

print("Demo data seeded successfully to PostgreSQL!")
print()
print("=" * 60)
print("DEMO LOGIN CREDENTIALS")
print("=" * 60)
print()
print("The app uses OTP-based login. Enter the Passbook Number")
print("and Mobile Number below, then use the OTP from the response.")
print("(OTP_DEMO_MODE is on, so the OTP is returned in the API response)")
print()
for f in farmers_data:
    print(f"  Farmer: {f['name']}")
    print(f"    Passbook: {f['passbook']}  |  Mobile: {f['mobile']}")
    print()
print("=" * 60)
print("HOW TO LOGIN:")
print("=" * 60)
print("1. Open http://localhost:5173/")
print("2. Enter any Passbook Number + Mobile Number from above")
print("3. Request OTP -> the OTP will be returned in the response")
print("4. Enter the OTP to get your JWT token and log in")
