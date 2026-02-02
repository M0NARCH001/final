# 🥗 NutriMate v2

A **personalized nutrition tracking and intelligence system** that not only tracks calories but proactively suggests foods to close nutritional gaps using a hybrid ML recommendation engine.

## 🚀 Features

### Core Features
- **Micronutrient Tracking**: Track Fiber, Sodium, Sugar, Iron, Calcium, Vitamin C, and Folate
- **Support for Health Conditions**: Personalized targets and warnings for **Diabetes, Hypertension, PCOS, Muscle Gain, and Heart Health**
- **Hybrid ML Recommendations**: A smart engine that blends hand-written nutritional rules with a **RandomForest ML model** that learns from your preferences
- **Smart Warnings**: Instant alerts if your sugar/sodium is too high or if you're missing critical minerals
- **BMR/TDEE Calculation**: Automatic calorie target calculation based on biometrics and activity level

### New in v2.1
- **Username-Based Authentication**: Login with username across devices (no password required)
- **Barcode Scanner**: Scan product barcodes to lookup nutritional info from OpenFoodFacts
- **Auto-Add to Database**: Scanned products not in the database can be automatically added and logged
- **Combined Endpoints**: Food creation and logging in single transactions for reliability
- **Smart Recommendation Filters**: Excludes condiments (masala, pickle, chutney, etc.) from recommendations

---

## 🧠 Hybrid ML Recommendation Engine

The system uses a **Phased Rollout** strategy for intelligence:

| Phase | Condition | Behavior |
|-------|-----------|----------|
| **Phase 0 (Day 1)** | < 80 impressions | 100% rule-based scoring. Collects "silent" data on which foods you log. |
| **Phase 1** | ≥ 80 impressions + ≥ 15 accepts | Automatically trains RandomForest model in the background |
| **Phase 2 (Ongoing)** | Model trained | **70% nutritional rules + 30% ML** hybrid scoring for personalized suggestions |

### Training Parameters
- **MIN_IMPRESSIONS**: 80 (minimum data points before training)
- **MIN_ACCEPTS**: 15 (minimum accepted recommendations)
- **MIN_HOURS_BETWEEN**: 6 (cooldown between retraining cycles)

### Check ML Status
```bash
curl https://your-backend.railway.app/ml/status
```

---

## 🏗 Architecture

NutriMate v2 uses a robust client-server architecture designed for serverless or persistent environments.

### Frontend (Expo / React Native)
- **Dashboard**: Circular calorie progress, macro/micro progress bars, health warnings
- **Setup**: Smart onboarding with username registration, biometric input, and health condition selection
- **Scanner**: Barcode scanner with OpenFoodFacts integration and auto-database-add feature
- **Food Log**: Search and log foods from IFCT (Indian) and USDA (Global) databases
- **Recommendations**: Intelligent food suggestions with portion sizes and reasoning badges

### Backend (FastAPI + ML Layer)
- **API Core**: FastAPI handling nutrition logic, user management, and food logging
- **User Management**: Username-based registration and lookup
- **Food Management**: Search, create, and combined create-and-log endpoints
- **ML Layer**: 
  - `predictor.py`: Hybrid scoring (70% rules / 30% ML probability)
  - `trainer.py`: Automated background training using RandomForest
  - `config.py`: Centralized ML constants, paths, and logging
- **Impressions System**: Tracks user interactions with recommendations for ML training
- **DB (SQLite)**: Persistent storage for food logs, user profiles, and ML training data

---

## 📱 Mobile App Flow

### 1. Onboarding
- Enter a unique username (used for cross-device access)
- Input biometrics: age, height, weight, gender
- Select activity level (sedentary to very active)
- Select health conditions (Diabetes, Hypertension, PCOS, etc.)
- **Auto-calculated nutritional targets** based on BMR/TDEE formulas

### 2. Dashboard
- **Circular calorie progress** with color-coded status
- **Macro bars**: Protein, Carbs, Fats with % completion
- **Micro bars**: Fiber, Iron, Calcium, Vitamin C, Folate, Sodium, Sugar
- **Smart warnings**: Yellow (high sugar/sodium), Blue (mineral deficits)
- **Today's food log** with delete capability

