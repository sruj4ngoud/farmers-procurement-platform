-- Sample queries for farmer_procurement.
-- Replace UUID literals after data exists (Phase 3). These are structural examples.

-- 1. Find farmer by passbook number
SELECT farmer_id, passbook_number, farmer_name, mobile_number, village, district, total_land_acres
FROM farmers
WHERE passbook_number = 'PPB000001';

-- 2. Get farmer profile
SELECT
    f.farmer_id,
    f.passbook_number,
    f.farmer_name,
    f.mobile_number,
    f.village,
    f.mandal,
    f.district,
    f.survey_number,
    f.total_land_acres,
    f.latitude,
    f.longitude
FROM farmers f
WHERE f.passbook_number = 'PPB000001';

-- 3. Get farmer cultivation records
SELECT
    c.cultivation_id,
    c.season,
    c.crop,
    c.cultivated_area_acres,
    c.quantity_produced_quintals,
    c.quantity_to_sell_quintals
FROM cultivation_records c
JOIN farmers f ON f.farmer_id = c.farmer_id
WHERE f.passbook_number = 'PPB000001'
ORDER BY c.created_at DESC;

-- 4. Find active procurement centres
SELECT centre_id, centre_code, centre_name, agency, village, district, capacity, current_status
FROM procurement_centres
WHERE current_status = 'ACTIVE'
ORDER BY centre_name;

-- 5. Get available slots for a centre
SELECT
    s.slot_id,
    s.slot_date,
    s.start_time,
    s.end_time,
    s.maximum_farmers,
    s.booked_farmers,
    (s.maximum_farmers - s.booked_farmers) AS remaining
FROM slots s
JOIN procurement_centres pc ON pc.centre_id = s.centre_id
WHERE pc.centre_code = 'PPC004'
  AND s.is_active = TRUE
  AND s.booked_farmers < s.maximum_farmers
  AND s.slot_date >= CURRENT_DATE
ORDER BY s.slot_date, s.start_time;

-- 6. Get booking details
SELECT
    b.booking_id,
    b.booking_number,
    b.booking_status,
    b.quantity_to_sell_quintals,
    f.farmer_name,
    f.passbook_number,
    c.crop,
    pc.centre_name,
    s.slot_date,
    s.start_time
FROM bookings b
JOIN farmers f ON f.farmer_id = b.farmer_id
JOIN cultivation_records c ON c.cultivation_id = b.cultivation_id
JOIN procurement_centres pc ON pc.centre_id = b.centre_id
JOIN slots s ON s.slot_id = b.slot_id
WHERE b.booking_number = 'BKG000001';

-- 7. Get current queue for a centre (today)
SELECT
    qt.token_number,
    qt.queue_status,
    f.farmer_name,
    cr.crop,
    b.quantity_to_sell_quintals,
    qt.called_at
FROM queue_tokens qt
JOIN bookings b ON b.booking_id = qt.booking_id
JOIN farmers f ON f.farmer_id = b.farmer_id
JOIN cultivation_records cr ON cr.cultivation_id = b.cultivation_id
JOIN slots s ON s.slot_id = b.slot_id
JOIN procurement_centres pc ON pc.centre_id = b.centre_id
WHERE pc.centre_code = 'PPC004'
  AND s.slot_date = CURRENT_DATE
  AND qt.queue_status IN ('WAITING', 'CALLED', 'PROCESSING')
ORDER BY qt.token_number;

-- 8. Get farmer's current queue position
SELECT
    farmer_token.token_number AS your_token,
    current_called.token_number AS current_token,
    GREATEST(farmer_token.token_number - COALESCE(current_called.token_number, farmer_token.token_number), 0)
        AS farmers_ahead
FROM queue_tokens farmer_token
JOIN bookings b ON b.booking_id = farmer_token.booking_id
JOIN farmers f ON f.farmer_id = b.farmer_id
JOIN slots s ON s.slot_id = b.slot_id
LEFT JOIN LATERAL (
    SELECT qt.token_number
    FROM queue_tokens qt
    JOIN bookings qb ON qb.booking_id = qt.booking_id
    JOIN slots qs ON qs.slot_id = qb.slot_id
    WHERE qb.centre_id = b.centre_id
      AND qs.slot_date = s.slot_date
      AND qt.queue_status IN ('CALLED', 'PROCESSING')
    ORDER BY qt.called_at DESC NULLS LAST
    LIMIT 1
) current_called ON TRUE
WHERE f.passbook_number = 'PPB000001'
  AND farmer_token.queue_status IN ('WAITING', 'CALLED', 'PROCESSING')
ORDER BY farmer_token.created_at DESC
LIMIT 1;

-- 9. Get procurement status
SELECT
    pr.procurement_id,
    b.booking_number,
    pr.quantity_submitted_quintals,
    pr.quantity_accepted_quintals,
    pr.price_per_quintal,
    pr.procurement_status,
    pr.remarks
FROM procurement_records pr
JOIN bookings b ON b.booking_id = pr.booking_id
WHERE b.booking_number = 'BKG000001';

-- 10. Get payment status
SELECT
    p.payment_id,
    b.booking_number,
    p.amount_payable,
    p.payment_status,
    p.transaction_reference,
    p.payment_date,
    p.failure_reason
FROM payments p
JOIN procurement_records pr ON pr.procurement_id = p.procurement_id
JOIN bookings b ON b.booking_id = pr.booking_id
WHERE b.booking_number = 'BKG000001';

-- 11. Get unread notifications
SELECT n.notification_id, n.notification_type, n.title, n.message, n.created_at
FROM notifications n
JOIN farmers f ON f.farmer_id = n.farmer_id
WHERE f.passbook_number = 'PPB000001'
  AND n.is_read = FALSE
ORDER BY n.created_at DESC;

-- 12. Centre dashboard statistics (today)
SELECT
    pc.centre_code,
    pc.centre_name,
    COUNT(*) FILTER (WHERE TRUE) AS total_farmers,
    COUNT(*) FILTER (WHERE qt.queue_status = 'COMPLETED') AS completed,
    COUNT(*) FILTER (WHERE qt.queue_status = 'WAITING') AS waiting,
    COUNT(*) FILTER (WHERE qt.queue_status = 'PROCESSING') AS processing,
    COUNT(*) FILTER (WHERE qt.queue_status = 'CALLED') AS called
FROM procurement_centres pc
JOIN bookings b ON b.centre_id = pc.centre_id
JOIN slots s ON s.slot_id = b.slot_id
JOIN queue_tokens qt ON qt.booking_id = b.booking_id
WHERE pc.centre_code = 'PPC004'
  AND s.slot_date = CURRENT_DATE
GROUP BY pc.centre_code, pc.centre_name;
