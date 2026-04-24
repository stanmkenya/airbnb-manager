# Airbnb Property Manager

A full-stack web application for managing Airbnb properties, tracking expenses, income, and generating reports.

## Features

- **Multi-Property Management**: Manage unlimited listings from a single dashboard
- **Multi-Tenant Collections**: Organize properties into separate collections with isolated data
- **Expense Tracking**: Log daily expenses with hierarchical categories
- **Income & Booking Tracking**: Track bookings, calculate commissions, and monitor revenue
- **Blocked Dates**: Mark properties as unavailable for specific date ranges
- **Reports & Analytics**: Generate monthly summaries, P&L reports, occupancy rates, and more
- **Multi-User Support**: Role-based access control (Super Admin, Collection Admin, Manager, Viewer)
- **Firebase Authentication**: Gmail OAuth + email/password login with password reset
- **Export Capabilities**: Export data to PDF, Excel, and CSV formats
- **Real-time Data**: Cloud Firestore for instant updates and powerful queries

## Tech Stack

### Frontend
- **React 18** with **Vite** for fast development
- **Tailwind CSS** for styling
- **React Router** for navigation
- **React Query** for server state management
- **Zustand** for client state
- **Recharts** for data visualizations
- **Firebase Auth SDK** for authentication
- **Axios** for API requests

### Backend
- **Python 3.11+**
- **FastAPI** for REST API
- **Firebase Admin SDK** for auth verification and database access
- **WeasyPrint** for PDF generation
- **openpyxl** for Excel exports

### Infrastructure
- **Cloud Firestore** for data storage with multi-tenant collections
- **Firebase Authentication** for user management
- **Firebase Hosting** for frontend deployment
- **GitHub Actions** for CI/CD

## Prerequisites

- **Node.js 20+** and npm
- **Python 3.11+** and pip
- **Firebase account** and project
- **Git**

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd airbnb-manager
```

### 2. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Enable **Firebase Authentication**:
   - Go to Authentication > Sign-in method
   - Enable **Google** and **Email/Password** providers
4. Enable **Cloud Firestore**:
   - Go to Firestore Database > Create Database
   - Start in **production mode** (we'll deploy rules later)
   - Choose a location closest to your users
5. Generate a service account:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save the JSON file securely (DO NOT commit to git)
6. Get your Firebase config:
   - Go to Project Settings > General
   - Scroll to "Your apps" and select or add a web app
   - Copy the Firebase configuration object

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

Edit `frontend/.env` and add your Firebase config:

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-app.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `backend/.env`:

```env
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
ALLOWED_ORIGINS=http://localhost:3000
DEBUG=true
```

**Important**: Copy the entire contents of your Firebase service account JSON into `FIREBASE_SERVICE_ACCOUNT_JSON` on a single line.

### 5. Deploy Firebase Security Rules

```bash
# From project root
firebase deploy --only firestore:rules
```

This deploys the Firestore security rules in `firestore.rules`.

### 6. Run the Application

**Terminal 1 - Backend:**

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

The API will run on `http://localhost:8000`
- API docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

The app will run on `http://localhost:3000`

### 7. Create Your First Super Admin User

1. Open http://localhost:3000 in your browser
2. Sign up with email/password or Gmail
3. The first user should be assigned the 'superadmin' role
4. Go to Firebase Console > Firestore Database
5. Navigate to the `users` collection
6. Find your user document by UID
7. Set the `role` field to `'superadmin'`
8. As a Super Admin, you can now create collections and invite other users

## Deployment

### Deploy Frontend to Firebase Hosting

```bash
cd frontend

# Build the app
npm run build

# Deploy to Firebase
firebase deploy --only hosting
```

### Deploy Backend

The backend can be deployed to:
- **Railway**: Easy deployment with automatic HTTPS
- **Render**: Free tier available
- **Google Cloud Run**: Serverless option
- **AWS Lambda**: With Mangum adapter

