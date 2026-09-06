-- Complete PostgreSQL schema for farmer_procurement.
-- Preferred apply path: Alembic (backend/migrations).
-- Manual apply: psql -d farmer_procurement -f database/schema.sql
-- Then: database/indexes.sql and database/seed.sql
--
-- Distance farmer↔centre is NOT stored. Compute it at request time.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE farmers (
    farmer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    passbook_number VARCHAR(32) NOT NULL,
    farmer_name VARCHAR(120) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL,
    village VARCHAR(120) NOT NULL,
    mandal VARCHAR(120) NOT NULL,
    district VARCHAR(120) NOT NULL,
    survey_number VARCHAR(64) NOT NULL,
    total_land_acres NUMERIC(12, 2) NOT NULL,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farmers_passbook_number UNIQUE (passbook_number),
    CONSTRAINT ck_farmers_positive_land CHECK (total_land_acres > 0)
);

CREATE TABLE land_records (
    land_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL,
    survey_number VARCHAR(64) NOT NULL,
    land_area_acres NUMERIC(12, 2) NOT NULL,
    land_type VARCHAR(40) NOT NULL DEFAULT 'AGRICULTURAL',
    ownership_status VARCHAR(40) NOT NULL DEFAULT 'OWNED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_land_records_positive_land_area CHECK (land_area_acres > 0),
    CONSTRAINT fk_land_records_farmer_id_farmers
        FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id) ON DELETE CASCADE
);

CREATE TABLE cultivation_records (
    cultivation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL,
    season VARCHAR(32) NOT NULL,
    cultivated_area_acres NUMERIC(12, 2) NOT NULL,
    crop VARCHAR(64) NOT NULL,
    quantity_produced_quintals NUMERIC(12, 2) NOT NULL,
    quantity_to_sell_quintals NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_cultivation_records_positive_cultivated_area
        CHECK (cultivated_area_acres > 0),
    CONSTRAINT ck_cultivation_records_positive_produced
        CHECK (quantity_produced_quintals > 0),
    CONSTRAINT ck_cultivation_records_non_negative_to_sell
        CHECK (quantity_to_sell_quintals >= 0),
    CONSTRAINT ck_cultivation_records_sell_not_exceed_produced
        CHECK (quantity_to_sell_quintals <= quantity_produced_quintals),
    CONSTRAINT fk_cultivation_records_farmer_id_farmers
        FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id) ON DELETE CASCADE
);

-- cultivated_area_acres <= farmers.total_land_acres is enforced in application
-- code (Phase 6). A cross-table CHECK is not used here.

CREATE TABLE procurement_centres (
    centre_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centre_code VARCHAR(32) NOT NULL,
    centre_name VARCHAR(160) NOT NULL,
    agency VARCHAR(64) NOT NULL,
    village VARCHAR(120) NOT NULL,
    mandal VARCHAR(120) NOT NULL,
    district VARCHAR(120) NOT NULL,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    capacity INTEGER NOT NULL,
    current_status VARCHAR(16) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_procurement_centres_centre_code UNIQUE (centre_code),
    CONSTRAINT ck_procurement_centres_positive_capacity CHECK (capacity > 0),
    CONSTRAINT ck_procurement_centres_valid_centre_status
        CHECK (current_status IN ('ACTIVE', 'LIMITED', 'FULL', 'INACTIVE'))
);

CREATE TABLE slots (
    slot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centre_id UUID NOT NULL,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    maximum_farmers INTEGER NOT NULL,
    booked_farmers INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_slots_centre_date_start UNIQUE (centre_id, slot_date, start_time),
    CONSTRAINT ck_slots_positive_maximum_farmers CHECK (maximum_farmers > 0),
    CONSTRAINT ck_slots_non_negative_booked_farmers CHECK (booked_farmers >= 0),
    CONSTRAINT ck_slots_booked_within_capacity CHECK (booked_farmers <= maximum_farmers),
    CONSTRAINT ck_slots_slot_end_after_start CHECK (end_time > start_time),
    CONSTRAINT fk_slots_centre_id_procurement_centres
        FOREIGN KEY (centre_id) REFERENCES procurement_centres (centre_id) ON DELETE CASCADE
);

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(80) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    farmer_id UUID,
    centre_id UUID,
    district VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT ck_users_valid_user_role
        CHECK (role IN ('FARMER', 'CENTRE_STAFF', 'DISTRICT_ADMIN')),
    CONSTRAINT fk_users_farmer_id_farmers
        FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id) ON DELETE SET NULL,
    CONSTRAINT fk_users_centre_id_procurement_centres
        FOREIGN KEY (centre_id) REFERENCES procurement_centres (centre_id) ON DELETE SET NULL
);

