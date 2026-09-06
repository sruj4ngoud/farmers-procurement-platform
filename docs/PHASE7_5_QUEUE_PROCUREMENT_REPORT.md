# PHASE 7.5 — ADMIN QUEUE AND PROCUREMENT MANAGEMENT REPORT

## 1. QUEUE DASHBOARD

### Overview Cards
Each slot shows:
- Centre name
- Slot date + time
- Current token number
- Waiting / Called / Processing / Completed counts
- "Call Next" button

### Token List (per slot)
Shows all tokens with:
- Token number
- Farmer name + passbook
- Crop + quantity
- Status badge (WAITING/CALLED/PROCESSING/COMPLETED/SKIPPED)
- Action buttons based on current status

## 2. TOKEN OPERATIONS

### Valid Transitions
| From | To |
|------|-----|
| WAITING | CALLED, SKIPPED, CANCELLED |
| CALLED | PROCESSING, SKIPPED, CANCELLED |
| PROCESSING | COMPLETED, SKIPPED, CANCELLED |

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/queue/overview` | GET | Slot-level queue overview |
| `/api/admin/queue/slot/{id}/tokens` | GET | All tokens for a slot |
| `/api/admin/queue/tokens/{id}/transition` | PUT | Transition token status |
| `/api/admin/queue/slot/{id}/call-next` | POST | Call next WAITING token |

### Timestamps
- `called_at` — set when status → CALLED
- `processing_started_at` — set when status → PROCESSING
- `completed_at` — set when status → COMPLETED

## 3. PROCUREMENT MANAGEMENT

### Procurement Cards
Shows:
- Booking number, farmer, crop
- Declared quantity vs accepted quantity
- Quantity difference (with ⚠ flag for mismatches)
- Status badge
- Payment status

### Edit Form
- Submitted weight (actual weighed quantity)
- Accepted quantity (after verification)
- Price per quintal
- Remarks (quality notes, etc.)
- "Complete Procurement" button

### Quantity Mismatch Display
```
Declared:  10.00 Q
Actual:     9.40 Q
Difference: -0.60 Q  ⚠
```
Flagged when `|submitted - accepted| > 0.01`

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/procurement/pending` | GET | Pending procurements |
| `/api/admin/procurement/all` | GET | All procurements |
| `/api/admin/procurement/{booking_id}` | GET | Procurement detail |
| `/api/admin/procurement/{booking_id}` | PUT | Update procurement |
| `/api/admin/procurement/{booking_id}/complete` | POST | Mark completed |

## 4. FARMER REFLECTION

Admin queue/procurement changes flow through:
1. Admin updates database via API
2. Farmer MyBooking reads from same database
3. Farmer sees updated queue position, status, procurement progress

## 5. TESTS

- **Backend**: 121/121 passing
- **Frontend build**: ✓ Success
- All existing tests unaffected

## 6. FILES CHANGED

### New Files
| File | Purpose |
|------|---------|
| `backend/app/api/admin/queue.py` | Admin queue management endpoints |
| `backend/app/api/admin/procurement.py` | Admin procurement management endpoints |
| `frontend/src/pages/admin/AdminQueuePage.jsx` | Queue dashboard UI |
| `frontend/src/pages/admin/AdminProcurementPage.jsx` | Procurement management UI |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/main.py` | Registered queue + procurement routers |
| `frontend/src/services/adminApi.js` | Added queue + procurement API methods |
| `frontend/src/layouts/AdminLayout.jsx` | Added Queue + Procurement links |
| `frontend/src/routes/AppRoutes.jsx` | Added queue + procurement routes |

---

**FINAL STATUS: ✅ PASS**