Example for Railway:

1. Install Railway CLI
2. Run `railway login`
3. Run `railway init` in the backend folder
4. Add environment variables in Railway dashboard
5. Run `railway up`

### GitHub Actions CI/CD

The repository includes GitHub Actions workflows:

1. `.github/workflows/frontend.yml` - Auto-deploys frontend to Firebase Hosting on push to `main`
2. `.github/workflows/backend.yml` - Runs backend tests on pull requests

**Required GitHub Secrets:**

- `FIREBASE_SERVICE_ACCOUNT_JSON`
- `FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_API_BASE_URL`

## Project Structure

```
airbnb-manager/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── utils/           # Utility functions
│   │   ├── api/             # API client
│   │   └── store/           # State management
│   └── package.json
│
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── exports/         # PDF/Excel generators
│   │   └── core/            # Config, auth, CORS
│   ├── main.py
│   └── requirements.txt
│
├── .github/workflows/        # CI/CD pipelines
├── database.rules.json       # Firebase Security Rules
├── firebase.json             # Firebase configuration
└── README.md
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Expense Categories

- **Rent** (fixed monthly)
- **Cleaning** (fixed schedule 2×/week)
- **Breakfast Shopping**: Coffee, Sugar, Oil, Salt, Tea Leaves, Sweets, Other
- **Detergents**: Utensil Cleaner, Floor Cleaner, Bath/Toilet
- **Utilities**: Gas, Electricity, Water Bill, Wi-Fi, Water Refill
- **Waste**: Trash/Waste collection
- **Maintenance & Other**: Repairs, Furniture, Appliances, Renovations, Other

Admins can add custom categories from the settings panel.

## User Roles

| Role | Permissions |
|------|------------|
| **Super Admin** | Platform-wide access: manage all collections, all users, all data; create collections |
| **Collection Admin** | Full access within assigned collection: manage users, listings, reports, exports, settings |
| **Manager** | Assigned listings within collection; add/edit expenses and income; export own listings |
| **Viewer** | Read-only on assigned listings within collection; view reports and export |

## User Invitations

Admins can invite new users to the platform through the Users page:

1. Go to **Users** → Click **"Invite User"**
2. Fill in user details (email, name, role, collection)
3. System generates a password reset link
4. **Copy the link** and send it to the user (via email, Slack, etc.)
5. User clicks the link to set their password and can then sign in

**Email Automation (Optional):**
- Configure automatic email sending using SendGrid, Gmail SMTP, or AWS SES
- See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed setup instructions
- Works great for high-volume user invitations

**Manual Process (No Setup Required):**
- Just copy the link from the success screen and send it yourself
- Perfect for small teams or getting started quickly

## Security

- All API endpoints require Firebase ID token authentication
- Firestore Security Rules enforce collection-level and listing-level access at the database layer
- Multi-tenant data isolation through collection-based access control
- HTTPS enforced in production (Firebase Hosting provides TLS automatically)
- Service account credentials stored securely in environment variables
- Role-based access control implemented at both frontend and backend

## Troubleshooting

### Frontend won't connect to backend

- Check that `VITE_API_BASE_URL` in frontend `.env` points to your backend URL
- Ensure backend is running and accessible
- Check browser console for CORS errors

### "Invalid token" errors

- Make sure you're logged in
- Try logging out and back in to refresh your token
- Check that Firebase project ID matches in both frontend and backend configs

### Firebase permission denied

- Verify Firestore Security Rules are deployed: `firebase deploy --only firestore:rules`
- Check that your user has the correct role in Firestore
- Ensure user is assigned to a collection (`collectionId` field)
- Ensure user has appropriate `assignedListings` set within their collection

### Backend won't start

- Verify Python version is 3.11+
- Check that all environment variables are set in backend `.env`
- Ensure Firebase service account JSON is valid and properly formatted
- Check that virtual environment is activated

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is proprietary and confidential.

## Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for Airbnb property managers**