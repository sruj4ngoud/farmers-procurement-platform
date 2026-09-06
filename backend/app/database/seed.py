"""Import denormalized CSV datasets into the Phase 2 PostgreSQL schema.

Run from backend/:

    python3 -m app.database.seed

Source files under data/ are never modified. Re-runs upsert on stable keys.
"""

from __future__ import annotations

import csv
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import (
    Booking,
    CultivationRecord,
    Farmer,
    LandRecord,
    Payment,
    ProcurementCentre,
    ProcurementRecord,
    QueueToken,
    Slot,
    User,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://farmer-procurement.local/seed")

CENTRE_STATUSES = {"ACTIVE", "LIMITED", "FULL", "INACTIVE"}
QUEUE_STATUSES = {"WAITING", "CALLED", "PROCESSING", "COMPLETED", "SKIPPED", "CANCELLED"}
PAYMENT_STATUSES = {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}

DEFAULT_SLOT_CAPACITY = 10
SLOT_DURATION = timedelta(minutes=30)


def stable_uuid(*parts: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, "|".join(parts))


def as_decimal(value: str | Decimal, places: str) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal(places))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid numeric value: {value!r}") from exc


def money(value: str | Decimal) -> Decimal:
    return as_decimal(value, "0.01")


def coord(value: str | Decimal) -> Decimal:
    return as_decimal(value, "0.000001")


