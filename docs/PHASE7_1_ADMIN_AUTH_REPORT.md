# PHASE 7.1 — ADMIN AUTHENTICATION & ROLE-BASED AUTHORIZATION REPORT

## 1. ADMIN AUTHENTICATION

- **Admin model**: Extended existing `users` table with `district` column and `DISTRICT_ADMIN` role
- **Admin login**: `POST /api/admin/auth/login` with username + password
- **Password hashing**: bcrypt (4.x) — no plaintext passwords stored
- **JWT**: Separate admin JWT containing `admin_id`, `username`, `role: DISTRICT_ADMIN`, `district`, `iat`, `exp`
- **District scope**: Each admin is scoped to a district; district_id comes from JWT/database, never from frontend
- **Role authorization**: `get_current_admin` dependency validates role = DISTRICT_ADMIN and is_active = true

## 2. SECURITY

- **Farmer cannot access admin**: Farmer JWT has `role: FARMER`; `decode_admin_token` rejects tokens where role ≠ DISTRICT_ADMIN (returns 403)
- **Cross-district access blocked**: All admin queries filter by `admin.district`; frontend cannot override district
- **Admin cannot impersonate farmer**: Separate JWT types, separate auth dependencies, separate localStorage keys

## 3. DATABASE

- **Migration**: User model updated with `district` column (String, nullable) and role constraint updated to `('FARMER', 'CENTRE_STAFF', 'DISTRICT_ADMIN')`
- **Schema**: `database/schema.sql` updated to match
- **Tables affected**: `users` only — no new tables created

## 4. FRONTEND

- **Admin login page**: `/admin/login` — separate from farmer login, dark theme
- **Admin layout**: Separate sidebar with Dashboard, Farmers, Centres, Bookings, Logout
- **Admin routes**: All under `/admin/*`, completely separated from farmer routes
- **Admin context**: `AdminContext` — separate auth state, localStorage keys (`fp_admin_token`, `fp_admin`)
- **Pages**: Dashboard (district stats), Farmers list, Centres list, Bookings list

## 5. API ENDPOINTS

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/admin/auth/login` | POST | No | Admin username/password login |
| `/api/admin/dashboard` | GET | Yes (admin JWT) | District aggregate stats |
| `/api/admin/farmers` | GET | Yes (admin JWT) | Farmers in admin's district |
| `/api/admin/centres` | GET | Yes (admin JWT) | Centres in admin's district |
| `/api/admin/bookings` | GET | Yes (admin JWT) | Bookings in admin's district |
| `/api/admin/district-info` | GET | Yes (admin JWT) | Admin's own district info |

## 6. TESTS

- **Backend**: 116/116 passing (100 existing + 16 new admin tests)
- **Admin tests cover**:
  - Valid admin login ✓
  - Wrong password rejection ✓
  - Nonexistent username rejection ✓
  - Inactive admin rejection ✓
  - Farmer role cannot login as admin ✓
  - Invalid JWT rejected ✓
  - Farmer token rejected on admin endpoint ✓
  - Admin token works ✓
  - District-scoped farmer listing ✓
  - Cross-district centre access blocked ✓
  - District info endpoint ✓
  - Admin dashboard stats ✓
  - District-scoped bookings ✓
  - Login requires no token ✓
  - Empty body validation ✓
  - Farmer auth not broken ✓
- **Frontend build**: ✓ Success

## 7. SEED DATA

Demo admin accounts (created by `demo_seed.py`):

| Username | Password | District |
|----------|----------|----------|
| admin_sangareddy | admin123 | Sangareddy |
| admin_medchal | admin123 | Medchal-Malkajgiri |
| admin_rangareddy | admin123 | Ranga Reddy |

## 8. FILES CHANGED

### New Files
| File | Purpose |
|------|---------|
| `backend/app/core/admin_security.py` | Password hashing + admin JWT creation/verification |
| `backend/app/core/admin_permissions.py` | `get_current_admin` FastAPI dependency |
| `backend/app/services/admin_auth_service.py` | Admin login business logic |
| `backend/app/schemas/admin.py` | Admin request/response schemas |
| `backend/app/api/admin/__init__.py` | Admin API endpoints |
| `backend/app/tests/test_admin.py` | 16 admin auth/authorization tests |
| `frontend/src/services/adminApi.js` | Admin API service |
| `frontend/src/context/AdminContext.jsx` | Admin authentication context |
| `frontend/src/layouts/AdminLayout.jsx` | Admin sidebar layout |
| `frontend/src/pages/admin/AdminLoginPage.jsx` | Admin login page |
| `frontend/src/pages/admin/AdminDashboardPage.jsx` | Admin dashboard |
| `frontend/src/pages/admin/AdminFarmersPage.jsx` | District farmers list |
| `frontend/src/pages/admin/AdminCentresPage.jsx` | District centres list |
| `frontend/src/pages/admin/AdminBookingsPage.jsx` | District bookings list |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/models/user.py` | Added `district` column, updated role constraint to DISTRICT_ADMIN |
| `backend/app/main.py` | Registered admin router |
| `backend/requirements.txt` | Added `bcrypt>=4.0.0,<5` |
| `backend/demo_seed.py` | Added admin user seeding |
| `database/schema.sql` | Added `district` column to users, updated role constraint |
| `frontend/src/routes/AppRoutes.jsx` | Added admin routes + admin auth guards |
| `frontend/src/main.jsx` | Added AdminProvider wrapper |

## 9. DATABASE CHANGES

```sql
-- Added to users table:
ALTER TABLE users ADD COLUMN district VARCHAR(120);

-- Updated constraint:
ALTER TABLE users DROP CONSTRAINT ck_users_valid_user_role;
ALTER TABLE users ADD CONSTRAINT ck_users_valid_user_role
    CHECK (role IN ('FARMER', 'CENTRE_STAFF', 'DISTRICT_ADMIN'));
```

## 10. REMAINING ISSUES

None. All tests pass and the build succeeds.

---

**FINAL STATUS: ✅ PASS**
