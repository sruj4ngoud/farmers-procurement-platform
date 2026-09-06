# PHASE 7.4 — ADMIN BOOKING REVIEW REPORT

## 1. BOOKING WORKFLOW

```
Farmer submits booking
        ↓
PENDING_ADMIN_REVIEW (default)
        ↓
Admin reviews
        ↓
ACCEPTED / REJECTED + COMMENT
        ↓
No admin action for 24 hours
        ↓
AUTO_ACCEPTED
```

### New Statuses
| Status | Meaning |
|--------|---------|
| `PENDING_ADMIN_REVIEW` | New default — awaiting admin decision |
| `ACCEPTED` | Admin approved |
| `REJECTED` | Admin rejected (with comment) |
| `AUTO_ACCEPTED` | Auto-accepted after 24h timeout |
| `CONFIRMED` | Legacy status (backward compatible) |
| `CANCELLED` | Cancelled by farmer |
| `COMPLETED` | Procurement completed |
| `NO_SHOW` | Farmer did not show |

## 2. ADMIN REVIEW

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/reviews/pending` | GET | List bookings pending review |
| `/api/admin/reviews/all` | GET | List all bookings in district |
| `/api/admin/reviews/{id}/review` | PUT | Accept or reject a booking |
| `/api/admin/reviews/auto-accept` | POST | Process overdue bookings (24h) |

### Review API Response
Each booking shows:
- Farmer name, passbook, mobile, village, mandal, district
- Total land, cultivated area, crop, quantity
- Centre name, mandal, slot date/time
- Slot usage (booked/max)
- Review deadline + remaining hours
- Admin comment (if reviewed)
- Reviewed by username + timestamp

### Accept/Reject
- **Accept**: Sets status to ACCEPTED, creates notification, checks slot capacity
- **Reject**: Requires comment (400 if empty), sets status to REJECTED, creates notification

## 3. 24-HOUR AUTO-ACCEPT

- Implemented as `POST /api/admin/reviews/auto-accept` endpoint
- Can be called manually by admin or by a cron job
- Processes all bookings where `created_at + 24h <= now` and status is `PENDING_ADMIN_REVIEW`
- Skips bookings where slot is at full capacity
- Creates notification: "Your booking was automatically accepted because it was not reviewed within 24 hours."

## 4. AUDIT TRAIL

- `reviewed_by` — admin user_id who made the decision
- `reviewed_at` — timestamp of decision
- `admin_comment` — comment/reason for rejection
- `auto_accepted_at` — timestamp of auto-accept
- Decisions are never overwritten

## 5. CAPACITY PROTECTION

- Accept checks slot capacity before approving
- PENDING_ADMIN_REVIEW bookings count against slot capacity (via `CONFIRMED_BOOKING_STATUSES`)
- Cannot reduce slot capacity below booked count
- Cultivation quantity check considers all active booking statuses

## 6. FARMER UI

### MyBooking Page Updates
- **Status banner** with color-coded badge:
  - ⏳ Pending Admin Review (amber)
  - ✅ Accepted (green)
  - ❌ Rejected (red)
  - 🤖 Auto-Accepted (purple)
- **Rejection comment** displayed prominently if rejected
- **Review deadline** with countdown (e.g., "7h 42m remaining")
- **Updated progress timeline** with "Admin Review" step

## 7. NOTIFICATIONS

Created on:
- **Accept**: "Your booking has been accepted."
- **Reject**: "Your booking has been rejected. Reason: {comment}"
- **Auto-Accept**: "Your booking was automatically accepted because it was not reviewed within 24 hours."

## 8. TESTS

- **Backend**: 121/121 passing
- **Frontend build**: ✓ Success
- Existing workflow tests updated for new default status

## 9. FILES CHANGED

### New Files
| File | Purpose |
|------|---------|
| `backend/app/api/admin/reviews.py` | Admin review endpoints |
| `frontend/src/pages/admin/AdminReviewsPage.jsx` | Admin review UI |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/models/booking.py` | Added review fields (reviewed_by, reviewed_at, admin_comment, auto_accepted_at) |
| `backend/app/core/constants.py` | Updated CONFIRMED_BOOKING_STATUSES with new statuses |
| `backend/app/services/booking_service.py` | Default status → PENDING_ADMIN_REVIEW |
| `backend/app/services/cultivation_service.py` | Quantity check uses CONFIRMED_BOOKING_STATUSES |
| `backend/app/main.py` | Registered reviews router |
| `frontend/src/services/adminApi.js` | Added review endpoints |
| `frontend/src/layouts/AdminLayout.jsx` | Added Reviews link to sidebar |
| `frontend/src/routes/AppRoutes.jsx` | Added reviews route |
| `frontend/src/pages/farmer/MyBooking.jsx` | Updated for new statuses, deadline, rejection comments |
| `backend/app/tests/test_farmer_workflow.py` | Updated for PENDING_ADMIN_REVIEW default |

---

**FINAL STATUS: ✅ PASS**
