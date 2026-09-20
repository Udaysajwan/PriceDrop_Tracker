# 🏷️ Price Drop Tracker & Alert API

A full-stack, production-ready system for tracking e-commerce product prices over time, alerting users when prices hit target thresholds, and visualizing price trends with interactive charts.

Built with **FastAPI**, **Google Cloud Firestore (Firebase)**, **APScheduler**, and **Chart.js**, following the 4-week build roadmap.

---

## ✨ Features

- **Google Cloud Firestore (Firebase)**: Scalable NoSQL document store with subcollections for historical price points.
- **Zero-Blocker Development Mode**: Includes an automatic Mock Firestore fallback so the app and test suite run immediately even before downloading your Firebase service account key.
- **Automated Price Tracking**: Tracks product URLs periodically via background scheduler (APScheduler).
- **Intelligent Web Scraper**: Universal parser extracting price, title, image, and stock status from JSON-LD schema, OpenGraph tags, and fallback HTML CSS selectors.
- **Price Drop Alerts**: Automatically detects when `current_price <= target_price`, logs alerts, and dispatches email notifications (via SMTP).
- **Historical Trends & Analytics**: Records price movements in `products/{id}/history` subcollections; calculates minimum, maximum, average prices, and overall percentage changes.
- **Interactive Visualizations**: Clean single-page dashboard with Chart.js line charts rendering price changes over time against a target threshold.
- **JWT Authentication**: User registration and login with bcrypt password hashing; all tracked products are securely scoped to their owner.
- **Built-in Mock Store**: Includes mock e-commerce pages with a dynamic price simulator so you can test price drops and triggers instantly without third-party rate limits.

---

## 🏗️ Architecture & Firestore Schema

```
Firestore Collections Hierarchy:
================================

 users/ (Collection)
   └── {userId}/ (Document)
         ├── id: string
         ├── email: string
         ├── hashed_password: string
         ├── is_active: boolean
         └── created_at: timestamp

 products/ (Collection)
   └── {productId}/ (Document)
         ├── id: string
         ├── user_id: string (Reference to users)
         ├── title: string
         ├── url: string
         ├── target_price: float
         ├── current_price: float
         ├── currency: string
         ├── image_url: string
         ├── in_stock: boolean
         ├── last_scraped_at: timestamp
         ├── created_at: timestamp
         ├── updated_at: timestamp
         │
         └── history/ (Subcollection)
               └── {historyId}/ (Document)
                     ├── id: string
                     ├── product_id: string
                     ├── price: float
                     └── scraped_at: timestamp
```

---

## 🛠️ Tech Stack

| Layer | Language / Tool | Purpose |
| :--- | :--- | :--- |
| **Backend Logic** | Python 3.13+ | Scraping, business rules, alerts, hashing |
| **API Framework** | FastAPI (Pydantic v2) | REST endpoints, OpenAPI documentation (`/docs`) |
| **Database** | Google Cloud Firestore (Firebase) | NoSQL document storage & subcollections |
| **SDK** | `firebase-admin` | Official Python Firebase Admin SDK |
| **Scheduling** | APScheduler | Periodic automated price checks |
| **Frontend** | HTML5, CSS3, Vanilla JS | Clean responsive UI, fetch API integration |
| **Charts** | Chart.js | Visualizing price trend curves vs target price |
| **Auth** | JWT (`python-jose` + `bcrypt`) | Secure password hashing and token authentication |

---

## 🔥 Setting Up Firebase Cloud Firestore

