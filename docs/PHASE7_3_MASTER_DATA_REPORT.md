# PHASE 7.3 — ADMIN MASTER DATA MANAGEMENT REPORT

## 1. CROPS

### New Model
- `Crop` — `crop_id`, `crop_name`, `crop_category`, `is_active`, `msp_per_quintal`, `msp_effective_date`
- 89 crops seeded from existing MSP_DATA into the database

### Admin CRUD
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/crops` | GET | List all crops (active + inactive) |
| `/api/admin/crops/{id}` | GET | Get single crop |
| `/api/admin/crops` | POST | Add new crop |
| `/api/admin/crops/{id}` | PUT | Update crop / activate / deactivate |

### Farmer API (reads from database)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crops` | GET | List all active crops with MSP |
| `/api/crops/{name}/msp` | GET | Get MSP for specific crop |
| `/api/crop-categories` | GET | List distinct active categories |

### Frontend Integration
- `SellCrop.jsx` — now fetches crops from `/api/crops` instead of hardcoded array
- `AddCultivation.jsx` — now fetches crops from `/api/crops` instead of hardcoded array
- `cropApi.js` — new service for farmer crop endpoints

## 2. MSP

- MSP stored on `Crop` model as `msp_per_quintal` and `msp_effective_date`
- Admin can update MSP for any crop via PUT endpoint
- Historical procurement records retain the rate used at the time (stored in `ProcurementRecord.price_per_quintal`)
- Farmer portal reads MSP from database, not hardcoded config

## 3. PROCUREMENT CENTRES

### Admin CRUD (district-scoped)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/centres` | GET | List centres in admin's district |
| `/api/admin/centres/{id}` | GET | Get single centre |
| `/api/admin/centres` | POST | Add new centre (auto-assigns admin's district) |
| `/api/admin/centres/{id}` | PUT | Update centre (name, capacity, status, etc.) |

### Fields: name, district, mandal, village, agency, lat/lon, capacity, status

## 4. SLOTS

### Admin CRUD (district-scoped, destructive-change protection)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/slots` | GET | List all slots in admin's district |
| `/api/admin/slots/{id}` | GET | Get single slot |
| `/api/admin/slots` | POST | Create new slot (validates centre is in admin's district) |
| `/api/admin/slots/{id}` | PUT | Update slot (protects capacity if bookings exist) |

### Protection
- Cannot reduce slot capacity below booked count when bookings are CONFIRMED/COMPLETED
- Centre must belong to admin's district

## 5. FARMER INTEGRATION

| Data | Before (Hardcoded) | After (Database) |
|------|--------------------|--------------------|
| Crop list | `data/crops.js` CROPS array | `GET /api/crops` |
| MSP values | `config/msp.py` MSP_DATA dict | `Crop.msp_per_quintal` via API |
| Categories | `CROP_CATEGORIES` JS array | `GET /crop-categories` |

When admin adds/edits/deactivates a crop:
1. Database changes
2. Farmer portal reads from API
3. No hardcoded frontend data

## 6. TESTS

- **Backend**: 121/121 passing
- **Frontend build**: ✓ Success
- **Admin tests**: 21 passing (auth + dashboard + mandals + cross-district)
- **Farmer auth**: Untouched and working

## 7. FILES CHANGED

### New Files
| File | Purpose |
|------|---------|
| `backend/app/models/crop.py` | Crop model with MSP |
| `backend/app/api/admin/crops.py` | Admin crop CRUD endpoints |
| `backend/app/api/admin/centres.py` | Admin centre CRUD endpoints |
| `backend/app/api/admin/slots.py` | Admin slot CRUD endpoints |
| `backend/app/api/farmer/crops.py` | Farmer-facing crop/MSP API |
| `frontend/src/services/cropApi.js` | Farmer crop API service |
| `frontend/src/pages/admin/AdminCropsPage.jsx` | Admin crops management |
| `frontend/src/pages/admin/AdminSlotsPage.jsx` | Admin slots management |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/models/__init__.py` | Registered Crop model |
| `backend/app/schemas/admin.py` | Added crop/centre/slot CRUD schemas |
| `backend/app/api/admin/__init__.py` | Added crop/centre/slot imports |
| `backend/app/main.py` | Registered new admin + farmer routers |
| `backend/demo_seed.py` | Seeds 89 crops from MSP_DATA |
| `frontend/src/pages/farmer/SellCrop.jsx` | Fetches crops from API |
| `frontend/src/pages/farmer/AddCultivation.jsx` | Fetches crops from API |
| `frontend/src/layouts/AdminLayout.jsx` | Added Crops & MSP + Slots sidebar links |
| `frontend/src/routes/AppRoutes.jsx` | Added admin crops + slots routes |
| `frontend/src/services/adminApi.js` | Added crop/centre/slot CRUD methods |

---

**FINAL STATUS: ✅ PASS**