### 3. Food Logging
- Search 1000+ foods from IFCT + USDA databases
- Instant results with nutritional preview
- Log with quantity adjustment
- Scan barcodes for quick product lookup

### 4. Barcode Scanning
- Scan any product barcode
- Lookup on OpenFoodFacts API (global product database)
- Match with NutriMate database OR
- **Add new product to database** with one tap
- Extracts: Calories, Protein, Carbs, Fats, Sugar, Fiber, Sodium, Calcium, Iron, Vitamin C, Folate

### 5. Smart Recommendations
- Backend calculates current deficits vs targets
- Scores foods based on nutritional gaps + ML preferences
- Excludes junk food and condiments automatically
- Shows reasoning badges (e.g., "High Protein", "Low Sodium")
- Records impressions for future ML training

---

## 🔌 API Endpoints

### User Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/check-username` | POST | Check if username exists, returns user_id if found |
| `/users/register` | POST | Register new user with username and profile |
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
| `/food-logs/today` | GET | Get today's food logs with nutritional data |
| `/food-logs/{log_id}` | DELETE | Delete a food log |

### Intelligence
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/daily-summary` | POST | Get nutritional summary for a day |
| `/recommendations/generate` | POST | Get personalized food recommendations |
| `/compute` | POST | Calculate nutritional targets based on biometrics |

### ML & Training
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ml/status` | GET | Get ML model status and training statistics |
| `/impressions/batch` | POST | Log recommendation impressions for ML training |
| `/impressions/{id}/mark-added` | PUT | Mark impression as accepted (user logged food) |

### Utilities
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/migrate-db` | GET | Run database migrations |

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Mobile** | Expo (React Native), Expo Router, Expo Camera, AsyncStorage |
| **API** | FastAPI, Uvicorn, Pydantic |
| **ML** | Scikit-Learn (RandomForest), Joblib, NumPy, StandardScaler |
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
- ML artifacts persist in `/data/ml_artifacts/`

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
│   │   └── models.py            # SQLAlchemy models
│   ├── ml/
│   │   ├── config.py            # ML constants & logging
│   │   ├── predictor.py         # Hybrid ML scoring
│   │   └── trainer.py           # Auto-retraining logic
│   └── requirements.txt
├── mobile/
│   ├── app/
│   │   ├── (tabs)/
│   │   │   ├── index.js         # Dashboard
│   │   │   ├── FoodLogScreen.js # Food logging
│   │   │   ├── ScannerScreen.js # Barcode scanner
│   │   │   └── RecommendScreen.js
│   │   └── setup.js             # User onboarding
│   ├── components/
│   │   ├── CalorieProgressCircle.js
│   │   └── ...
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
- ✅ Hybrid ML recommendations with phased rollout
- ✅ Automatic background model retraining
- ✅ Health condition support (Diabetes, PCOS, Hypertension, etc.)
- ✅ Micronutrient tracking (11 nutrients)
- ✅ BMR/TDEE-based calorie targets
- ✅ Smart warnings system
- ✅ Condiment filtering in recommendations

The architecture supports 10,000+ food items with sub-second recommendation latency.

---

## 📐 How It Works: Formulas & Algorithms

### 1. BMR Calculation (Mifflin-St Jeor Equation)

The **Basal Metabolic Rate** is calculated based on gender:

```
Male:   BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
Female: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
```

### 2. TDEE Calculation (Total Daily Energy Expenditure)

```
TDEE = BMR × Activity Multiplier
```

| Activity Level | Multiplier |
|----------------|------------|
| Low (Sedentary) | 1.2 |
| Moderate | 1.55 |
| High (Very Active) | 1.75 |

### 3. Goal-Based Calorie Adjustment

**Weight Loss:**
```
Total Deficit = (Current Weight - Target Weight) × 7700 kcal/kg
Daily Calories = TDEE - (Total Deficit / Days)
```

**Weight Gain:**
```
Total Surplus = (Target Weight - Current Weight) × 7700 kcal/kg
Daily Calories = TDEE + (Total Surplus / Days)
```

*Minimum daily calories clamped at 1200 kcal for safety.*

### 4. Macronutrient Distribution

**Protein:**
```
Base:        Protein = Weight × 1.6 g/kg
Weight Gain: Protein = Weight × 2.0 g/kg
Muscle Focus: Protein = Weight × 2.2 g/kg
```

**Carbohydrates:**
```
Default:        50% of calories
Diabetes/PCOS:  40% of calories (lower for blood sugar control)
```

**Fats:**
```
Default:       25% of calories
Heart Health:  30% of calories (emphasis on healthy fats)

