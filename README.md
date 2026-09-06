# Smart Farmer Procurement Platform

**A farmer-first digital platform for procurement booking, queue management, procurement tracking, and Government-to-Farmer payments.**

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-33-4169E1?logo=postgresql)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-136%20passing-brightgreen)](#testing)

---

## Project Overview

Farmers in India often face significant challenges during government crop procurement:

- **Long, unpredictable waiting times** at procurement centres with no visibility into queue status
- **No advance scheduling** — farmers arrive without knowing when they will be served
- **Unclear procurement status** after dropping off crops
- **Delayed payments** with no visibility into the payment pipeline
- **District-level administration** that is difficult to scale uniformly across regions

The **Smart Farmer Procurement Platform** solves these problems with a complete digital workflow — from booking a procurement slot at a nearby centre, through queue management and crop verification, to Government-to-Farmer payment tracking. Every step is transparent, database-backed, and district-scoped.

---

## What Makes This Platform Different

| Differentiator | Description |
|---|---|
| **Farmer-First Design** | The entire system is built around the farmer's procurement journey, not an administrative workflow |
| **Slot-Based Procurement** | Farmers book specific date/time slots at nearby centres instead of arriving unannounced |
| **Queue / Token Transparency** | Farmers receive a token and can see their position, farmers ahead, and estimated wait time |
| **33 District Administration** | Complete Telangana coverage with one District Admin per district |
| **Strict District Isolation** | Backend-enforced authorization — an admin can only access their district's data |
| **89-Crop Database Master** | All crop data stored in PostgreSQL, managed through the admin system |
| **Dynamic Nearby Centres** | Distance calculated using Haversine formula based on farmer and centre coordinates |
| **Admin Booking Review** | Bookings flow through PENDING_ADMIN_REVIEW → ACCEPTED / REJECTED / AUTO_ACCEPTED |
| **24-Hour Auto-Accept** | Backend can automatically accept bookings not reviewed within 24 hours |
| **Government-to-Farmer Payments** | Clear payment flow from Government → Farmer after procurement completion |
| **ML Congestion Insights** | Prototype ML model predicts centre congestion and estimated wait times |
| **PostgreSQL-Backed Sync** | Farmer-created bookings are immediately visible to the correct District Admin |

---

## Features

### Farmer Features

- **Passbook-based login** with mobile number and OTP verification
- **Dashboard** with greeting, passbook number, active booking, and procurement journey timeline
- **Crop selection** from 89 database-backed crops with category filtering and search
- **Land details** — enter cultivated area in acres
- **Quantity to sell** — enter quantity in quintals with MSP display and estimated Government payment
- **Nearby procurement centres** — dynamic distance calculation, availability status
- **Slot selection** — choose date and time slot with capacity visibility
- **Booking confirmation** with booking ID and summary
- **Token generation** and queue position tracking
- **My Booking** — full status tracking with animated procurement journey
- **Bank details** — account verification with OTP confirmation
- **Payment tracking** — Government payment status with timeline
- **History** — chronological procurement and payment history

### District Admin Features

- **Separate admin login portal** (`/admin/login`)
- **33 district administrations** with one admin per district
- **District dashboard** — total farmers, active bookings, pending reviews, today's metrics, mandal overview
- **Farmer management** — searchable list, district-scoped
- **Mandal management** — mandal overview per district
- **Crop management** — CRUD operations on the 89-crop master, activate/deactivate
- **Procurement centre management** — create, update, view centres
- **Slot management** — create and manage procurement slots with capacity control
- **Booking review** — accept/reject with mandatory comment, review deadline tracking
- **Queue management** — call next, current token display, queue status board
- **Procurement management** — declared quantity, actual weight, accepted quantity, MSP, payment
- **Bank verification** — verify, reject bank accounts, masked account numbers
- **Payment management** — Government → Farmer payment pipeline with status tracking
- **Reports** — farmers by mandal, crop usage, centre utilization, booking status, payment summary
- **Issue management** — create, assign, resolve operational issues
- **Audit logs** — full activity audit trail
- **ML insights** — congestion prediction, estimated wait time, confidence scores

---

## Complete Farmer Workflow

```
Farmer
  ↓
Login (Passbook + Mobile)
  ↓
OTP Verification
  ↓
Dashboard
  ↓
Sell Crop
  ↓
Select Crop (from 89-crop database)
  ↓
Enter Cultivated Area (Acres)
  ↓
Enter Quantity to Sell (Quintals)
  ↓
View MSP + Estimated Government Payment
  ↓
Choose Nearby Procurement Centre
  ↓
Choose Date/Time Slot
  ↓
Booking Confirmed (Booking ID + Token)
  ↓
Admin Review (24-hour window)
  ↓
  ├── Accepted
  ├── Rejected (with comment)
  └── Auto-Accepted (after 24 hours)
  ↓
Token / Queue
  ↓
Crop Verification
  ↓
Weighing
  ↓
Quality Verification
  ↓
Procurement Complete
  ↓
Government Payment
  ↓
History
```

---

## Admin Workflow

```
District Admin Login
  ↓
District Dashboard (scoped to district)
  ↓
├── Farmers (search, view, district-filtered)
├── Bookings / Reviews
│     ├── Accept (with comment)
│     └── Reject (with reason)
├── Queue Management
│     └── Call Next → Current Token → Process
├── Procurement
│     └── Declared → Actual → Accepted → Payment
├── Bank Verification
│     └── Pending → Verified / Rejected
├── Payments
│     └── Government → Farmer pipeline
├── Reports
├── Issues / Exceptions
├── Audit Logs
└── ML Congestion Insights
```

---

## District Architecture

The system supports **all 33 Telangana districts**, each with its own District Admin account.

| District | Admin Username |
|---|---|
| Adilabad | `admin_adilabad` |
| Bhadradri Kothagudem | `admin_bhadradri_kothagudem` |
| Hanumakonda | `admin_hanumakonda` |
| Hyderabad | `admin_hyderabad` |
| Jagtial | `admin_jagtial` |
| Jangaon | `admin_jangaon` |
| Jayashankar Bhupalpally | `admin_jayashankar_bhupalpally` |
| Jogulamba Gadwal | `admin_jogulamba_gadwal` |
| Kamareddy | `admin_kamareddy` |
| Karimnagar | `admin_karimnagar` |
| Khammam | `admin_khammam` |
| Kumuram Bheem | `admin_kumuram_bheem` |
| Mahabubabad | `admin_mahabubabad` |
| Mahabubnagar | `admin_mahabubnagar` |
| Mancherial | `admin_mancherial` |
| Medak | `admin_medak` |
| Medchal-Malkajgiri | `admin_medchalmalkajgiri` |
| Mulugu | `admin_mulugu` |
| Nagarkurnool | `admin_nagarkurnool` |
| Nalgonda | `admin_nalgonda` |
| Narayanpet | `admin_narayanpet` |
| Nirmal | `admin_nirmal` |
| Nizamabad | `admin_nizamabad` |
| Peddapalli | `admin_peddapalli` |
| Rajanna Sircilla | `admin_rajanna_sircilla` |
| Rangareddy | `admin_rangareddy` |
| Sangareddy | `admin_sangareddy` |
| Siddipet | `admin_siddipet` |
| Suryapet | `admin_suryapet` |
| Vikarabad | `admin_vikarabad` |
| Wanaparthy | `admin_wanaparthy` |
| Warangal | `admin_warangal` |
| Yadadri Bhuvanagiri | `admin_yadadri_bhuvanagiri` |

**District isolation is enforced on the backend.** The frontend does not provide the security boundary. An admin can only access resources belonging to their district.

---

## Farmer → Admin Synchronization

This is a core architectural feature of the platform:

```
Sangareddy Farmer
  ↓
Creates Booking (quantity, crop, centre, slot)
  ↓
Booking saved in PostgreSQL
  ↓
Sangareddy District Admin opens Reviews/Bookings
  ↓
Same Booking ID appears — farmer details, crop, centre, slot all match
  ↓
Admin reviews → Accepts / Rejects
  ↓
Status saved in PostgreSQL
  ↓
Farmer sees updated status in My Booking
```

**Critical guarantee:** `admin_medchalmalkajgiri` **cannot** see Sangareddy bookings. `admin_hyderabad` **cannot** see Sangareddy bookings. This is enforced at the backend API level, not through frontend filtering.

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| React | 18.3 | UI framework |
| React Router | 6.28 | Client-side routing |
| Vite | 6.0 | Build tool and dev server |
| Lucide React | 1.40 | SVG icon library |
| Framer Motion | 13.2 | Animation library |
| JavaScript (JSX) | ES2022 | Component logic |
| CSS | Custom design system | Black & white monochrome styling |

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime |
| FastAPI | 0.115 | REST API framework |
| SQLAlchemy | 2.0 | ORM and database access |
| Alembic | 1.14 | Database migrations |
| psycopg | 3.2 | PostgreSQL driver |
| Pydantic | 2.10 | Data validation and schemas |
| Uvicorn | 0.32 | ASGI server |
| PyJWT | 2.8 | JWT token authentication |
| bcrypt | 4.0 | Password hashing |

### ML / Data Science

| Technology | Purpose |
|---|---|
| pandas | Data preparation and analysis |
| numpy | Numerical computation |
| scikit-learn | Congestion prediction model |
| joblib | Model serialization |

### Database

| Technology | Purpose |
|---|---|
| PostgreSQL | Primary data store |
| SQLAlchemy | ORM layer |
| Alembic | Schema migrations |

### Testing

| Technology | Purpose |
|---|---|
| pytest | Backend test runner |
| httpx | HTTP client for API tests |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  React Frontend                  │
│  (Vite dev server / production build)            │
│  Farmer pages · Admin pages · CSS design system  │
└──────────────────┬──────────────────────────────┘
                   │ REST API (JSON)
                   │ Authorization: JWT Bearer
┌──────────────────▼──────────────────────────────┐
│                FastAPI Backend                    │
│  Auth · Farmer · Admin · Booking · Queue ·       │
│  Procurement · Payment · ML · Notifications      │
└──────────────────┬──────────────────────────────┘
                   │ SQLAlchemy ORM
┌──────────────────▼──────────────────────────────┐
│              PostgreSQL Database                  │
│  17 tables · 33 districts · 500 farmers          │
│  89 crops · 82 centres · 1230 slots              │
└─────────────────────────────────────────────────┘
```

### Authentication

- **Farmer login:** Passbook number + Mobile → OTP verification → JWT access token
- **Admin login:** Username + Password → JWT access token with district scope
- All protected routes require a valid JWT in the `Authorization: Bearer` header

### Authorization

- **District-scoped admin access:** Every admin API checks `current_user.district` against the requested resource
- The frontend never supplies `district_id` for authorization — it is derived from the authenticated admin's token

---

## Database Schema

The PostgreSQL database contains the following tables:

| Table | Purpose |
|---|---|
| `districts` | 33 Telangana districts |
| `mandals` | Administrative subdivisions within districts |
| `users` | Admin accounts (role = DISTRICT_ADMIN) |
| `farmers` | Farmer profiles with passbook, mobile, location |
| `land_records` | Farmer land ownership records |
| `cultivation_records` | Crop cultivation details per farmer |
| `crops` | Master crop list (89 crops with MSP) |
| `procurement_centres` | Procurement centres with coordinates |
| `slots` | Available date/time slots at each centre |
| `bookings` | Farmer procurement bookings |
| `queue_tokens` | Queue position tokens for active bookings |
| `procurement_records` | Declared, actual, and accepted quantities |
| `bank_details` | Farmer bank account information |
| `payments` | Government-to-Farmer payment records |
| `notifications` | System notifications for farmers |
| `issues` | Operational issues and exceptions |
| `audit_logs` | Full activity audit trail |

---

## Security

- **JWT authentication** for both farmer and admin sessions
- **OTP verification** for farmer login (demo mode returns OTP in response for testing)
- **bcrypt password hashing** for admin accounts
- **District-scoped authorization** enforced at the backend API level
- **Masked bank account numbers** — only last 4 digits visible in API responses and UI
- **Environment variables** for all secrets — `.env` excluded from Git
- **No secrets in frontend source** — all authentication handled via API calls
- **CORS configuration** — restricted to known frontend origins

---

## ML Congestion Prediction

The platform includes a prototype congestion prediction system for procurement centres:

- **Predicted congestion level** (LOW / MODERATE / HIGH)
- **Estimated waiting time** in minutes
- **Confidence score**
- **Recommendation** text

The model is trained on historical booking and queue data using scikit-learn. Predictions are displayed during slot selection to help farmers choose the best time to visit.

> **Disclaimer:** ML outputs are prototype/demo predictions intended for academic demonstration and are not production government forecasts.

---

## Project Structure

```
farmer-procurement-platform/
├── README.md
├── .env.example
├── .gitignore
├── LICENSE
├── docker-compose.yml
│
├── frontend/                      # React + Vite frontend
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx               # Entry point
│       ├── App.jsx                # Root component + error boundary
│       ├── routes/                # Route definitions
│       ├── pages/
│       │   ├── auth/              # Login, OTP verification
│       │   ├── farmer/            # Dashboard, Sell Crop, My Booking, etc.
│       │   └── admin/             # Admin dashboard, reviews, queue, etc.
│       ├── components/            # Shared components
│       ├── layouts/               # FarmerLayout, AdminLayout, AuthLayout
│       ├── context/               # Auth, Farmer, Admin contexts
│       ├── services/              # API service layer
│       ├── data/                  # Crop category data
│       └── styles/                # CSS design system
│
├── backend/                       # FastAPI backend
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── conftest.py
│   ├── app/
│   │   ├── main.py                # FastAPI application entry
│   │   ├── api/                   # Route handlers
│   │   │   ├── auth/              # Login, OTP, token
│   │   │   ├── farmer/            # Farmer endpoints
│   │   │   ├── admin/             # Admin endpoints
│   │   │   ├── bookings/          # Booking operations
│   │   │   ├── queue/             # Queue management
│   │   │   ├── procurement/       # Procurement tracking
│   │   │   ├── payments/          # Payment processing
│   │   │   ├── notifications/     # Notification system
│   │   │   ├── centres/           # Centre management
│   │   │   ├── slots/             # Slot management
│   │   │   └── ml/                # ML predictions
│   │   ├── models/                # SQLAlchemy models (17 tables)
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # Business logic layer
│   │   ├── core/                  # Auth, security, permissions
│   │   ├── config/                # Settings, MSP, logging
│   │   ├── database/              # Connection, base, seed
│   │   ├── middleware/            # CORS, error handling
│   │   ├── utils/                 # Validators, distance calc
│   │   └── tests/                 # 136 pytest tests
│   ├── migrations/                # Alembic migrations
│   ├── ml/                        # ML model training + prediction
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── model/                 # Serialized model files
│   ├── seed_telangana.py          # 33-district demo seed
│   └── demo_seed.py               # Basic demo seed
│
├── database/                      # Raw SQL schemas and queries
│   ├── schema.sql
│   ├── indexes.sql
│   ├── seed.sql
│   └── sample_queries.sql
│
├── data/                          # Generated CSV data
│
├── docs/                          # Development reports
│
├── scripts/                       # Utility scripts
│
└── tests/                         # Integration tests
```

---

## Demo Dataset

The application ships with a comprehensive Telangana-wide demo dataset:

| Entity | Count |
|---|---|
| Telangana Districts | 33 |
| District Admins | 33 |
| Mandals | 166 |
| Farmers | 500 |
| Land Records | 500 |
| Cultivation Records | 1,018 |
| Crops | 89 |
| Procurement Centres | 82 |
| Procurement Slots | 1,230 |
| Bookings | 335 |
| Queue Tokens | 196 |
| Procurement Records | 195 |
| Bank Details | 500 |
| Payments | 195 |
| Notifications | 338 |

> All farmer data, payment records, and personal information in the demo dataset are fictional. No real personal data is used.

---

## Quick Start

### Prerequisites

- [Git](https://git-scm.com/)
- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- [PostgreSQL 14+](https://www.postgresql.org/)

### 1. Clone the Repository

```bash
git clone https://github.com/sruj4ngoud/farmer-procurement-platform.git
cd farmer-procurement-platform
```

### 2. Create the PostgreSQL Database

Using **pgAdmin**:
- Open pgAdmin → right-click "Databases" → Create → Database
- Name: `farmer_procurement`
- Click "Save"

Using **psql**:
```sql
CREATE DATABASE farmer_procurement;
```

### 3. Configure the Backend

```bash
cd backend
copy .env.example .env
```

Edit `backend/.env` and replace the placeholders:

```ini
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/farmer_procurement
JWT_SECRET=change-me-to-a-long-random-secret-at-least-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OTP_DEMO_MODE=true
```

> Replace `YOUR_PASSWORD` with your actual PostgreSQL password.

### 4. Set Up the Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Install dependencies (no need to activate venv)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Run database migrations
.\.venv\Scripts\python.exe -m alembic upgrade head

# Seed the 33-district Telangana demo dataset
.\.venv\Scripts\python.exe seed_telangana.py
```

### 5. Start the Backend

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend is now running at:
- **API:** http://localhost:8000
- **Swagger docs:** http://localhost:8000/docs

### 6. Start the Frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend is now running at:
- **App:** http://localhost:5173

---

## Demo Credentials

> **DEMO / ACADEMIC USE ONLY** — Do not use these in production.

### Farmer Login

Use any farmer from the seeded dataset. Example:

| Field | Value |
|---|---|
| Passbook Number | `PB-TS-000396` |
| Mobile Number | `9000000396` |

After entering these on the login page, the OTP verification screen will display the OTP (demo mode). Enter the 6-digit code to complete login.

### District Admin Login

**Password for all admin accounts: `admin123`**

| Username | District |
|---|---|
| `admin_adilabad` | Adilabad |
| `admin_bhadradri_kothagudem` | Bhadradri Kothagudem |
| `admin_hanumakonda` | Hanumakonda |
| `admin_hyderabad` | Hyderabad |
| `admin_jagtial` | Jagtial |
| `admin_jangaon` | Jangaon |
| `admin_jayashankar_bhupalpally` | Jayashankar Bhupalpally |
| `admin_jogulamba_gadwal` | Jogulamba Gadwal |
| `admin_kamareddy` | Kamareddy |
| `admin_karimnagar` | Karimnagar |
| `admin_khammam` | Khammam |
| `admin_kumuram_bheem` | Kumuram Bheem |
| `admin_mahabubabad` | Mahabubabad |
| `admin_mahabubnagar` | Mahabubnagar |
| `admin_mancherial` | Mancherial |
| `admin_medak` | Medak |
| `admin_medchalmalkajgiri` | Medchal-Malkajgiri |
| `admin_mulugu` | Mulugu |
| `admin_nagarkurnool` | Nagarkurnool |
| `admin_nalgonda` | Nalgonda |
| `admin_narayanpet` | Narayanpet |
| `admin_nirmal` | Nirmal |
| `admin_nizamabad` | Nizamabad |
| `admin_peddapalli` | Peddapalli |
| `admin_rajanna_sircilla` | Rajanna Sircilla |
| `admin_rangareddy` | Rangareddy |
| `admin_sangareddy` | Sangareddy |
| `admin_siddipet` | Siddipet |
| `admin_suryapet` | Suryapet |
| `admin_vikarabad` | Vikarabad |
| `admin_wanaparthy` | Wanaparthy |
| `admin_warangal` | Warangal |
| `admin_yadadri_bhuvanagiri` | Yadadri Bhuvanagiri |

> Each admin sees **only** their district's data. District isolation is enforced at the backend.

---

## Telangana District Coverage

The platform supports all **33 Telangana districts**:

1. Adilabad
2. Bhadradri Kothagudem
3. Hanumakonda
4. Hyderabad
5. Jagtial
6. Jangaon
7. Jayashankar Bhupalpally
8. Jogulamba Gadwal
9. Kamareddy
10. Karimnagar
11. Khammam
12. Kumuram Bheem
13. Mahabubabad
14. Mahabubnagar
15. Mancherial
16. Medak
17. Medchal-Malkajgiri
18. Mulugu
19. Nagarkurnool
20. Nalgonda
21. Narayanpet
22. Nirmal
23. Nizamabad
24. Peddapalli
25. Rajanna Sircilla
26. Rangareddy
27. Sangareddy
28. Siddipet
29. Suryapet
30. Vikarabad
31. Wanaparthy
32. Warangal
33. Yadadri Bhuvanagiri

- One District Admin is provisioned per district
- District names are real administrative divisions of Telangana
- All farmer data, bank details, and payment records in the demo dataset are fictional

---

## 5-Minute Demo

A quick demonstration flow suitable for SIH judges or project evaluation:

### Part 1: Farmer Journey

1. Open http://localhost:5173/login
2. Enter Passbook: `PB-TS-000396` and Mobile: `9000000396`
3. Copy the OTP shown on screen → enter and verify
4. Dashboard shows greeting, passbook, and active booking
5. Click **Sell Crop**
6. Enter cultivated area (e.g., 5 acres)
7. Select a crop (e.g., Paddy)
8. Enter quantity to sell (e.g., 20 quintals)
9. View MSP (₹2,320/quintal) and estimated Government payment (₹46,400)
10. Select a nearby procurement centre (sorted by distance)
11. Select a date/time slot
12. Confirm booking → Booking ID generated

### Part 2: Admin Review

13. Open http://localhost:5173/admin/login
14. Login as `admin_sangareddy` / `admin123`
15. Dashboard shows district-scoped metrics
16. Navigate to **Reviews**
17. Find the SAME booking ID from step 12
18. Review farmer details, crop, quantity, centre, slot
19. **Accept** the booking
20. Verify the booking now shows ACCEPTED status

### Part 3: District Isolation Verification

21. Logout → Login as `admin_medchalmalkajgiri` / `admin123`
22. Navigate to Reviews/Bookings
23. The Sangareddy booking is **NOT visible**

---

## API Documentation

- **Backend base URL:** http://localhost:8000
- **Swagger (interactive docs):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Major API Areas

| Area | Prefix | Description |
|---|---|---|
| Authentication | `/api/auth` | Farmer OTP login, admin login, token management |
| Farmer | `/api/farmer` | Dashboard, profile, land, crops, cultivation, bookings, bank |
| Admin | `/api/admin` | District-scoped management for all entities |
| Bookings | `/api/bookings` | Booking creation and management |
| Centres | `/api/centres` | Procurement centre listing and distance |
| Slots | `/api/slots` | Slot availability and management |
| Queue | `/api/queue` | Queue token generation and status |
| Procurement | `/api/procurement` | Procurement record management |
| Payments | `/api/payments` | Government-to-Farmer payment tracking |
| Notifications | `/api/notifications` | Farmer notification system |
| ML | `/api/ml` | Congestion prediction and insights |

---

## Testing

### Backend Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

**Result: 136 tests passing** across 18 test modules covering:
- Authentication and OTP
- Admin authorization and district isolation
- Farmer workflow (complete procurement journey)
- Booking creation and management
- Queue token management
- Procurement record handling
- Payment processing
- ML prediction endpoints
- Centre and slot API
- Cultivation and crop API
- Root endpoint

### Frontend Build

```bash
cd frontend
npm run build
```

Build output:
- `dist/index.html` — 0.74 KB
- `dist/assets/index.css` — 21.48 KB (4.65 KB gzipped)
- `dist/assets/index.js` — 324.94 KB (86.20 KB gzipped)

---

## Troubleshooting

### Python command not found

Try `py` instead of `python`, or ensure Python 3.10+ is installed and on your PATH.

### PowerShell virtual environment activation blocked

Instead of activating the venv, run Python directly:

```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Port 8000 already in use

An existing backend process may be running:

```bash
netstat -ano | findstr :8000
```

Find the PID and stop it, or use a different port:

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

### PostgreSQL connection error

- Ensure PostgreSQL service is running
- Verify the database `farmer_procurement` exists
- Check your `DATABASE_URL` in `backend/.env` — username, password, and database name must be correct
- Ensure the port matches your PostgreSQL installation (default: 5432)

### Access token expired

Log in again. Tokens expire after 60 minutes (configurable in `backend/.env`).

### Frontend blank page

- Open browser DevTools (F12) → Console tab → check for errors
- Verify the backend is running on http://localhost:8000
- Verify `frontend/vite.config.js` has the correct API proxy configuration

---

## Environment Variables

### `backend/.env`

```ini
# PostgreSQL connection
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/farmer_procurement

# JWT configuration
JWT_SECRET=change-me-to-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OTP (demo mode returns OTP in API response)
OTP_DEMO_MODE=true
OTP_LENGTH=6
OTP_EXPIRY_SECONDS=300
OTP_MAX_ATTEMPTS=5
```

> **Never commit `.env` files.** The `.gitignore` excludes them automatically.

---

## License

MIT LICENSE

---

## Disclaimer

This project is an academic/prototype implementation built for demonstration purposes. Demo farmer data, payment records, bank details, and ML predictions are synthetic/demo data and are not official government records. The platform does not process real financial transactions.

---

*Built with React, FastAPI, and PostgreSQL. Designed for the farmers of Telangana.*