CREATE TABLE bookings (
    booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_number VARCHAR(32) NOT NULL,
    farmer_id UUID NOT NULL,
    cultivation_id UUID NOT NULL,
    centre_id UUID NOT NULL,
    slot_id UUID NOT NULL,
    quantity_to_sell_quintals NUMERIC(12, 2) NOT NULL,
    booking_status VARCHAR(16) NOT NULL DEFAULT 'CONFIRMED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_bookings_booking_number UNIQUE (booking_number),
    CONSTRAINT ck_bookings_positive_booking_qty CHECK (quantity_to_sell_quintals > 0),
    CONSTRAINT ck_bookings_valid_booking_status
        CHECK (booking_status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW')),
    CONSTRAINT fk_bookings_farmer_id_farmers
        FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id) ON DELETE RESTRICT,
    CONSTRAINT fk_bookings_cultivation_id_cultivation_records
        FOREIGN KEY (cultivation_id) REFERENCES cultivation_records (cultivation_id) ON DELETE RESTRICT,
    CONSTRAINT fk_bookings_centre_id_procurement_centres
        FOREIGN KEY (centre_id) REFERENCES procurement_centres (centre_id) ON DELETE RESTRICT,
    CONSTRAINT fk_bookings_slot_id_slots
        FOREIGN KEY (slot_id) REFERENCES slots (slot_id) ON DELETE RESTRICT
);

CREATE TABLE queue_tokens (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL,
    token_number INTEGER NOT NULL,
    queue_status VARCHAR(16) NOT NULL DEFAULT 'WAITING',
    called_at TIMESTAMPTZ,
    processing_started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_queue_tokens_booking_id UNIQUE (booking_id),
    CONSTRAINT ck_queue_tokens_positive_token_number CHECK (token_number > 0),
    CONSTRAINT ck_queue_tokens_valid_queue_status
        CHECK (queue_status IN ('WAITING', 'CALLED', 'PROCESSING', 'COMPLETED', 'SKIPPED', 'CANCELLED')),
    CONSTRAINT fk_queue_tokens_booking_id_bookings
        FOREIGN KEY (booking_id) REFERENCES bookings (booking_id) ON DELETE CASCADE
);

CREATE TABLE procurement_records (
    procurement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL,
    quantity_submitted_quintals NUMERIC(12, 2) NOT NULL,
    quantity_accepted_quintals NUMERIC(12, 2) NOT NULL,
    price_per_quintal NUMERIC(12, 2) NOT NULL,
    procurement_status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    verified_by UUID,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_procurement_records_booking_id UNIQUE (booking_id),
    CONSTRAINT ck_procurement_records_positive_submitted
        CHECK (quantity_submitted_quintals > 0),
    CONSTRAINT ck_procurement_records_non_negative_accepted
        CHECK (quantity_accepted_quintals >= 0),
    CONSTRAINT ck_procurement_records_positive_price CHECK (price_per_quintal > 0),
    CONSTRAINT ck_procurement_records_accepted_not_exceed_submitted
        CHECK (quantity_accepted_quintals <= quantity_submitted_quintals),
    CONSTRAINT ck_procurement_records_valid_procurement_status
        CHECK (procurement_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED')),
    CONSTRAINT fk_procurement_records_booking_id_bookings
        FOREIGN KEY (booking_id) REFERENCES bookings (booking_id) ON DELETE RESTRICT,
    CONSTRAINT fk_procurement_records_verified_by_users
        FOREIGN KEY (verified_by) REFERENCES users (user_id) ON DELETE SET NULL
);

CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    procurement_id UUID NOT NULL,
    amount_payable NUMERIC(12, 2) NOT NULL,
    payment_status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    transaction_reference VARCHAR(64),
    payment_date TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_payments_procurement_id UNIQUE (procurement_id),
    CONSTRAINT ck_payments_non_negative_amount CHECK (amount_payable >= 0),
    CONSTRAINT ck_payments_valid_payment_status
        CHECK (payment_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    CONSTRAINT fk_payments_procurement_id_procurement_records
        FOREIGN KEY (procurement_id) REFERENCES procurement_records (procurement_id) ON DELETE RESTRICT
);

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL,
    booking_id UUID,
    notification_type VARCHAR(40) NOT NULL,
    title VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_notifications_farmer_id_farmers
        FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_booking_id_bookings
        FOREIGN KEY (booking_id) REFERENCES bookings (booking_id) ON DELETE SET NULL
);

CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_audit_logs_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
);
