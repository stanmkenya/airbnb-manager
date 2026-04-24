# Airbnb Property Manager — Product Requirements Document
**Version 1.3 | April 2026**

> **Stack at a glance**
> | Layer | Technology |
> |---|---|
> | Frontend | React + Vite → Firebase Hosting |
> | Backend | Python FastAPI |
> | Database | **Cloud Firestore** |
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
| 1.3 | April 2026 | **Database migrated from Firebase Realtime DB to Cloud Firestore**. **Multi-tenant Collections architecture implemented**. **Super Admin role added** (distinct from Collection Admin). Blocked dates feature added. |

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
10. [Cloud Firestore Database Structure](#10-cloud-firestore-database-structure)
11. [Firestore Security Rules](#11-firestore-security-rules)
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
- **Cloud Firestore** as the persistent data store with multi-tenant collections architecture
- **Firebase Authentication** handling Gmail OAuth, email/password login, and password resets
- **GitHub** repository with **CI/CD** pipeline auto-deploying to Firebase Hosting
- **PDF** and **Excel** export built into the backend
- **Multi-tenant Collections** system for managing multiple property groups with isolated data

### 1.3 Scope — v1.0

**In scope:**
- Multi-listing management (unlimited listings)
- **Multi-tenant Collections** for managing multiple property groups
- Daily expense entry with full category hierarchy
- Income and booking tracking per listing
- **Blocked dates** management for property availability
- Monthly summary and cumulative daily reports
- Multi-user with roles: **Super Admin**, **Collection Admin**, Property Manager, Viewer
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

> Firebase Auth handles **who** the user is. Cloud Firestore handles **what** they can access — roles, collection assignments, and listing assignments stored in the DB.

**Multi-Tenant Architecture:**
- Users are assigned to a **Collection** (a group of properties)
- Each collection has isolated data (listings, expenses, bookings)
- Collections enable managing multiple independent property groups in one platform

| Role | Assigned By | Permissions |
|---|---|---|
| **Super Admin** | System (first user) or another Super Admin | Platform-wide access: all collections, all users, all data; create/manage collections |
| **Collection Admin** | Super Admin | Full access within assigned collection: manage users, listings, reports, exports, settings; cannot access other collections |
| **Property Manager** | Super Admin or Collection Admin | Assigned listings within their collection only; add/edit expenses and income; export own listings |
| **Viewer** | Super Admin or Collection Admin | Read-only on assigned listings within their collection; view reports and export |

### 2.4 Security Rules Summary
- **Firestore Security Rules** enforce collection-level and listing-level access server-side
- Multi-tenant data isolation through collection-based access control
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

#### Super Admin
- As a Super Admin I can create and manage multiple collections (property groups)
- As a Super Admin I can invite users to any collection and assign them roles
- As a Super Admin I can view and edit all collections, listings, and financial data across the platform
- As a Super Admin I can see consolidated reports across all collections
- As a Super Admin I can configure expense categories globally
- As a Super Admin I can promote/demote users and deactivate accounts

#### Collection Admin
- As a Collection Admin I can invite users to my collection and assign them roles
- As a Collection Admin I can view and edit all listings and financial data within my collection
- As a Collection Admin I can see a consolidated portfolio P&L across all listings in my collection
- As a Collection Admin I can export full collection reports to PDF and Excel
- As a Collection Admin I can deactivate users within my collection without deleting their historical data

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
| Database | **Cloud Firestore** | Document/collection model; real-time sync; built-in indexing; multi-tenant collections |
| DB Access (backend) | firebase-admin Python SDK | Read/write Firestore from FastAPI |
| DB Rules | **Firestore Security Rules** | Collection-level + listing-level access enforced at DB layer |
| PDF Export | WeasyPrint | Server-side HTML → PDF |
| Excel Export | openpyxl | Formatted `.xlsx` generation |
| CI/CD | GitHub Actions → Firebase Hosting | Auto-deploy on merge to `main` |

---

## 10. Cloud Firestore Database Structure

**Multi-Tenant Collections Architecture:**
The database uses a hierarchical structure where data is organized into collections for multi-tenancy.

```
/users (collection)
  /{uid} (document)
    - email: string
    - displayName: string
    - photoURL: string
    - role: "superadmin" | "collection_admin" | "manager" | "viewer"
    - collectionId: string (reference to assigned collection)
    - assignedListings: { "{listingId}": true }
    - createdAt: timestamp
    - createdBy: string (uid)
    - lastLogin: timestamp
    - isActive: boolean

/collections (collection)
  /{collectionId} (document)
    - name: string
    - description: string
    - isActive: boolean
    - createdAt: timestamp
    - createdBy: string (email)
    - updatedAt: timestamp
    - userCount: number

  /{collectionId}/listings (subcollection)
    /{listingId} (document)
      - name: string
      - address: string
      - airbnbUrl: string
      - defaultRate: number
      - bedrooms: number
      - bathrooms: number
      - status: "active" | "inactive"
      - assignedManagers: { "{uid}": true }
      - createdBy: string (uid)
      - createdAt: timestamp
      - updatedAt: timestamp

  /{collectionId}/expenses (subcollection)
    /{expenseId} (document)
      - listingId: string
      - date: "YYYY-MM-DD"
      - category: string
      - subCategory: string
      - amount: number
      - notes: string
      - receiptRef: string
      - enteredBy: string (uid)
      - createdAt: timestamp
      - updatedAt: timestamp

  /{collectionId}/bookings (subcollection)
    /{bookingId} (document)
      - listingId: string
      - guestName: string
      - guestPhone: string
      - guestEmail: string
      - checkIn: "YYYY-MM-DD"
      - checkOut: "YYYY-MM-DD"
      - nights: number
      - nightlyRate: number
      - totalPaid: number
      - platform: "Airbnb" | "Booking.com" | "Direct" | "VRBO" | "Other"
      - commissionPaid: number
      - netIncome: number
      - commissionPct: number
      - notes: string
      - enteredBy: string (uid)
      - createdAt: timestamp
      - updatedAt: timestamp

  /{collectionId}/blocked-dates (subcollection)
    /{dateId} (document)
      - listingId: string
      - startDate: "YYYY-MM-DD"
      - endDate: "YYYY-MM-DD"
      - reason: string
      - createdBy: string (uid)
      - createdAt: timestamp

/categories (collection - global)
  /{categoryId} (document)
    - name: string
    - parentId: string | null
    - isDefault: boolean
    - createdBy: string (uid)

/audit_log (collection)
  /{logId} (document)
    - table: "expenses" | "bookings" | "listings" | "users" | "collections"
    - recordId: string
    - collectionId: string
    - action: "create" | "update" | "delete"
    - changedBy: string (uid)
    - oldValues: map
    - newValues: map
    - timestamp: timestamp
```

**Key Changes from Realtime Database:**
- Multi-tenant architecture with collections as top-level containers
- Listings, expenses, bookings, and blocked dates are subcollections within each collection
- Users reference their assigned collection via `collectionId` field
- Firestore document/collection structure instead of JSON tree
- Built-in indexing and querying capabilities

---

## 11. Firestore Security Rules

**Multi-Tenant Security Model:**
Firestore security rules enforce collection-level data isolation and role-based access control.

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {

    // Helper functions
    function isSignedIn() {
      return request.auth != null;
    }

    function getUserData() {
      return get(/databases/$(database)/documents/users/$(request.auth.uid)).data;
    }

    function isSuperAdmin() {
      return isSignedIn() && getUserData().role == 'superadmin';
    }

    function isCollectionAdmin() {
      return isSignedIn() && getUserData().role == 'collection_admin';
    }

    function belongsToCollection(collectionId) {
      return isSignedIn() && getUserData().collectionId == collectionId;
    }

    // Users collection
    match /users/{userId} {
      // Users can read their own profile
      allow read: if isSignedIn() && request.auth.uid == userId;

      // Superadmins can read all users
      allow read: if isSuperAdmin();

      // Users can update their own profile (limited fields)
      allow update: if isSignedIn() &&
                       request.auth.uid == userId &&
                       request.resource.data.diff(resource.data)
                         .affectedKeys().hasOnly(['lastLogin', 'displayName', 'photoURL', 'updatedAt']);

      // Superadmins can update any user
      allow update: if isSuperAdmin();

      // Only superadmins can create or delete users
      allow create, delete: if isSuperAdmin();
    }

    // Collections - multi-tenant data structure
    match /collections/{collectionId} {
      // Superadmins can read/write all collections
      allow read, write: if isSuperAdmin();

      // Collection admins can read/write their own collection
      allow read, write: if isCollectionAdmin() && belongsToCollection(collectionId);

      // Regular users can read their collection
      allow read: if belongsToCollection(collectionId);

      // Listings subcollection
      match /listings/{listingId} {
        allow read, write: if isSuperAdmin();
        allow read, write: if isCollectionAdmin() && belongsToCollection(collectionId);
        allow read: if belongsToCollection(collectionId);
      }

      // Expenses subcollection
      match /expenses/{expenseId} {
        allow read, write: if isSuperAdmin();
        allow read, write: if belongsToCollection(collectionId);
      }

      // Bookings subcollection
      match /bookings/{bookingId} {
        allow read, write: if isSuperAdmin();
        allow read, write: if belongsToCollection(collectionId);
      }

      // Blocked dates subcollection
      match /blocked-dates/{dateId} {
        allow read, write: if isSuperAdmin();
        allow read, write: if belongsToCollection(collectionId);
      }
    }

    // Categories collection (global)
    match /categories/{categoryId} {
      allow read: if isSignedIn();
      allow write: if isSuperAdmin();
    }

    // Audit log (admin only)
    match /audit_log/{logId} {
      allow read: if isSuperAdmin();
      allow write: if isSignedIn();
    }
  }
}
```

**Key Security Features:**
- Collection-based data isolation prevents cross-collection access
- Super Admins have platform-wide access
- Collection Admins have full access only within their assigned collection
- Regular users (managers, viewers) can only access data in their assigned collection
- Helper functions provide reusable role-checking logic

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

### Collections *(New in v1.3)*
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/collections` | List all collections (Super Admin) or user's collection (others) |
| `GET` | `/collections/{id}` | Get specific collection details |
| `POST` | `/collections` | Create new collection *(Super Admin only)* |
| `PUT` | `/collections/{id}` | Update collection *(Super Admin or Collection Admin)* |
| `DELETE` | `/collections/{id}` | Delete collection *(Super Admin only)* |

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

### Blocked Dates *(New in v1.3)*
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/blocked-dates` | List blocked dates — query params: `listingId`, `from`, `to` |
| `POST` | `/blocked-dates` | Add blocked date range |
| `GET` | `/blocked-dates/{id}` | Get single blocked date entry |
| `PUT` | `/blocked-dates/{id}` | Edit blocked date |
| `DELETE` | `/blocked-dates/{id}` | Delete blocked date |

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
