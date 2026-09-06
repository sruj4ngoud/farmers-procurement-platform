"""Validate generated CSV data for consistency before importing to database."""

import csv
from collections import defaultdict
from decimal import Decimal

def load_csv(filename):
    """Load CSV file into list of dicts."""
    with open(f"data/{filename}", "r", newline="") as f:
        return list(csv.DictReader(f))

def validate_data():
    """Run all validation checks."""
    print("=" * 60)
    print("VALIDATING GENERATED DATA")
    print("=" * 60)
    
    farmers = load_csv("farmers.csv")
    cultivations = load_csv("cultivation_records.csv")
    centres = load_csv("procurement_centres.csv")
    bookings = load_csv("bookings_queue.csv")
    procurements = load_csv("procurement_payments.csv")
    
    errors = []
    warnings = []
    
    # === STEP 1: Farmer validation ===
    print("\n1. Validating farmers...")
    farmer_ids = set(f["passbook_number"] for f in farmers)
    print(f"   Total farmers: {len(farmers)}")
    print(f"   Unique farmers: {len(farmer_ids)}")
    if len(farmer_ids) != len(farmers):
        errors.append(f"Duplicate farmer IDs found: {len(farmers) - len(farmer_ids)}")
    
    # === STEP 2: Cultivation validation ===
    print("\n2. Validating cultivations...")
    cultivation_ids = set(c["cultivation_id"] for c in cultivations)
    print(f"   Total cultivations: {len(cultivations)}")
    print(f"   Unique cultivations: {len(cultivation_ids)}")
    
    if len(cultivation_ids) != len(cultivations):
        errors.append(f"Duplicate cultivation IDs found: {len(cultivations) - len(cultivation_ids)}")
    
    cultivations_by_farmer = defaultdict(list)
    for cult in cultivations:
        passbook = cult["passbook_number"]
        if passbook not in farmer_ids:
            errors.append(f"Cultivation {cult['cultivation_id']}: unknown farmer {passbook}")
        cultivations_by_farmer[passbook].append(cult)
    
    print(f"   Farmers with cultivations: {len(cultivations_by_farmer)}")
    
    # === STEP 3: Procurement centres validation ===
    print("\n3. Validating procurement centres...")
    centre_ids = set(c["centre_id"] for c in centres)
    print(f"   Total centres: {len(centres)}")
    print(f"   Unique centres: {len(centre_ids)}")
    if len(centre_ids) != len(centres):
        errors.append(f"Duplicate centre IDs found: {len(centres) - len(centre_ids)}")
    
    # === STEP 4: Booking validation ===
    print("\n4. Validating bookings...")
    booking_ids = set()
    quantity_by_cultivation = defaultdict(Decimal)
    
    for bkg in bookings:
        bkg_id = bkg["booking_id"]
        
        # Check for duplicates
        if bkg_id in booking_ids:
            errors.append(f"Duplicate booking ID: {bkg_id}")
        booking_ids.add(bkg_id)
        
        # Check farmer exists
        passbook = bkg["passbook_number"]
        if passbook not in farmer_ids:
            errors.append(f"Booking {bkg_id}: unknown farmer {passbook}")
            continue
        
        # Check cultivation exists
        cult_id = bkg["cultivation_id"]
        if cult_id not in cultivation_ids:
            errors.append(f"Booking {bkg_id}: unknown cultivation {cult_id}")
            continue
        
        # Check centre exists
        centre_code = bkg["centre_id"]
        if centre_code not in centre_ids:
            errors.append(f"Booking {bkg_id}: unknown centre {centre_code}")
            continue
        
        # Find cultivation record
        cultivation = next((c for c in cultivations if c["cultivation_id"] == cult_id), None)
        if not cultivation:
            errors.append(f"Booking {bkg_id}: cultivation {cult_id} not found in data")
            continue
        
        # Check farmer owns cultivation
        if cultivation["passbook_number"] != passbook:
            errors.append(
                f"Booking {bkg_id}: cultivation {cult_id} belongs to {cultivation['passbook_number']}, "
                f"not {passbook}"
            )
            continue
        
        # Check crop matches
        csv_crop = bkg["crop"].strip()
        cult_crop = cultivation["crop"].strip()
        if csv_crop != cult_crop:
            errors.append(
                f"Booking {bkg_id}: crop mismatch. CSV={csv_crop}, cultivation={cult_crop}"
            )
            continue
        
        # Check quantity
        try:
            qty = Decimal(str(bkg["quantity_to_sell_quintals"]))
            produced = Decimal(str(cultivation["quantity_produced_quintals"]))
            
            if qty <= 0:
                errors.append(f"Booking {bkg_id}: quantity must be > 0, got {qty}")
                continue
            
            quantity_by_cultivation[cult_id] += qty
            
            if quantity_by_cultivation[cult_id] > produced:
                errors.append(
                    f"Booking {bkg_id}: cumulative quantity {quantity_by_cultivation[cult_id]} "
                    f"exceeds production {produced} for cultivation {cult_id}"
                )
        except Exception as e:
            errors.append(f"Booking {bkg_id}: invalid quantity {bkg['quantity_to_sell_quintals']}: {e}")
    
    print(f"   Total bookings: {len(bookings)}")
    print(f"   Unique booking IDs: {len(booking_ids)}")
    
    # Verify cumulative quantities per cultivation
    for cult_id, total_qty in quantity_by_cultivation.items():
        cult = next((c for c in cultivations if c["cultivation_id"] == cult_id), None)
        if cult:
            produced = Decimal(str(cult["quantity_produced_quintals"]))
            if total_qty > produced:
                errors.append(
                    f"Cultivation {cult_id}: total bookings {total_qty} "
                    f"exceed production {produced}"
                )
    
    # === STEP 5: Procurement validation ===
    print("\n5. Validating procurements...")
    booking_ids_set = set(b["booking_id"] for b in bookings)
    
    for proc in procurements:
        proc_id = proc["procurement_id"]
        bkg_id = proc["booking_id"]
        
        # Check booking exists
        if bkg_id not in booking_ids_set:
            errors.append(f"Procurement {proc_id}: unknown booking {bkg_id}")
            continue
        
        try:
            submitted = Decimal(str(proc["quantity_submitted_quintals"]))
            accepted = Decimal(str(proc["quantity_accepted_quintals"]))
            price = Decimal(str(proc["price_per_quintal"]))
            amount = Decimal(str(proc["amount_payable"]))
            
            # Check submitted > 0
            if submitted <= 0:
                errors.append(f"Procurement {proc_id}: submitted quantity must be > 0")
                continue
            
            # Check accepted <= submitted
            if accepted > submitted:
                errors.append(
                    f"Procurement {proc_id}: accepted {accepted} > submitted {submitted}"
                )
                continue
            
            # Check amount calculation
            expected_amount = accepted * price
            if amount != expected_amount:
                errors.append(
                    f"Procurement {proc_id}: amount mismatch. Expected {expected_amount}, got {amount}"
                )
        except Exception as e:
            errors.append(f"Procurement {proc_id}: invalid data: {e}")
    
    print(f"   Total procurements: {len(procurements)}")
    
    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Farmers: {len(farmers)}")
    print(f"Cultivations: {len(cultivations)}")
    print(f"Centres: {len(centres)}")
    print(f"Bookings: {len(bookings)}")
    print(f"Procurements: {len(procurements)}")
    print(f"\nErrors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    
    if errors:
        print("\n--- ERRORS ---")
        for i, err in enumerate(errors, 1):
            print(f"{i:3d}. {err}")
    
    if warnings:
        print("\n--- WARNINGS ---")
        for i, warn in enumerate(warnings, 1):
            print(f"{i:3d}. {warn}")
    
    print("\n" + "=" * 60)
    if errors:
        print("VALIDATION FAILED")
        return False
    else:
        print("VALIDATION PASSED")
        return True

if __name__ == "__main__":
    success = validate_data()
    exit(0 if success else 1)
