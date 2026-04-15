# Airbnb Property Manager — Product Requirements Document
**Version 1.2 | April 2026**

> **Stack at a glance**
> | Layer | Technology |
> |---|---|
> | Frontend | React + Vite → Firebase Hosting |
> | Backend | Python FastAPI |
> | Database | Firebase Realtime Database |
> | Auth | Firebase Auth (Gmail OAuth + Email/Password + Password Reset) |
> | Export | PDF (WeasyPrint) + Excel (openpyxl) |
> | CI/CD | GitHub Actions → Firebase Hosting |

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | April 2026 | Initial release |
| 1.1 | April 2026 | Auth updated to Firebase (Gmail OAuth + password reset). Database updated to Firebase Realtime DB. Architecture revised accordingly. |
| 1.2 | April 2026 | Hosting changed from Netlify to Firebase Hosting. All Netlify references removed. CI/CD updated to use Firebase CLI + GitHub Actions. |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Authentication & Security](#2-authentication--security)
3. [Users & Roles](#3-users--roles)
4. [Listings Management](#4-listings-management)
5. [Expense Tracking](#5-expense-tracking)
6. [Income & Booking Tracking](#6-income--booking-tracking)
7. [Reports & Analytics](#7-reports--analytics)
8. [Export Features](#8-export-features)
9. [Technical Architecture](#9-technical-architecture)
10. [Firebase Realtime Database Structure](#10-firebase-realtime-database-structure)
11. [Firebase Security Rules](#11-firebase-security-rules)
12. [Repository Structure](#12-repository-structure)
13. [API Endpoints](#13-api-endpoints)
14. [Non-Functional Requirements](#14-non-functional-requirements)
15. [Development Phases](#15-development-phases)
16. [Environment Variables](#16-environment-variables)
17. [Success Metrics](#17-success-metrics)

---

## 1. Project Overview

### 1.1 Problem Statement

Managing Airbnb income and expenses across 10+ listings in spreadsheets creates serious operational pain:

- No single source of truth — each manager maintains separate files
- Manual aggregation across listings is error-prone and slow
- No role-based access — anyone with the file sees everything
- No real-time visibility — reports are always stale
- Export and sharing requires tedious manual formatting

### 1.2 Solution

A full-stack web application that replaces spreadsheets with a centralised, real-time platform:

- **React + Vite** frontend deployed on **Firebase Hosting**
- **Python FastAPI** backend serving a REST API
- **Firebase Realtime Database** as the persistent data store
- **Firebase Authentication** handling Gmail OAuth, email/password login, and password resets
- **GitHub** repository with **CI/CD** pipeline auto-deploying to Firebase Hosting
- **PDF** and **Excel** export built into the backend

### 1.3 Scope — v1.0

**In scope:**
- Multi-listing management (unlimited listings)
- Daily expense entry with full category hierarchy
- Income and booking tracking per listing
- Monthly summary and cumulative daily reports
- Multi-user with roles: Admin, Property Manager, Viewer
- Gmail OAuth + email/password login + password reset
- Export to PDF and Excel
- Firebase Hosting deployment with GitHub Actions

**Out of scope for v1.0:**
- Direct Airbnb API integration
- Native mobile app (responsive web only)
- Accounting software integrations (QuickBooks, Xero)
- Automated bank feed import

---

## 2. Authentication & Security

> Firebase Authentication is used for all auth. This handles Gmail OAuth, email/password, session tokens, and password resets with zero custom auth code required.

### 2.1 Authentication Methods

#### Method 1 — Gmail / Google OAuth
- User clicks **"Continue with Google"** on the login page
- Firebase Auth opens the standard Google OAuth consent screen
- On success, Firebase issues an ID token and refresh token
- No password stored — Google manages the credential
- Display name and profile photo pulled from Google account automatically

#### Method 2 — Email + Password
- Users register with any email address and a password
- Passwords hashed and stored exclusively by Firebase — never in the app database
- Email verification sent on registration; account locked until verified
- Admins can invite users by email from the admin panel

#### Password Reset Flow
1. User clicks **"Forgot password?"** on the login screen
2. Enters their registered email address
3. Firebase sends a branded password reset email with a **1-hour** time-limited link
4. User clicks link → enters new password on Firebase-hosted reset page
5. On success, all existing sessions invalidated; user must log in again
6. Reset email template customised in Firebase Console with app name and logo

### 2.2 Session Management
- Firebase ID token used as `Bearer` token on all API requests
- ID token expires after **1 hour**; Firebase SDK auto-refreshes via refresh token
- FastAPI backend verifies Firebase ID token on every protected route using `firebase-admin` Python SDK
- On logout: frontend calls `Firebase.signOut()` and clears local token storage

### 2.3 Role Assignment

> Firebase Auth handles **who** the user is. The Firebase Realtime Database handles **what** they can access — roles and listing assignments stored in the DB.

| Role | Assigned By | Permissions |
|---|---|---|
| **Admin** | First user (auto) or another Admin | Full access: all listings, users, reports, exports, settings |
| **Property Manager** | Admin | Assigned listings only; add/edit expenses and income; export own listings |
| **Viewer** | Admin | Read-only on assigned listings; view reports and export |

### 2.4 Security Rules Summary
- Firebase Realtime Database Security Rules enforce listing-level access server-side
- HTTPS enforced everywhere (Firebase Hosting provides TLS automatically)
- CORS restricted to the Firebase Hosting frontend domain in production
- Firebase service account credentials stored in GitHub Secrets / Firebase Hosting env vars — **never committed to the repo**

### 2.5 Login Page UI Requirements
- Two clear options: **"Continue with Google"** (primary) and **"Sign in with email"** (secondary)
- Google sign-in button follows Google branding guidelines
- "Forgot password?" link visible on the email/password form
- Inline error messages: "Email not found", "Wrong password", "Account not verified"
- Redirect to originally requested URL after successful login
- Loading spinner during OAuth redirect

---

## 3. Users & Roles

### 3.1 User Stories

#### Admin
- As an Admin I can invite users by email and assign them a role and listings
- As an Admin I can view and edit all listings and all financial data
- As an Admin I can see a consolidated portfolio P&L across all listings
- As an Admin I can export full portfolio reports to PDF and Excel
- As an Admin I can configure expense categories globally
- As an Admin I can deactivate a user without deleting their historical data

#### Property Manager
- As a Property Manager I can log daily expenses for my assigned listings
- As a Property Manager I can log income and booking details
- As a Property Manager I can view monthly cumulative expense reports for my listings
- As a Property Manager I can export reports for my listings

#### Viewer
- As a Viewer I can view income, expenses, and reports for assigned listings
- As a Viewer I can export reports but cannot add or edit any data

---

## 4. Listings Management

### 4.1 Listing Data Fields

Each listing record contains:

| Field | Type | Notes |
|---|---|---|
| `id` | String | Auto-generated Firebase push key |
| `name` | String | e.g. "Beachfront Villa Unit 4" |
| `address` | String | Full property address |
| `airbnbUrl` | String | Optional |
| `defaultRate` | Number | Default nightly rate |
| `bedrooms` | Number | |
| `bathrooms` | Number | |
| `status` | Enum | `active` \| `inactive` |
| `assignedManagers` | Map | `{ uid: true }` |
| `createdBy` | String | User UID |
| `createdAt` | Timestamp | |

### 4.2 Multi-Listing Dashboard (Admin View)
- Total revenue across all listings — current month / YTD / custom range
- Total expenses and net income per listing in a sortable table
- Occupancy rate per listing (nights booked ÷ nights available)
- Quick filters: by listing, by month, by manager
- Colour-coded profit/loss indicators per listing

---

## 5. Expense Tracking

### 5.1 Daily Expense Entry Fields

| Field | Type | Notes |
|---|---|---|
| `listingId` | Dropdown | Scoped to user's assigned listings |
| `date` | Date picker | Defaults to today |
| `category` | Dropdown | Hierarchical — see 5.2 |
| `subCategory` | Dropdown | Auto-filtered by parent category |
| `amount` | Currency | Required; 2 decimal places |
| `notes` | Text | Optional free-text |
| `receiptRef` | Text | Optional receipt / invoice number |
| `enteredBy` | Auto | Firebase UID — read only |
| `createdAt` | Auto | Server timestamp — read only |

### 5.2 Expense Categories

| Parent Category | Sub-categories |
|---|---|
| Rent | *(none — fixed monthly)* |
| Cleaning | *(none — fixed schedule 2×/week)* |
| Breakfast Shopping | Coffee · Sugar · Oil · Salt · Tea Leaves · Sweets · Other |
| Detergents | Utensil Cleaner · Floor Cleaner · Bath/Toilet |
| Utilities | Gas · Electricity · Water Bill · Wi-Fi · Water Refill |
| Waste | Trash / Waste collection |
| Maintenance & Other | Repairs · Furniture · Appliances · Renovations · Other |

> Admins can add custom categories from the settings panel.

### 5.3 Bulk Entry
- Upload a CSV of expenses for a listing and date range
- CSV template downloadable from the app
- Validation errors shown before import is confirmed

### 5.4 Edit, Delete & Audit
- Managers can edit/delete their own entries within **30 days**
- Admins can edit/delete any entry at any time
- All edits written to `audit_log` node in Firebase with old + new values, user UID, and timestamp

---

## 6. Income & Booking Tracking

### 6.1 Booking Entry Fields

| Field | Type | Notes |
|---|---|---|
| `listingId` | Dropdown | Assigned listings |
| `guestName` | String | Required |
| `guestPhone` | String | Optional |
| `guestEmail` | String | Optional |
| `checkIn` | Date | Required |
| `checkOut` | Date | Required |
| `nights` | Auto | `checkOut - checkIn` |
| `nightlyRate` | Currency | Required |
| `totalPaid` | Currency | Auto: `nights × rate`; editable override |
| `platform` | Dropdown | Airbnb / Booking.com / Direct / VRBO / Other |
| `commissionPaid` | Currency | Platform fee deducted |
| `netIncome` | Auto | `totalPaid - commissionPaid` |
| `commissionPct` | Auto | `commissionPaid ÷ totalPaid` |
| `notes` | String | Optional |
| `enteredBy` | Auto | Firebase UID |
| `createdAt` | Auto | Server timestamp |

### 6.2 Guest Directory
- Searchable across all listings (Admins) or assigned listings (Managers)
- Each guest links to their full booking history
- Exportable to Excel / CSV

### 6.3 Booking Calendar View
- Visual per-listing calendar: booked / available / blocked nights
- Colour-coded by platform (Airbnb, Booking.com, Direct, etc.)
- Click a booking to view details inline

---

## 7. Reports & Analytics

### 7.1 Report Types

| Report | Description |
|---|---|
| Daily Expense Log | All expenses for a listing in a date range; filterable by category |
| Monthly Summary | Expense totals by category per month + annual roll-up |
| Monthly Cumulative | Running daily total per month — shows spend build-up day by day |
| Income Statement | Revenue, commission, net income per listing per month |
| P&L by Listing | Side-by-side profit/loss for each listing; sortable |
| Portfolio P&L | Consolidated P&L across all listings for a period (Admin only) |
| Occupancy Report | Nights booked vs available; occupancy % by month |
| Category Breakdown | Pie/bar chart of spend by category |
| Year-over-Year | Income and expense comparison across calendar years |

### 7.2 Report Filters
- **Listing** — one, many, or all (scoped by role)
- **Date range** — custom, or quick-select: This Month / Last Month / This Quarter / YTD / Last Year
- **Category** — expense reports
- **Property Manager** — Admin only
- **Platform** — income reports

### 7.3 Data Visualisations
- Monthly revenue vs expenses bar chart (per listing or portfolio)
- Net income trend line
- Expense category pie chart
- Occupancy rate heatmap calendar
- Commission % by platform comparison

> Charts rendered with **Recharts**. All charts exportable as PNG.

---

## 8. Export Features

### 8.1 PDF Export
- Any report page exportable to a formatted PDF
- PDF includes: listing name, report title, date range, generated-by, timestamp
- Generated server-side with **WeasyPrint** (Python)
- Consistent branding: app name, colour scheme, formatted tables

### 8.2 Excel Export
- Expense log or income log per listing → `.xlsx`
- Monthly summary (categories × months) → `.xlsx`
- Portfolio P&L (all listings × all months) → `.xlsx`
- Generated with **openpyxl**; colour-coded headers, currency formatting, totals rows

### 8.3 CSV Export
- Raw expense or booking data → `.csv`
- Compatible with accounting tools and third-party import

---

## 9. Technical Architecture

### 9.1 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + Vite | SPA; fast HMR in dev; optimised prod build |
| Styling | Tailwind CSS | Utility-first responsive design |
| Charts | Recharts | D3-based React charting |
| State / Cache | React Query + Zustand | Server data cache + client UI state |
| Auth (client) | Firebase Auth JS SDK | Gmail OAuth + email/password + password reset |
| Hosting | Firebase Hosting | Global CDN, HTTPS, CI/CD, URL rewrites for SPA |
| Backend | Python FastAPI | REST API; async; auto Swagger docs at `/docs` |
| Auth (server) | firebase-admin SDK | ID token verification on every route |
| Database | Firebase Realtime Database | JSON tree; real-time sync; no schema migrations |
| DB Access (backend) | firebase-admin Python SDK | Read/write Realtime DB from FastAPI |
| DB Rules | Firebase Security Rules | Listing-level access enforced at DB layer |
| PDF Export | WeasyPrint | Server-side HTML → PDF |
| Excel Export | openpyxl | Formatted `.xlsx` generation |
| CI/CD | GitHub Actions → Firebase Hosting | Auto-deploy on merge to `main` |

---

## 10. Firebase Realtime Database Structure

```json
{
  "users": {
    "{uid}": {
      "email": "string",
      "displayName": "string",
      "photoURL": "string",
      "role": "admin | manager | viewer",
      "assignedListings": { "{listingId}": true },
      "createdAt": "timestamp",
      "lastLogin": "timestamp",
      "isActive": true
    }
  },

  "listings": {
    "{listingId}": {
      "name": "string",
      "address": "string",
      "airbnbUrl": "string",
      "defaultRate": 0,
      "bedrooms": 0,
      "bathrooms": 0,
      "status": "active | inactive",
      "assignedManagers": { "{uid}": true },
      "createdBy": "{uid}",
      "createdAt": "timestamp"
    }
  },

  "expenses": {
    "{listingId}": {
      "{expenseId}": {
        "date": "YYYY-MM-DD",
        "category": "string",
        "subCategory": "string",
        "amount": 0.00,
        "notes": "string",
        "receiptRef": "string",
        "enteredBy": "{uid}",
        "createdAt": "timestamp",
        "updatedAt": "timestamp"
      }
    }
  },

  "bookings": {
    "{listingId}": {
      "{bookingId}": {
        "guestName": "string",
        "guestPhone": "string",
        "guestEmail": "string",
        "checkIn": "YYYY-MM-DD",
        "checkOut": "YYYY-MM-DD",
        "nights": 0,
        "nightlyRate": 0.00,
        "totalPaid": 0.00,
        "platform": "Airbnb | Booking.com | Direct | VRBO | Other",
        "commissionPaid": 0.00,
        "netIncome": 0.00,
        "commissionPct": 0.00,
        "notes": "string",
        "enteredBy": "{uid}",
        "createdAt": "timestamp"
      }
    }
  },

  "categories": {
    "{categoryId}": {
      "name": "string",
      "parentId": "string | null",
      "isDefault": true,
      "createdBy": "{uid}"
    }
  },

  "audit_log": {
    "{logId}": {
      "table": "expenses | bookings | listings | users",
      "recordId": "string",
      "action": "create | update | delete",
      "changedBy": "{uid}",
      "oldValues": {},
      "newValues": {},
      "timestamp": "timestamp"
    }
  }
}
```

---

## 11. Firebase Security Rules

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read":  "$uid === auth.uid || root.child('users/'+auth.uid+'/role').val() === 'admin'",
        ".write": "root.child('users/'+auth.uid+'/role').val() === 'admin'"
      }
    },

    "listings": {
      ".read":  "auth != null",
      ".write": "auth != null && root.child('users/'+auth.uid+'/role').val() === 'admin'"
    },

    "expenses": {
      "$listingId": {
        ".read": "auth != null && (
                    root.child('users/'+auth.uid+'/role').val() === 'admin' ||
                    root.child('users/'+auth.uid+'/assignedListings/'+$listingId).exists()
                  )",
        ".write": "auth != null && (
                    root.child('users/'+auth.uid+'/role').val() === 'admin' ||
                    (root.child('users/'+auth.uid+'/role').val() === 'manager' &&
                     root.child('users/'+auth.uid+'/assignedListings/'+$listingId).exists())
                  )"
      }
    },

    "bookings": {
      "$listingId": {
        ".read": "auth != null && (
                    root.child('users/'+auth.uid+'/role').val() === 'admin' ||
                    root.child('users/'+auth.uid+'/assignedListings/'+$listingId).exists()
                  )",
        ".write": "auth != null && (
                    root.child('users/'+auth.uid+'/role').val() === 'admin' ||
                    (root.child('users/'+auth.uid+'/role').val() === 'manager' &&
                     root.child('users/'+auth.uid+'/assignedListings/'+$listingId).exists())
                  )"
      }
    },

    "categories": {
      ".read":  "auth != null",
      ".write": "auth != null && root.child('users/'+auth.uid+'/role').val() === 'admin'"
    },

    "audit_log": {
      ".read":  "auth != null && root.child('users/'+auth.uid+'/role').val() === 'admin'",
      ".write": "auth != null"
    }
  }
}
```

---

## 12. Repository Structure

```
airbnb-manager/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # Button, Input, Modal, Toast, Table …
│   │   │   ├── charts/              # RevenueChart, ExpensePieChart …
│   │   │   ├── forms/               # ExpenseForm, BookingForm …
│   │   │   └── layout/              # Sidebar, Navbar, PageWrapper
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx        # Portfolio overview (Admin)
│   │   │   ├── Listings.jsx
│   │   │   ├── Expenses.jsx
│   │   │   ├── Income.jsx
│   │   │   ├── Reports.jsx
│   │   │   ├── GuestDirectory.jsx
│   │   │   └── Admin.jsx            # User management
│   │   ├── hooks/
│   │   │   ├── useAuth.js           # Firebase Auth state
│   │   │   ├── useListings.js
│   │   │   ├── useExpenses.js
│   │   │   └── useBookings.js
│   │   ├── store/
│   │   │   └── appStore.js          # Zustand global state
│   │   ├── api/
│   │   │   └── client.js            # Axios instance; attaches Firebase ID token
│   │   ├── firebase.js              # Firebase app init + Auth + DB exports
│   │   └── utils/
│   │       ├── formatCurrency.js
│   │       ├── dateHelpers.js
│   │       └── roleGuard.js
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py              # Token verify; user profile
│   │   │   ├── listings.py
│   │   │   ├── expenses.py
│   │   │   ├── income.py
│   │   │   ├── reports.py
│   │   │   ├── export.py            # PDF + Excel endpoints
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── expense_service.py
│   │   │   ├── income_service.py
│   │   │   ├── report_service.py
│   │   │   └── user_service.py
│   │   ├── exports/
│   │   │   ├── pdf_export.py        # WeasyPrint PDF generation
│   │   │   └── excel_export.py      # openpyxl Excel generation
│   │   ├── firebase_client.py       # firebase-admin singleton init
│   │   └── core/
│   │       ├── config.py            # Env var loading
│   │       ├── auth.py              # FastAPI dependency: verify_token
│   │       └── cors.py
│   ├── tests/
│   │   ├── test_expenses.py
│   │   ├── test_income.py
│   │   └── test_reports.py
│   ├── main.py
│   └── requirements.txt
│
├── .github/
│   └── workflows/
│       ├── frontend.yml             # Build Vite app + firebase deploy --only hosting
│       └── backend.yml              # Run pytest on every PR
│
├── firebase.toml                     # Build config + redirect rules
├── firebase.json                    # Firebase project config
├── database.rules.json              # Realtime DB security rules (deploy via CLI)
├── .env.example                     # Template — copy to .env, never commit .env
└── README.md
```

---

## 13. API Endpoints

All endpoints require `Authorization: Bearer {firebase_id_token}` unless noted.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/verify` | Verify Firebase ID token; return user profile + role from DB |
| `PUT` | `/auth/profile` | Update display name / preferences |

### Listings
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/listings` | List all listings scoped by user role |
| `POST` | `/listings` | Create listing *(Admin only)* |
| `GET` | `/listings/{id}` | Get listing detail |
| `PUT` | `/listings/{id}` | Update listing *(Admin only)* |
| `DELETE` | `/listings/{id}` | Soft-delete listing *(Admin only)* |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/expenses` | List expenses — query params: `listingId`, `from`, `to`, `category` |
| `POST` | `/expenses` | Add expense entry |
| `GET` | `/expenses/{id}` | Get single expense |
| `PUT` | `/expenses/{id}` | Edit expense |
| `DELETE` | `/expenses/{id}` | Delete expense |
| `POST` | `/expenses/bulk` | Bulk import from CSV |

### Income / Bookings
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/income` | List bookings — query params: `listingId`, `from`, `to`, `platform` |
| `POST` | `/income` | Add booking |
| `GET` | `/income/{id}` | Get single booking |
| `PUT` | `/income/{id}` | Edit booking |
| `DELETE` | `/income/{id}` | Delete booking |

### Reports
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reports/monthly-summary` | Expense totals by category per month |
| `GET` | `/reports/cumulative` | Daily running totals per month |
| `GET` | `/reports/pnl` | P&L by listing for a date range |
| `GET` | `/reports/portfolio` | Consolidated portfolio P&L *(Admin only)* |
| `GET` | `/reports/occupancy` | Occupancy rate per listing |
| `GET` | `/reports/yoy` | Year-over-year comparison |

### Export
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/export/excel` | Download `.xlsx` — query params: `listingId`, `type`, `from`, `to` |
| `GET` | `/export/pdf` | Download PDF — same query params |
| `GET` | `/export/csv` | Download raw CSV |

### Users *(Admin only)*
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users` | List all users |
| `POST` | `/users/invite` | Send Firebase invite email; set role in DB |
| `PUT` | `/users/{uid}/role` | Change user role |
| `PUT` | `/users/{uid}/listings` | Update listing assignments |
| `PUT` | `/users/{uid}/deactivate` | Deactivate user |

---

## 14. Non-Functional Requirements

### 14.1 Performance
- Report pages load in under **2 seconds** for up to 10,000 records
- API responses under **500 ms** for standard queries
- PDF/Excel export completes in under **10 seconds**
- Firebase DB indexed on `listingId` + `date` for fast filtering

### 14.2 Security
- All FastAPI routes require a valid Firebase ID token (verified via `firebase-admin`)
- Firebase Security Rules enforce listing-level data isolation at the database layer
- HTTPS enforced on all environments (Firebase Hosting TLS + backend behind HTTPS)
- Firebase service account JSON stored in GitHub Secrets / Firebase Hosting env — never committed
- CORS restricted to Firebase Hosting domain in production

### 14.3 Availability
- Frontend: **99.95% uptime** via Firebase Hosting global CDN (Google-managed)
- Firebase Realtime DB: **99.95% SLA** (Google-managed)
- Backend: hosted on Railway or Render with auto-restart on crash

### 14.4 Scalability
- Firebase Realtime DB scales automatically — no capacity planning required
- Stateless FastAPI backend — horizontally scalable
- Pagination on all list endpoints (default: 50 records per page)

### 14.5 Usability
- Responsive design — desktop, tablet, mobile
- Expense entry completable in under **30 seconds**
- All tables sortable and filterable in UI
- Toast notifications for all create / edit / delete actions

---

## 15. Development Phases

### Phase 1 — Foundation
- [ ] Create GitHub repo with monorepo structure
- [ ] Scaffold `frontend/` with Vite + React + Tailwind
- [ ] Scaffold `backend/` with FastAPI skeleton
- [ ] Set up Firebase project (Auth + Realtime DB)
- [ ] Implement Firebase Auth: Gmail OAuth + email/password + password reset
- [ ] Build Login page UI (Google button + email form + forgot password)
- [ ] Implement `verify_token` FastAPI dependency using `firebase-admin`
- [ ] Configure Firebase Hosting + `firebase.toml` + GitHub Actions CI/CD
- [ ] Set up `.env.example` with all required variables

### Phase 2 — Listings & Users
- [ ] Listing CRUD (Admin)
- [ ] User management panel (invite, assign role, assign listings)
- [ ] Role-based route guards in React (`<RoleGuard role="admin">`)
- [ ] Firebase Security Rules v1 deployed
- [ ] Property Manager dashboard (assigned listings only)

### Phase 3 — Expenses
- [ ] Daily expense entry form with hierarchical category dropdown
- [ ] Expense list page with filters (listing, date range, category)
- [ ] Edit / delete with 30-day rule for managers
- [ ] Audit log writes to Firebase on every change
- [ ] CSV bulk import endpoint + UI

### Phase 4 — Income & Bookings
- [ ] Booking entry form (all fields, auto-calculations)
- [ ] Booking list with filters (listing, date, platform)
- [ ] Guest directory page (search + export)
- [ ] Booking calendar view

### Phase 5 — Reports
- [ ] Monthly expense summary table
- [ ] Monthly cumulative daily report
- [ ] P&L by listing
- [ ] Portfolio P&L (Admin)
- [ ] Occupancy report
- [ ] All Recharts visualisations
- [ ] Report filter bar (date range, listing, category, platform)

### Phase 6 — Export
- [ ] Excel export via `openpyxl` (expense log, monthly summary, portfolio P&L)
- [ ] PDF export via `WeasyPrint` (any report)
- [ ] CSV raw export
- [ ] Download endpoints in FastAPI + download buttons in UI

### Phase 7 — Polish & Launch
- [ ] End-to-end tests (Playwright or Cypress)
- [ ] Backend unit tests (pytest) — all routers
- [ ] Firebase Security Rules hardening + penetration test
- [ ] README with full setup guide
- [ ] Firebase Hosting production deploy + custom domain (optional)
- [ ] Firebase App Check setup (optional v2 hardening)

---

## 16. Environment Variables

### Frontend (`frontend/.env`)

```bash
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
VITE_FIREBASE_DATABASE_URL=https://your-app-default-rtdb.firebaseio.com
VITE_FIREBASE_PROJECT_ID=your-app
VITE_FIREBASE_STORAGE_BUCKET=your-app.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_API_BASE_URL=https://your-backend.railway.app
```

### Backend (`backend/.env`)

```bash
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account", ...}
FIREBASE_DATABASE_URL=https://your-app-default-rtdb.firebaseio.com
ALLOWED_ORIGINS=https://your-app.firebase.app
```


### Firebase Hosting config (`firebase.json`)

```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      { "source": "**", "destination": "/index.html" }
    ]
  }
}
```

> The `rewrites` rule is critical — it routes all URLs to `index.html` so React Router handles navigation on the client side.


### GitHub Actions workflow (`.github/workflows/frontend.yml`)

```yaml
name: Deploy to Firebase Hosting

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install and build
        working-directory: frontend
        env:
          VITE_FIREBASE_API_KEY: ${{ secrets.VITE_FIREBASE_API_KEY }}
          VITE_FIREBASE_AUTH_DOMAIN: ${{ secrets.VITE_FIREBASE_AUTH_DOMAIN }}
          VITE_FIREBASE_DATABASE_URL: ${{ secrets.VITE_FIREBASE_DATABASE_URL }}
          VITE_FIREBASE_PROJECT_ID: ${{ secrets.VITE_FIREBASE_PROJECT_ID }}
          VITE_FIREBASE_STORAGE_BUCKET: ${{ secrets.VITE_FIREBASE_STORAGE_BUCKET }}
          VITE_FIREBASE_MESSAGING_SENDER_ID: ${{ secrets.VITE_FIREBASE_MESSAGING_SENDER_ID }}
          VITE_FIREBASE_APP_ID: ${{ secrets.VITE_FIREBASE_APP_ID }}
          VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
        run: |
          npm ci
          npm run build

      - name: Deploy to Firebase Hosting
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_JSON }}
          channelId: live
          projectId: ${{ secrets.FIREBASE_PROJECT_ID }}
```

### GitHub Secrets (CI/CD)

```
FIREBASE_TOKEN
FIREBASE_PROJECT_ID
FIREBASE_SERVICE_ACCOUNT_JSON
```

> **Never commit `.env` files.** All secrets go in GitHub Secrets or Firebase Hosting environment settings.

---

## 17. Success Metrics

- [ ] All 10+ listings manageable from a single login
- [ ] Gmail OAuth login completes in under 5 seconds including Google consent screen
- [ ] Password reset email delivered and functional within 60 seconds
- [ ] Expense entry completable in under 30 seconds per transaction
- [ ] Monthly P&L report accessible with 2 clicks
- [ ] PDF and Excel exports generated in under 10 seconds
- [ ] Firebase Security Rules pass review — no cross-listing data leakage
- [ ] CI/CD pipeline auto-deploys to Firebase Hosting within 3 minutes of merge to `main`
- [ ] Zero data loss — Firebase managed backups active

---

*Airbnb Property Manager — PRD v1.1 | April 2026 | Confidential — Internal Use Only*