def parse_slot_datetime(raw: str) -> datetime:
    return datetime.strptime(raw.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@dataclass
class ImportReport:
    farmers: int = 0
    land_records: int = 0
    cultivation_records: int = 0
    centres: int = 0
    slots: int = 0
    bookings: int = 0
    queue_tokens: int = 0
    procurements: int = 0
    payments: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def upsert_farmers(session: Session, rows: list[dict[str, str]], report: ImportReport) -> dict[str, uuid.UUID]:
    mapping: dict[str, uuid.UUID] = {}
    for row in rows:
        passbook = row["passbook_number"].strip()
        try:
            total_land = money(row["total_land_acres"])
            if total_land <= 0:
                report.error(f"Farmer {passbook}: total_land_acres must be > 0 ({total_land})")
                continue
            farmer = session.scalar(select(Farmer).where(Farmer.passbook_number == passbook))
            if farmer is None:
                farmer = Farmer(farmer_id=stable_uuid("farmer", passbook), passbook_number=passbook)
                session.add(farmer)
            farmer.farmer_name = row["farmer_name"].strip()
            farmer.mobile_number = row["mobile_number"].strip()
            farmer.village = row["village"].strip()
            farmer.mandal = row["mandal"].strip()
            farmer.district = row["district"].strip()
            farmer.survey_number = row["survey_number"].strip()
            farmer.total_land_acres = total_land
            farmer.latitude = coord(row["latitude"]) if row.get("latitude") else None
            farmer.longitude = coord(row["longitude"]) if row.get("longitude") else None
            session.flush()
            mapping[passbook] = farmer.farmer_id
            report.farmers += 1
        except Exception as exc:  # noqa: BLE001 - isolate a bad CSV row
            report.error(f"Farmer {passbook}: {exc}")
    return mapping


def upsert_land_records(
    session: Session,
    rows: list[dict[str, str]],
    farmer_ids: dict[str, uuid.UUID],
    report: ImportReport,
) -> None:
    for row in rows:
        passbook = row["passbook_number"].strip()
        farmer_id = farmer_ids.get(passbook)
        if farmer_id is None:
            continue
        survey = row["survey_number"].strip()
        land = session.scalar(
            select(LandRecord).where(
                LandRecord.farmer_id == farmer_id,
                LandRecord.survey_number == survey,
            )
        )
        if land is None:
            land = LandRecord(
                land_id=stable_uuid("land", passbook, survey),
                farmer_id=farmer_id,
                survey_number=survey,
            )
            session.add(land)
        land.land_area_acres = money(row["total_land_acres"])
        land.land_type = "AGRICULTURAL"
        land.ownership_status = "ACTIVE"
        report.land_records += 1


def upsert_cultivations(
    session: Session,
    rows: list[dict[str, str]],
    farmer_ids: dict[str, uuid.UUID],
    report: ImportReport,
) -> dict[str, uuid.UUID]:
    """Return CSV cultivation_id → internal cultivation_id."""
    mapping: dict[str, uuid.UUID] = {}
    farmers = {
        farmer.farmer_id: farmer
        for farmer in session.scalars(select(Farmer).where(Farmer.farmer_id.in_(farmer_ids.values()))).all()
    }
    for row in rows:
        csv_id = row["cultivation_id"].strip()
        passbook = row["passbook_number"].strip()
        farmer_id = farmer_ids.get(passbook)
        if farmer_id is None:
            report.error(f"Cultivation {csv_id}: unknown passbook {passbook}")
            continue
        farmer = farmers[farmer_id]
        try:
            area = money(row["cultivated_area_acres"])
            produced = money(row["quantity_produced_quintals"])
        except ValueError as exc:
            report.error(f"Cultivation {csv_id}: {exc}")
            continue
        if area <= 0:
            report.error(f"Cultivation {csv_id}: cultivated_area_acres must be > 0 ({area})")
            continue
        if produced <= 0:
            report.error(f"Cultivation {csv_id}: quantity_produced_quintals must be > 0 ({produced})")
            continue
        if area > farmer.total_land_acres:
            report.error(
                f"Cultivation {csv_id}: cultivated area {area} exceeds registered land "
                f"{farmer.total_land_acres} for {passbook}"
            )
            continue
        cultivation_id = stable_uuid("cultivation", csv_id)
        record = session.get(CultivationRecord, cultivation_id)
        if record is None:
            record = CultivationRecord(cultivation_id=cultivation_id, farmer_id=farmer_id)
            session.add(record)
        record.farmer_id = farmer_id
        record.season = row["season"].strip()
        record.cultivated_area_acres = area
        record.crop = row["crop"].strip()
        record.quantity_produced_quintals = produced
        record.quantity_to_sell_quintals = Decimal("0.00")
        mapping[csv_id] = cultivation_id
        report.cultivation_records += 1
    session.flush()
    return mapping


def upsert_centres(session: Session, rows: list[dict[str, str]], report: ImportReport) -> dict[str, uuid.UUID]:
    mapping: dict[str, uuid.UUID] = {}
    for row in rows:
        centre_code = (row.get("centre_id") or row.get("id") or "").strip()
        status = row["status"].strip().upper()
        if status not in CENTRE_STATUSES:
            report.error(f"Centre {centre_code}: invalid status {status}")
            continue
        try:
            capacity = int(row["capacity"])
            if capacity <= 0:
                report.error(f"Centre {centre_code}: capacity must be > 0")
                continue
            centre = session.scalar(
                select(ProcurementCentre).where(ProcurementCentre.centre_code == centre_code)
            )
            if centre is None:
                centre = ProcurementCentre(
                    centre_id=stable_uuid("centre", centre_code),
                    centre_code=centre_code,
                )
                session.add(centre)
            centre.centre_name = row["centre_name"].strip()
            centre.agency = row["agency"].strip()
            centre.village = row["village"].strip()
            centre.mandal = row["mandal"].strip()
            centre.district = row["district"].strip()
            centre.latitude = coord(row["latitude"]) if row.get("latitude") else None
            centre.longitude = coord(row["longitude"]) if row.get("longitude") else None
            centre.capacity = capacity
            centre.current_status = status
            session.flush()
            mapping[centre_code] = centre.centre_id
            report.centres += 1
        except Exception as exc:  # noqa: BLE001
            report.error(f"Centre {centre_code}: {exc}")
    return mapping


def _match_valid_bookings(
    session: Session,
    booking_rows: list[dict[str, str]],
    farmer_ids: dict[str, uuid.UUID],
    centre_ids: dict[str, uuid.UUID],
    cultivation_ids: dict[str, uuid.UUID],
    report: ImportReport,
) -> tuple[list[dict], dict[uuid.UUID, Decimal]]:
    """Validate bookings with explicit cultivation_id references.
    
    The booking CSV now contains cultivation_id and crop.
    We validate but no longer need to infer which cultivation owns each booking.
    """
    # Build lookup: cultivation_id -> CultivationRecord for validation
    cultivations: dict[uuid.UUID, CultivationRecord] = {}
    for record in session.scalars(select(CultivationRecord)).all():
        cultivations[record.cultivation_id] = record

    remaining: dict[uuid.UUID, Decimal] = {
        record.cultivation_id: record.quantity_produced_quintals
        for record in cultivations.values()
    }
    allocated: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0.00"))
    accepted: list[dict] = []

    for row in sorted(booking_rows, key=lambda item: item["booking_id"]):
        csv_booking_id = row["booking_id"].strip()
        passbook = row["passbook_number"].strip()
        csv_cultivation_id = row.get("cultivation_id", "").strip()
        csv_crop = row.get("crop", "").strip()
        centre_code = row["centre_id"].strip()
        
        farmer_id = farmer_ids.get(passbook)
        centre_uuid = centre_ids.get(centre_code)
        cultivation_uuid = cultivation_ids.get(csv_cultivation_id)
        
        if farmer_id is None:
            report.error(f"Booking {csv_booking_id}: unknown passbook {passbook}")
            continue
        if centre_uuid is None:
            report.error(f"Booking {csv_booking_id}: unknown centre {centre_code}")
            continue
        if cultivation_uuid is None:
            report.error(f"Booking {csv_booking_id}: unknown cultivation {csv_cultivation_id}")
            continue
        
        cultivation = cultivations.get(cultivation_uuid)
        if cultivation is None:
            report.error(f"Booking {csv_booking_id}: cultivation {csv_cultivation_id} not in database")
            continue
        
        # Validate farmer owns this cultivation
        if cultivation.farmer_id != farmer_id:
            report.error(
                f"Booking {csv_booking_id}: cultivation {csv_cultivation_id} does not belong to farmer {passbook}"
            )
            continue
        
        # Validate crop matches
        if cultivation.crop.strip() != csv_crop:
            report.error(
                f"Booking {csv_booking_id}: crop mismatch. CSV={csv_crop}, cultivation={cultivation.crop}"
            )
            continue
        
        try:
            slot_dt = parse_slot_datetime(row["slot_datetime"])
            qty = money(row["quantity_to_sell_quintals"])
            token_number = int(row["token_number"])
        except (ValueError, InvalidOperation) as exc:
            report.error(f"Booking {csv_booking_id}: {exc}")
            continue
        
        if qty <= 0:
            report.error(f"Booking {csv_booking_id}: quantity_to_sell must be > 0")
            continue
        
        # Validate quantity does not exceed remaining
        if qty > remaining[cultivation_uuid]:
            report.error(
                f"Booking {csv_booking_id}: quantity {qty} exceeds remaining production {remaining[cultivation_uuid]} "
                f"for {csv_crop} (cultivation {csv_cultivation_id})"
            )
            continue
        
        remaining[cultivation_uuid] -= qty
        allocated[cultivation_uuid] += qty
        
        queue_status = row["queue_status"].strip().upper()
        if queue_status not in QUEUE_STATUSES:
            report.warn(
                f"Booking {csv_booking_id}: unknown queue_status {queue_status}, defaulting to WAITING"
            )
            queue_status = "WAITING"
        
        accepted.append(
            {
                "csv_booking_id": csv_booking_id,
                "farmer_id": farmer_id,
                "centre_code": centre_code,
                "centre_uuid": centre_uuid,
                "slot_dt": slot_dt,
                "qty": qty,
                "token_number": token_number,
                "cultivation_id": cultivation_uuid,
                "queue_status": queue_status,
                "booking_status": "COMPLETED" if queue_status == "COMPLETED" else "CONFIRMED",
            }
        )
    return accepted, allocated


def build_slots_and_bookings(
    session: Session,
    booking_rows: list[dict[str, str]],
    farmer_ids: dict[str, uuid.UUID],
    centre_ids: dict[str, uuid.UUID],
    cultivation_ids: dict[str, uuid.UUID],
    report: ImportReport,
) -> dict[str, uuid.UUID]:
    accepted, allocated = _match_valid_bookings(
        session, booking_rows, farmer_ids, centre_ids, cultivation_ids, report
    )

    slot_groups: dict[tuple[uuid.UUID, str, datetime], list[dict]] = defaultdict(list)
    for item in accepted:
        slot_groups[(item["centre_uuid"], item["centre_code"], item["slot_dt"])].append(item)

    slot_ids: dict[tuple[uuid.UUID, datetime], uuid.UUID] = {}
    for (centre_uuid, centre_code, slot_dt), group in sorted(
        slot_groups.items(), key=lambda item: (item[0][1], item[0][2])
    ):
        if len(group) > DEFAULT_SLOT_CAPACITY:
            report.warn(
                f"Slot {centre_code} {slot_dt}: {len(group)} bookings exceed default "
                f"capacity {DEFAULT_SLOT_CAPACITY}; maximum_farmers raised to fit"
            )
        slot = session.scalar(
            select(Slot).where(
                Slot.centre_id == centre_uuid,
                Slot.slot_date == slot_dt.date(),
                Slot.start_time == slot_dt.time(),
            )
        )
        if slot is None:
            slot = Slot(
                slot_id=stable_uuid("slot", centre_code, slot_dt.isoformat()),
                centre_id=centre_uuid,
                slot_date=slot_dt.date(),
                start_time=slot_dt.time(),
            )
            session.add(slot)
        slot.end_time = (slot_dt + SLOT_DURATION).time()
        slot.maximum_farmers = max(DEFAULT_SLOT_CAPACITY, len(group))
        slot.booked_farmers = len(group)
        slot.is_active = True
        session.flush()
        slot_ids[(centre_uuid, slot_dt)] = slot.slot_id
        report.slots += 1

    booking_ids: dict[str, uuid.UUID] = {}
    for item in accepted:
        slot_id = slot_ids[(item["centre_uuid"], item["slot_dt"])]
        booking = session.scalar(
            select(Booking).where(Booking.booking_number == item["csv_booking_id"])
        )
        if booking is None:
            booking = Booking(
                booking_id=stable_uuid("booking", item["csv_booking_id"]),
                booking_number=item["csv_booking_id"],
            )
            session.add(booking)
        booking.farmer_id = item["farmer_id"]
        booking.cultivation_id = item["cultivation_id"]
        booking.centre_id = item["centre_uuid"]
        booking.slot_id = slot_id
        booking.quantity_to_sell_quintals = item["qty"]
        booking.booking_status = item["booking_status"]
        session.flush()
        booking_ids[item["csv_booking_id"]] = booking.booking_id
        report.bookings += 1
        _upsert_queue_token(
            session,
            booking=booking,
            token_number=item["token_number"],
            queue_status=item["queue_status"],
            slot_dt=item["slot_dt"],
            report=report,
        )

    for cultivation_id, total_sell in allocated.items():
        record = session.get(CultivationRecord, cultivation_id)
        if record is not None:
            record.quantity_to_sell_quintals = total_sell

    used_slot_ids = set(slot_ids.values())
    unused = session.scalars(select(Slot).where(Slot.slot_id.not_in(used_slot_ids))).all()
    for slot in unused:
        if session.scalar(select(Booking).where(Booking.slot_id == slot.slot_id).limit(1)) is None:
            session.delete(slot)

    session.flush()
    return booking_ids


def _upsert_queue_token(
    session: Session,
    booking: Booking,
    token_number: int,
    queue_status: str,
    slot_dt: datetime,
    report: ImportReport,
) -> None:
    token = session.scalar(select(QueueToken).where(QueueToken.booking_id == booking.booking_id))
    if token is None:
        token = QueueToken(
            queue_id=stable_uuid("queue", booking.booking_number),
            booking_id=booking.booking_id,
        )
        session.add(token)
    token.token_number = token_number
    token.queue_status = queue_status
    token.called_at = None
    token.processing_started_at = None
    token.completed_at = None
    if queue_status == "PROCESSING":
        token.processing_started_at = slot_dt
    elif queue_status == "COMPLETED":
        token.processing_started_at = slot_dt
        token.completed_at = slot_dt + SLOT_DURATION
    report.queue_tokens += 1


def upsert_procurement_and_payments(
    session: Session,
    rows: list[dict[str, str]],
    booking_ids: dict[str, uuid.UUID],
    report: ImportReport,
) -> None:
    for row in rows:
        csv_procurement_id = row["procurement_id"].strip()
        csv_booking_id = row["booking_id"].strip()
        booking_uuid = booking_ids.get(csv_booking_id)
        if booking_uuid is None:
            report.error(
                f"Procurement {csv_procurement_id}: booking {csv_booking_id} was not imported"
            )
            continue
        try:
            submitted = money(row["quantity_submitted_quintals"])
            accepted = money(row["quantity_accepted_quintals"])
            price = money(row["price_per_quintal"])
            amount = money(row["amount_payable"])
        except ValueError as exc:
            report.error(f"Procurement {csv_procurement_id}: {exc}")
            continue
        if accepted > submitted:
            report.error(
                f"Procurement {csv_procurement_id}: accepted {accepted} exceeds submitted {submitted}"
            )
            continue
        if submitted <= 0 or price <= 0:
            report.error(f"Procurement {csv_procurement_id}: submitted and price must be > 0")
            continue

        payment_status = row["payment_status"].strip().upper()
        if payment_status not in PAYMENT_STATUSES:
            report.error(f"Payment for {csv_procurement_id}: invalid status {payment_status}")
            continue

        record = session.scalar(
            select(ProcurementRecord).where(ProcurementRecord.booking_id == booking_uuid)
        )
        if record is None:
            record = ProcurementRecord(
                procurement_id=stable_uuid("procurement", csv_procurement_id),
                booking_id=booking_uuid,
            )
            session.add(record)
        record.quantity_submitted_quintals = submitted
        record.quantity_accepted_quintals = accepted
        record.price_per_quintal = price
        record.procurement_status = "COMPLETED"
        record.verified_by = None
        record.remarks = "Imported from mock procurement dataset"
        session.flush()
        report.procurements += 1

        payment = session.scalar(select(Payment).where(Payment.procurement_id == record.procurement_id))
        if payment is None:
            payment = Payment(
                payment_id=stable_uuid("payment", csv_procurement_id),
                procurement_id=record.procurement_id,
            )
            session.add(payment)
        payment.amount_payable = amount
        payment.payment_status = payment_status
        payment.transaction_reference = f"MOCK-TXN-{csv_procurement_id.replace('PRC', '')}"
        booking = session.get(Booking, booking_uuid)
        slot = session.get(Slot, booking.slot_id) if booking else None
        payment_dt = None
        if slot is not None:
            payment_dt = datetime.combine(slot.slot_date, slot.start_time, tzinfo=timezone.utc) + timedelta(days=1)
        if payment_status == "COMPLETED":
            payment.payment_date = payment_dt
            payment.failure_reason = None
        elif payment_status == "FAILED":
            payment.payment_date = None
            payment.failure_reason = "Mock payment failure"
        else:
            payment.payment_date = None
            payment.failure_reason = None
        report.payments += 1


def link_centre_staff(session: Session, report: ImportReport) -> None:
    staff = session.scalar(select(User).where(User.username == "centre.staff"))
    if staff is None:
        report.warn("centre.staff user not found; skip centre assignment")
        return
    centre = session.scalar(
        select(ProcurementCentre)
        .where(ProcurementCentre.current_status == "ACTIVE")
        .order_by(ProcurementCentre.centre_code)
        .limit(1)
    )
    if centre is None:
        report.warn("No ACTIVE centre available to assign to centre.staff")
        return
    staff.centre_id = centre.centre_id
    report.warn(f"Assigned centre.staff to {centre.centre_code} ({centre.centre_name})")


def print_report(report: ImportReport) -> None:
    print("========================================")
    print("FARMER PROCUREMENT DATA IMPORT")
    print("========================================")
    print(f"Farmers imported: {report.farmers}")
    print(f"Land records imported: {report.land_records}")
    print(f"Cultivation records imported: {report.cultivation_records}")
    print(f"Centres imported: {report.centres}")
    print(f"Slots created: {report.slots}")
    print(f"Bookings imported: {report.bookings}")
    print(f"Queue tokens imported: {report.queue_tokens}")
    print(f"Procurements imported: {report.procurements}")
    print(f"Payments imported: {report.payments}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Errors: {len(report.errors)}")
    if report.warnings:
        print("\n--- Warnings ---")
        for message in report.warnings:
            print(f"  WARN: {message}")
    if report.errors:
        print("\n--- Errors / skipped records ---")
        for message in report.errors:
            print(f"  ERROR: {message}")
    print("\nIMPORT COMPLETED")
    print("========================================")


def run_import() -> ImportReport:
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    farmer_rows = read_csv("farmers.csv")
    cultivation_rows = read_csv("cultivation_records.csv")
    centre_rows = read_csv("procurement_centres.csv")
    booking_rows = read_csv("bookings_queue.csv")
    payment_rows = read_csv("procurement_payments.csv")

    report = ImportReport()
    with SessionLocal() as session:
        with session.begin():
            farmer_ids = upsert_farmers(session, farmer_rows, report)
            upsert_land_records(session, farmer_rows, farmer_ids, report)
            cultivation_ids = upsert_cultivations(session, cultivation_rows, farmer_ids, report)
            centre_ids = upsert_centres(session, centre_rows, report)
            booking_ids = build_slots_and_bookings(
                session, booking_rows, farmer_ids, centre_ids, cultivation_ids, report
            )
            upsert_procurement_and_payments(session, payment_rows, booking_ids, report)
            link_centre_staff(session, report)
    return report


def main() -> None:
    report = run_import()
    print_report(report)


if __name__ == "__main__":
    main()
