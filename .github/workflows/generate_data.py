import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# -----------------------------
# SAMPLE MASTER DATA
# -----------------------------

first_names = [
    "Ramesh", "Suresh", "Ravi", "Mahesh", "Kiran",
    "Anil", "Rajesh", "Vijay", "Srikanth", "Prakash",
    "Naveen", "Mohan", "Arjun", "Naresh", "Venkat"
]

last_names = [
    "Kumar", "Reddy", "Rao", "Naidu", "Yadav",
    "Patel", "Sharma", "Verma", "Goud", "Varma"
]

villages = [
    ("Kondapur", "Serilingampally", "Hyderabad", 17.4580, 78.3560),
    ("Gachibowli", "Serilingampally", "Hyderabad", 17.4401, 78.3489),
    ("Miyapur", "Serilingampally", "Hyderabad", 17.4960, 78.3570),
    ("Bachupally", "Quthbullapur", "Medchal", 17.5460, 78.3670),
    ("Shamirpet", "Shamirpet", "Medchal", 17.5947, 78.5650),
    ("Ibrahimpatnam", "Ibrahimpatnam", "Rangareddy", 17.1900, 78.5720),
    ("Shadnagar", "Shadnagar", "Rangareddy", 17.0700, 78.2050),
    ("Nalgonda", "Nalgonda", "Nalgonda", 17.0500, 79.2670),
    ("Suryapet", "Suryapet", "Suryapet", 17.1400, 79.6200),
    ("Kodad", "Kodad", "Suryapet", 16.9980, 79.9650)
]

crops = [
    ("Paddy", 20, 30),
    ("Maize", 15, 25),
    ("Cotton", 4, 8),
    ("Soybean", 5, 10),
    ("Groundnut", 6, 12)
]

agencies = ["PACS", "IKP", "FPO", "MEPMA"]

statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "LIMITED", "FULL", "INACTIVE"]


# -----------------------------
# CREATE DATA FOLDER
# -----------------------------

import os
os.makedirs("data", exist_ok=True)


# -----------------------------
# 1. FARMERS
# -----------------------------

farmers = []

for i in range(1, 1001):

    village = random.choice(villages)

    village_name = village[0]
    mandal = village[1]
    district = village[2]
    base_lat = village[3]
    base_lon = village[4]

    name = random.choice(first_names) + " " + random.choice(last_names)

    mobile = "9" + "".join(
        str(random.randint(0, 9)) for _ in range(9)
    )

    total_land = round(random.uniform(1, 10), 2)

    latitude = round(
        base_lat + random.uniform(-0.01, 0.01), 6
    )

    longitude = round(
        base_lon + random.uniform(-0.01, 0.01), 6
    )

    farmers.append([
        f"PPB{i:06d}",
        name,
        mobile,
        village_name,
        mandal,
        district,
        f"SY{i:06d}",
        total_land,
        latitude,
        longitude
    ])


with open("data/farmers.csv", "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "passbook_number",
        "farmer_name",
        "mobile_number",
        "village",
        "mandal",
        "district",
        "survey_number",
        "total_land_acres",
        "latitude",
        "longitude"
    ])

    writer.writerows(farmers)


# -----------------------------
# 2. CULTIVATION RECORDS
# -----------------------------

cultivation_records = []

cultivation_id = 1

for farmer in farmers:

    passbook = farmer[0]
    total_land = float(farmer[7])

    # 1 or 2 crop records
    number_of_crops = random.choice([1, 1, 1, 2])

    remaining_land = total_land

    for _ in range(number_of_crops):

        if remaining_land <= 0.25:
            break

        cultivated_area = round(
            random.uniform(0.5, remaining_land),
            2
        )

        crop = random.choice(crops)

        crop_name = crop[0]
        min_yield = crop[1]
        max_yield = crop[2]

        production_per_acre = random.uniform(
            min_yield,
            max_yield
        )

        quantity_produced = round(
            cultivated_area * production_per_acre,
            2
        )

        cultivation_records.append([
            f"CUL{cultivation_id:06d}",
            passbook,
            "2026-KHARIF",
            cultivated_area,
            crop_name,
            quantity_produced
        ])

        cultivation_id += 1

        remaining_land = round(
            remaining_land - cultivated_area,
            2
        )


with open("data/cultivation_records.csv", "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "cultivation_id",
        "passbook_number",
        "season",
        "cultivated_area_acres",
        "crop",
        "quantity_produced_quintals"
    ])

    writer.writerows(cultivation_records)


