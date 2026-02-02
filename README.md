# 🥗 NutriMate v2

A **personalized nutrition tracking and intelligence system** that not only tracks calories but proactively suggests foods to close nutritional gaps using a hybrid ML recommendation engine.

## 🚀 Features

### Core Features
- **Micronutrient Tracking**: Track Fiber, Sodium, Sugar, Iron, Calcium, Vitamin C, and Folate
- **Support for Health Conditions**: Personalized targets and warnings for **Diabetes, Hypertension, PCOS, Muscle Gain, and Heart Health**
- **Hybrid ML Recommendations**: A smart engine that blends hand-written nutritional rules with a **RandomForest ML model** that learns from your preferences
- **Smart Warnings**: Instant alerts if your sugar/sodium is too high or if you're missing critical minerals

### New in v2.1
- **Username-Based Authentication**: Login with username across devices (no password required)
- **Barcode Scanner**: Scan product barcodes to lookup nutritional info from OpenFoodFacts
- **Auto-Add to Database**: Scanned products not in the database can be automatically added and logged
- **Combined Endpoints**: Food creation and logging in single transactions for reliability
- **Smart Recommendation Filters**: Excludes condiments (masala, pickle, chutney, etc.) from recommendations

---

## 🏗 Architecture

NutriMate v2 uses a robust client-server architecture designed for serverless or persistent environments.

### Frontend (Expo / React Native)
- **Dashboard**: High-level macro & micro progress bars with health warnings
- **Setup**: Smart onboarding with username registration, biometric input, and health condition selection
- **Scanner**: Barcode scanner with OpenFoodFacts integration and auto-database-add feature
- **Food Log**: Search and log foods from IFCT (Indian) and USDA (Global) databases
- **Recommendations**: Intelligent food suggestions with portion sizes and reasoning badges

### Backend (FastAPI + ML Layer)
- **API Core**: FastAPI handling nutrition logic, user management, and food logging
- **User Management**: Username-based registration and lookup (`/users/check-username`, `/users/register`)
- **Food Management**: Search, create, and combined create-and-log endpoints (`/foods/create-and-log`)
- **ML Layer (`/ml`)**: 
  - `predictor.py`: Hybrid scoring (70% rules / 30% ML)
  - `trainer.py`: Automated background training using RandomForest
  - `config.py`: Centralized ML constants and logging
- **DB (SQLite)**: Persistent storage for food logs, user profiles, and ML training data

---

## 📱 Mobile App Flow

1. **Onboarding**: 
   - Enter a unique username (used for cross-device access)
   - Input biometrics (age, height, weight, activity level)
   - Select health conditions (Diabetes, Hypertension, PCOS, etc.)
   - Auto-calculated nutritional targets based on BMR/TDEE

2. **Daily Tracking**: 
   - Search and log foods from 1000+ items (IFCT + USDA)
   - Scan barcodes to find products instantly
   - Dashboard shows live progress with color-coded bars

3. **Barcode Scanning**:
   - Scan any product barcode
   - Lookup on OpenFoodFacts API
   - Find matching food in NutriMate database OR
   - **Add new product to database** with one tap

4. **Smart Recommendations**: 
   - Backend calculates current deficits
   - Scores foods based on nutritional gaps + ML preferences
   - Excludes junk food and condiments automatically

---

## 🔌 API Endpoints

### User Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/check-username` | POST | Check if username exists, returns user_id if found |
| `/users/register` | POST | Register new user with username |
| `/users/by-username/{username}` | GET | Get user by username |
| `/users/{user_id}` | GET/PUT | Get or update user profile |

### Food Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/foods` | GET | Search foods by query |
| `/foods` | POST | Create new food item |
| `/foods/create-and-log` | POST | Create food AND log it in one transaction |

### Food Logging
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/food-logs` | POST | Log a food item |
| `/food-logs/today` | GET | Get today's food logs |
| `/food-logs/{log_id}` | DELETE | Delete a food log |

### Intelligence
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/daily-summary` | POST | Get nutritional summary for a day |
| `/recommendations/generate` | POST | Get personalized food recommendations |
| `/compute` | POST | Calculate nutritional targets |

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Mobile** | Expo (React Native), Expo Router, Expo Camera, AsyncStorage |
| **API** | FastAPI, Uvicorn, Pydantic |
| **ML** | Scikit-Learn (RandomForest), Joblib, NumPy |
| **Database** | SQLite + SQLAlchemy ORM |
| **External APIs** | OpenFoodFacts (barcode lookup) |
| **Deployment** | Railway (Backend), Expo EAS (Mobile) |

---

## 🏁 Getting Started

### Backend (Local)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

### Mobile (Local)
```bash
cd mobile
npm install
npx expo start
```

### Environment Configuration
- Update `EXPO_PUBLIC_API_URL` in `mobile/app.json` for production
- Update `API_BASE` in `mobile/src/api.js` for local development IP

---

## 🚢 Deployment

### Railway (Backend)
- Uses `railway.json` and a `/data` volume for persistent SQLite storage
- Variables needed: `RAILWAY_VOLUME_MOUNT_PATH=/data`
- Database migrations: Visit `/migrate-db` endpoint after deploying new schema changes

### Expo EAS (Mobile)
```bash
# Build Android APK
eas build --platform android --profile preview

# Build iOS
eas build --platform ios --profile preview
```

---

## 📁 Project Structure

```
Nutrimate-v2/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── main.py          # Core API endpoints
│   │   │   ├── users.py         # User management
│   │   │   ├── foods.py         # Food CRUD + create-and-log
│   │   │   └── food_logs.py     # Food logging
│   │   ├── db/
│   │   │   └── database.py      # SQLAlchemy setup
│   │   ├── ml/
│   │   │   ├── predictor.py     # Hybrid ML scoring
│   │   │   └── trainer.py       # Model training
│   │   └── models.py            # SQLAlchemy models
│   └── requirements.txt
├── mobile/
│   ├── app/
│   │   ├── (tabs)/
│   │   │   ├── index.js         # Dashboard
│   │   │   ├── FoodLogScreen.js # Food logging
│   │   │   ├── ScannerScreen.js # Barcode scanner
│   │   │   └── ...
│   │   └── setup.js             # User onboarding
│   ├── src/
│   │   ├── api.js               # API client
│   │   └── openfood.js          # OpenFoodFacts client
│   └── app.json                 # Expo config
└── README.md
```

---

## ✅ Status: Production Ready

All core v2 features are implemented:
- ✅ Username-based authentication
- ✅ Barcode scanning with OpenFoodFacts
- ✅ Auto-add scanned products to database
- ✅ Hybrid ML recommendations
- ✅ Health condition support
- ✅ Micronutrient tracking

The architecture supports 10,000+ food items with sub-second recommendation latency.

---

## 📄 License

MIT License - Feel free to use and modify for your own projects.