1. **Create a Project**:
   - Go to [https://console.firebase.google.com/](https://console.firebase.google.com/) and click **Add project**.
2. **Create Firestore Database**:
   - In the left sidebar, click **Build** > **Firestore Database**.
   - Click **Create database**, choose a location, and select **Start in test mode** (or production mode).
3. **Generate Service Account Key**:
   - Click the ⚙️ **Gear icon** (Project Settings) > **Service accounts** tab.
   - Click **Generate new private key**, then click **Generate key**.
   - A JSON file will download.
4. **Place Key in Project**:
   - Rename the downloaded file to `firebase-credentials.json` and put it in the root folder of this project: `e:/Uday_Document/projet/firebase-credentials.json`.
   - Update `.env`:
     ```env
     DATABASE_BACKEND="firestore"
     FIREBASE_CREDENTIALS_PATH="firebase-credentials.json"
     ```
5. **Restart Server**:
   - The app will automatically connect to your live Google Cloud Firestore!
   - *(Note: If `firebase-credentials.json` is not provided, the application runs in local Mock Firestore mode so you are never blocked).*

---

## 🚀 Quickstart Guide (Local Development)

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Git

### 2. Setup Virtual Environment
```powershell
# Clone or enter repository
cd e:/Uday_Document/projet

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(By default, `.env` uses SQLite `sqlite:///./price_tracker.db` so you can run immediately without setting up a database server).*

### 4. Run the Server
```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Web Dashboard**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Docs (Swagger UI)**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🐳 Docker Deployment (PostgreSQL + FastAPI)

To run the complete stack with a dedicated PostgreSQL database container:

```bash
docker compose up --build -d
```

This starts:
- **Database**: PostgreSQL 16 on port `5432` with persistent volume `postgres_data`.
- **Backend & Frontend**: FastAPI application on port `8000`.

To stop the containers:
```bash
docker compose down
```

---

## 🧪 Testing Price Drops with the Built-in Mock Store

Testing third-party sites can lead to IP throttling. This application includes a built-in mock store with dynamic price control:

1. Log in on the dashboard (`http://127.0.0.1:8000`).
2. Click **Track New Product** and use the quick demo button:
   - **Product**: `Laptop Pro`
   - **URL**: `http://127.0.0.1:8000/mock-store/product/laptop-pro`
   - **Target Price**: `$1750.00`
   - (Current store price is `$1899.00`, so status shows `Tracking (above target)`).
3. Scroll down to the **Price Drop Simulator**:
   - Select `UltraBook Pro 16-inch`.
   - Set Simulated New Price to `$1699.00`.
   - Click **Drop / Update Price**.
4. The simulator updates the mock store price and triggers an immediate check:
   - Notice the card badge immediately turns green: **`🎉 Target Met!`**
   - Click **📈 Trends** to view the Chart.js line graph showing the drop below your dashed green target line!

---

## 📖 API Reference

### Authentication
- `POST /auth/register` — Create user account (`email`, `password`).
- `POST /auth/login` — Login with JSON (`email`, `password`) -> returns JWT `access_token`.
- `POST /auth/token` — OAuth2 compatible login for Swagger UI `/docs`.
- `GET /auth/me` — Return profile of currently authenticated user.

### Products
- `POST /products` — Add a product to track (`url`, `target_price`, optional `title`).
- `GET /products` — List tracked products for the current user.
- `GET /products/{id}` — Get single product details.
- `PUT /products/{id}` — Update target price or title.
- `DELETE /products/{id}` — Stop tracking and delete product.
- `GET /products/{id}/history` — Return chronological price history list for charts.
- `GET /products/{id}/summary` — Return statistical summary (min, max, avg, savings).
- `POST /products/{id}/check` — Trigger immediate on-demand scrape and check.

### Mock Store
- `GET /mock-store/product/{sku}` — Render mock e-commerce HTML product page.
- `GET /mock-store/list` — List available mock products.
- `POST /mock-store/product/{sku}/set-price` — Change mock price for simulations.

---

## 🧪 Running Automated Tests

Run the full pytest suite:

```powershell
.venv\Scripts\python -m pytest backend/tests/ -v
```

All 12 tests cover:
- Authentication & JWT token security
- Duplicate account handling
- Product tracking CRUD
- Price drop detection & savings math
- Scraper parsing & CSS fallback logic
- Mock store endpoints