# -----------------------------
# 3. PROCUREMENT CENTRES
# -----------------------------

procurement_centres = []

centre_id = 1

for village in villages:

    village_name = village[0]
    mandal = village[1]
    district = village[2]
    base_lat = village[3]
    base_lon = village[4]

    # 5 centres per location
    for j in range(5):

        latitude = round(
            base_lat + random.uniform(-0.015, 0.015),
            6
        )

        longitude = round(
            base_lon + random.uniform(-0.015, 0.015),
            6
        )

        capacity = random.choice([
            300, 400, 500, 600, 700, 1000
        ])

        status = random.choice(statuses)

        procurement_centres.append([
            f"PPC{centre_id:03d}",
            f"{village_name} Procurement Centre {j + 1}",
            random.choice(agencies),
            village_name,
            mandal,
            district,
            latitude,
            longitude,
            capacity,
            status
        ])

        centre_id += 1


with open("data/procurement_centres.csv", "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "centre_id",
        "centre_name",
        "agency",
        "village",
        "mandal",
        "district",
        "latitude",
        "longitude",
        "capacity",
        "status"
    ])

    writer.writerows(procurement_centres)


# -----------------------------
# 4. BOOKINGS + QUEUE
# -----------------------------

bookings = []

booking_id = 1

start_date = datetime(2026, 9, 1)

for i in range(500):

    cultivation = random.choice(cultivation_records)

    passbook = cultivation[1]
    produced = float(cultivation[5])

    quantity_to_sell = round(
        random.uniform(1, produced),
        2
    )

    centre = random.choice(procurement_centres)

    booking_date = start_date + timedelta(
        days=random.randint(0, 30)
    )

    hour = random.choice([
        9, 10, 11, 12, 14, 15, 16
    ])

    slot_time = booking_date.replace(
        hour=hour,
        minute=0
    )

    queue_status = random.choice([
        "WAITING",
        "WAITING",
        "PROCESSING",
        "COMPLETED"
    ])

    token = random.randint(1, 150)

    bookings.append([
        f"BKG{booking_id:06d}",
        passbook,
        centre[0],
        slot_time.strftime("%Y-%m-%d %H:%M:%S"),
        token,
        quantity_to_sell,
        queue_status
    ])

    booking_id += 1


with open("data/bookings_queue.csv", "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "booking_id",
        "passbook_number",
        "centre_id",
        "slot_datetime",
        "token_number",
        "quantity_to_sell_quintals",
        "queue_status"
    ])

    writer.writerows(bookings)


# -----------------------------
# 5. PROCUREMENT + PAYMENT
# -----------------------------

procurement_payments = []

procurement_id = 1

for booking in bookings:

    if booking[6] != "COMPLETED":
        continue

    quantity_submitted = float(booking[5])

    # Usually accepted quantity is same or slightly lower
    quantity_accepted = round(
        quantity_submitted * random.uniform(0.95, 1.0),
        2
    )

    # Example procurement rate
    price_per_quintal = random.choice([
        2200,
        2300,
        2400,
        2500
    ])

    amount_payable = round(
        quantity_accepted * price_per_quintal,
        2
    )

    payment_status = random.choice([
        "PROCESSING",
        "COMPLETED",
        "COMPLETED",
        "COMPLETED",
        "FAILED"
    ])

    procurement_payments.append([
        f"PRC{procurement_id:06d}",
        booking[0],
        quantity_submitted,
        quantity_accepted,
        price_per_quintal,
        amount_payable,
        payment_status
    ])

    procurement_id += 1


with open("data/procurement_payments.csv", "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "procurement_id",
        "booking_id",
        "quantity_submitted_quintals",
        "quantity_accepted_quintals",
        "price_per_quintal",
        "amount_payable",
        "payment_status"
    ])

    writer.writerows(procurement_payments)


# -----------------------------
# DONE
# -----------------------------

print("===================================")
print("DATA GENERATION COMPLETED")
print("===================================")

print("Farmers:", len(farmers))
print("Cultivation records:", len(cultivation_records))
print("Procurement centres:", len(procurement_centres))
print("Bookings:", len(bookings))
print("Procurement records:", len(procurement_payments))

print("\nFiles created inside data/:")
print("1. farmers.csv")
print("2. cultivation_records.csv")
print("3. procurement_centres.csv")
print("4. bookings_queue.csv")
print("5. procurement_payments.csv")