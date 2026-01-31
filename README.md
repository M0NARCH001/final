# 🥗 NutriMate v2

A **personalized nutrition tracking and intelligence system** that not only tracks calories but proactively suggests foods to close nutritional gaps using a hybrid ML recommendation engine.

## 🚀 New in v2
- **Micronutrient Tracking**: Track Fiber, Sodium, Sugar, Iron, Calcium, Vitamin C, and Folate.
- **Support for Health Conditions**: Personalized targets and warnings for **Diabetes, Hypertension, PCOS, Muscle Gain, and Heart Health**.
- **Hybrid ML Recommendations**: A smart engine that blends hand-written nutritional rules with a **RandomForest ML model** that learns from your preferences.
- **Smart Warnings**: Instant alerts if your sugar/sodium is too high or if you're missing critical minerals.

---

## 🏗 Architecture

NutriMate v2 uses a robust client-server architecture designed for serverless or persistent environments.

### Frontend (Expo / React Native)
- **Dashboard**: High-level macro & micro progress bars with health warnings.
- **Setup**: Smart onboarding that calculates BMR/TDEE and adjusts targets based on medical conditions.
- **Recommendations**: Intelligent food suggestions with portion sizes and "reasoning" badges (e.g., "High Protein", "Low Sodium").
- **API**: Centralized `api.js` with dynamic environment detection.

### Backend (FastAPI + ML Layer)
- **API Core**: FastAPI handling nutrition logic and food logging.
- **ML Layer (`/ml`)**: 
  - `predictor.py`: Hybrid scoring (70% rules / 30% ML).
  - `trainer.py`: Automated background training using RandomForest.
  - `config.py`: Centralized ML constants and logging.
- **DB (SQLite)**: Persistent storage for food logs, user profiles, and ML training data (impressions).

---

## 📱 Mobile Features & Flow

1. **Onboarding**: Users enter biometrics + select health conditions (e.g., Diabetes). Targets are automatically narrowed (e.g., <40% carbs for Diabetes).
2. **Daily Tracking**: Log Indian (IFCT) and Global (USDA) foods. Dashboard shows "Live" progress.
3. **Nutritional Intelligence**: 
   - **Yellow Warnings**: High Sodium (>2300mg) or High Sugar.
   - **Blue Warnings**: Deficits in Iron, Calcium, or Fiber.
4. **Interactive Recommendations**: Backend calculates current deficits and scores 1000+ foods. ML boosts foods you frequently accept.

---

## 🧠 Hybrid Recommendation Engine

The system uses a **Phased Rollout** strategy for intelligence:
- **Phase 0 (Day 1)**: 100% rule-based scoring. Collects "silent" data on which foods you choose.
- **Phase 1 (80+ Impressions)**: Automatically trains a RandomForest model in the background.
- **Phase 2 (Ongoing)**: Blends ML probability with nutritional rules (70/30) to provide suggestions that are both healthy and personalized.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Mobile** | Expo (React Native), Expo Router, AsyncStorage |
| **API** | FastAPI, Uvicorn, Pydantic |
| **ML** | Scikit-Learn (RandomForest), Joblib, NumPy |
| **Database** | SQLite + SQLAlchemy ORM |
| **Deployment** | Railway (Backend), Expo EAS (Mobile) |

---

## 🏁 Getting Started

### Backend (Local)
1. `cd backend`
2. `python -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app.api.main:app --reload`

### Mobile (Local)
1. `cd mobile`
2. `npm install`
3. `npx expo start`

---

## 🚢 Deployment

### Railway (Backend)
- Uses `railway.json` and a `/data` volume for persistent SQLite storage.
- Variables needed: `RAILWAY_VOLUME_MOUNT_PATH=/data`.

### Expo EAS (Mobile)
- Build Android APK: `eas build --platform android --profile preview`
- Set `EXPO_PUBLIC_API_URL` in `app.json` or as an EAS Secret.

---

## ✅ Status: Production Ready
All core v2 features are implemented. The architecture supports 10,000+ food items with sub-second recommendation latency.