Fat (g) = (Daily Calories × Fat %) / 9
Carbs (g) = (Remaining Calories) / 4  [min 50g]
```

### 5. Micronutrient Targets (RDA-Based)

| Nutrient | Male | Female | Condition Adjustment |
|----------|------|--------|---------------------|
| **Fiber** | 30g | 25g | - |
| **Sugar** | 10% of calories | 10% of calories | Diabetes/PCOS: max 25g |
| **Sodium** | 2300mg | 2300mg | Hypertension: 2000mg |
| **Iron** | 8mg | 18mg | - |
| **Calcium** | 1000mg | 1000mg | - |
| **Vitamin C** | 90mg | 75mg | - |
| **Folate** | 400μg | 400μg | - |

### 6. Food Recommendation Scoring Algorithm

Each food gets a **rule-based score** calculated as:

```python
score = 0

# Macronutrient scoring (based on current deficits)
score += min(food.calories, deficit.calories) × 0.2
score += min(food.protein, deficit.protein) × 4.0   # Protein is king
score += min(food.carbs, deficit.carbs) × 1.0
score += min(food.fat, deficit.fat) × 0.5

# Micronutrient bonuses
if food.fiber >= 3g:  score += 10
if food.sugar < 5g:   score += 8
if food.sodium < 200mg: score += 5

# Iron/Calcium/VitC deficit matching
score += iron_contribution × 2
score += calcium_contribution × 3
score += vitC_contribution × 0.5

# Penalties
if food.fat > 20g:    score -= fat × 2
if junk_food_name:    score -= 80

# Condition-based penalties
if (diabetes OR pcos) AND carbs > 30g:   score -= 30
if (diabetes OR pcos) AND sugar > 10g:   score -= 25
if (hypertension) AND sodium > 400mg:    score -= 25

# Preferred foods bonus
if name contains ["paneer","egg","dal","chicken","curd","fish"]: score += 20
```

### 7. Hybrid ML Scoring (After Training)

Once the ML model is trained (≥80 impressions):

```python
# ML model predicts probability of user accepting food
ml_probability = model.predict_proba(features)[1]

# Hybrid score: 70% rules + 30% ML
final_score = (0.70 × rule_score) + (0.30 × ml_probability × 100)
```

**ML Features (10 dimensions):**
```python
features = [
    deficit.calories / 500,
    deficit.protein / 100,
    deficit.fat / 80,
    deficit.carbs / 200,
    food.calories / 500,
    food.protein / 30,
    food.fat / 20,
    food.carbs / 60,
    display_rank / 10,
    rule_score / 100
]
```

### 8. Food Filtering (Exclusions)

Foods automatically excluded from recommendations:
- **Ultra-low calorie**: < 40 kcal
- **Sugar bombs**: Carbs > 40g AND Protein < 5g AND Sugar > 15g
- **Pure fat**: Fat > 20g AND Protein < 5g
- **Condiments**: Contains "masala", "premix", "chutney", "pickle", "achar", "papad", "sauce"
- **Junk foods**: Contains "burfi", "laddu", "halwa", "cake", "sweet", "pudding", "pastry", "cookie"
- **Diabetes restriction**: Carbs > 50g (when has_diabetes or has_pcos)

---

## 📄 License

MIT License - Feel free to use and modify for your own projects.

