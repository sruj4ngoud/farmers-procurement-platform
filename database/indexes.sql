-- Lookup indexes. Unique constraints in schema.sql already index:
-- farmers.passbook_number, procurement_centres.centre_code, slots(centre_id, slot_date, start_time),
-- bookings.booking_number, queue_tokens.booking_id, payments.procurement_id, users.username.

CREATE INDEX IF NOT EXISTS ix_farmers_mobile_number
    ON farmers (mobile_number);

CREATE INDEX IF NOT EXISTS ix_farmers_latitude_longitude
    ON farmers (latitude, longitude);

CREATE INDEX IF NOT EXISTS ix_land_records_farmer_id
    ON land_records (farmer_id);

CREATE INDEX IF NOT EXISTS ix_cultivation_records_farmer_id
    ON cultivation_records (farmer_id);

CREATE INDEX IF NOT EXISTS ix_cultivation_records_crop
    ON cultivation_records (crop);

CREATE INDEX IF NOT EXISTS ix_procurement_centres_latitude_longitude
    ON procurement_centres (latitude, longitude);

CREATE INDEX IF NOT EXISTS ix_procurement_centres_current_status
    ON procurement_centres (current_status);

CREATE INDEX IF NOT EXISTS ix_slots_centre_id_slot_date
    ON slots (centre_id, slot_date);

CREATE INDEX IF NOT EXISTS ix_bookings_farmer_id
    ON bookings (farmer_id);

CREATE INDEX IF NOT EXISTS ix_bookings_centre_id
    ON bookings (centre_id);

CREATE INDEX IF NOT EXISTS ix_bookings_slot_id
    ON bookings (slot_id);

CREATE INDEX IF NOT EXISTS ix_bookings_cultivation_id
    ON bookings (cultivation_id);

CREATE INDEX IF NOT EXISTS ix_queue_tokens_queue_status
    ON queue_tokens (queue_status);

CREATE INDEX IF NOT EXISTS ix_notifications_farmer_id
    ON notifications (farmer_id);

CREATE INDEX IF NOT EXISTS ix_users_farmer_id
    ON users (farmer_id);

CREATE INDEX IF NOT EXISTS ix_users_centre_id
    ON users (centre_id);

CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id
    ON audit_logs (user_id);

CREATE INDEX IF NOT EXISTS ix_procurement_records_verified_by
    ON procurement_records (verified_by);
