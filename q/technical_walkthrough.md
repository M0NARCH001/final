# NutriMate v2: Complete Technical Walkthrough

## Table of Contents
1. [Project Structure & File Overview](#1-project-structure--file-overview)
2. [Database Design (Tables, PK, FK)](#2-database-design-tables-pk-fk)
3. [Barcode Scanning Flow](#3-barcode-scanning-flow)
4. [Food Logging System](#4-food-logging-system)
5. [Recommendation Engine (Automatic System)](#5-recommendation-engine-automatic-system)
6. [Machine Learning Training Pipeline](#6-machine-learning-training-pipeline)
7. [Complete Data Flow Diagram](#7-complete-data-flow-diagram)

---

## 1. Project Structure & File Overview

### Backend Files (`/backend`)

#### `app/models.py` - Database Schema Definition
**Purpose**: Defines all database tables using SQLAlchemy ORM

**Key Tables**:
```python
class User(Base):
    user_id = Column(Integer, primary_key=True)  # ← PK
    username = Column(String, unique=True)
    age, gender, height_cm, weight_kg  # Biometrics
    has_diabetes, has_pcos, has_hypertension  # Health conditions

class FoodItem(Base):
    food_id = Column(Integer, primary_key=True)  # ← PK
    food_name = Column(String)
    Calories_kcal, Protein_g, Carbohydrates_g, Fats_g  # Macros
    Fibre_g, Sodium_mg, Iron_mg, Calcium_mg, VitaminC_mg  # Micros

class FoodLog(Base):
    log_id = Column(Integer, primary_key=True)  # ← PK
    user_id = Column(Integer)  # ← FK to User
    food_id = Column(Integer, ForeignKey("food_items.food_id"))  # ← FK
    quantity = Column(Float)
    logged_at = Column(DateTime)

class RecommendationImpression(Base):
    id = Column(Integer, primary_key=True)  # ← PK
    user_id = Column(Integer, ForeignKey("user.user_id"))  # ← FK
    food_id = Column(Integer, ForeignKey("food_items.food_id"))  # ← FK
    deficits = Column(Text)  # JSON: {"Protein_g": 45, ...}
    rank = Column(Integer)  # Position in recommendation list
    rule_score = Column(Float)
    added = Column(Boolean)  # Did user accept? (ML label)
```

#### `app/api/main.py` - Core API Logic (1178 lines)
**Purpose**: Main FastAPI application with all major endpoints

**Key Functions**:
1. **Startup**: `lifespan()` loads ML model on app start
2. **CORS**: Configures cross-origin requests for mobile
3. **Recommendation Scoring**: `score_food()` - rule-based algorithm
4. **Warning Generation**: `generate_warnings()` - nutrition alerts

**Critical Endpoint** (Line 800+):
```python
@app.post("/recommendations/generate")
async def generate_recommendations(req: RecommendationRequest, db: Session):
    # STEP 1: Calculate deficits
    deficits = {
        "Calories_kcal": req.daily_calories - current_totals["Calories_kcal"],
        "Protein_g": req.protein_g - current_totals["Protein_g"],
        # ... other nutrients
    }
    
    # STEP 2: Score ALL foods in database
    foods = db.query(FoodItem).all()
    scored_foods = []
    for food in foods:
        rule_score = score_food(food, deficits, conditions)
        
        # STEP 3: Apply ML hybrid scoring if model exists
        if ML_AVAILABLE and MODEL is not None:
            hybrid_score = get_hybrid_score(food, deficits, rule_score, rank)
            final_score = hybrid_score if hybrid_score else rule_score
        else:
            final_score = rule_score
        
        scored_foods.append((food, final_score))
    
    # STEP 4: Sort and return top 10
    scored_foods.sort(key=lambda x: x[1], reverse=True)
    return scored_foods[:10]
```

#### `app/api/foods.py` - Food CRUD Operations
**Key Endpoint**: `/foods/create-and-log` (Lines 82-133)
```python
@router.post("/create-and-log")
def create_food_and_log(payload: FoodCreateAndLog, db: Session):
    # ATOMIC TRANSACTION - both operations succeed or fail together
    
    # Step 1: Create food
    f = FoodItem(food_name=payload.food_name, ...)
    db.add(f)
    db.flush()  # ← Gets food_id WITHOUT committing
    
    # Step 2: Create log using the new food_id
    log_entry = FoodLog(
        user_id=payload.user_id,
        food_id=f.food_id,  # ← Uses food_id from step 1
        quantity=payload.quantity
    )
    db.add(log_entry)
    db.flush()
    
    # Step 3: Commit BOTH together (atomic)
    db.commit()
    return {"food_id": f.food_id, "log_id": log_entry.log_id}
```

#### `ml/predictor.py` - ML Inference Engine
**Key Variables** (Global):
```python
MODEL = None   # RandomForest model (loaded on startup)
SCALER = None  # StandardScaler (for feature normalization)
```

**Feature Extraction** (Lines 13-31):
```python
def extract_features(impression, food):
    """Converts impression + food into 10-dimensional feature vector"""
    d = impression.deficits  # JSON: {"Calories_kcal": 320, ...}
    
    return np.array([
        d.get('Calories_kcal', 0) / 500.0,      # Feature 1: Normalized deficit
        d.get('Protein_g', 0) / 100.0,          # Feature 2
        d.get('Fats_g', 0) / 80.0,              # Feature 3
        d.get('Carbohydrates_g', 0) / 200.0,    # Feature 4
        food.Calories_kcal / 500.0,             # Feature 5: Food's nutrients
        food.Protein_g / 30.0,                  # Feature 6
        food.Fats_g / 20.0,                     # Feature 7
        food.Carbohydrates_g / 60.0,            # Feature 8
        impression.rank / 10.0,                 # Feature 9: Display position
        impression.rule_score / 100.0,          # Feature 10: Rule score
    ])
```

**Hybrid Scoring** (Lines 53-77):
```python
def get_hybrid_score(food, deficits, rule_score, rank):
    if MODEL is None or SCALER is None:
        return None  # ← Fallback to 100% rules
    
    # Create features
    features = extract_features(dummy_impression, food)
    
    # Scale and predict
    features_scaled = SCALER.transform(features.reshape(1, -1))
    ml_probability = MODEL.predict_proba(features_scaled)[0, 1]
    
    # Hybrid blend: 70% rules + 30% ML
    hybrid = 0.70 * rule_score + 0.30 * (ml_probability * 100)
    return hybrid
```

#### `ml/trainer.py` - Automatic ML Training
**Training Trigger** (Lines 135-150):
```python
def should_retrain(db: Session) -> bool:
    # Check 1: Enough data?
    if impression_count < MIN_IMPRESSIONS:  # MIN_IMPRESSIONS = 80
        return False
    
    # Check 2: Enough time passed?
    if not os.path.exists(LAST_TRAIN_PATH):
        return True  # Never trained before
    
    last_train_time = read_timestamp_from_file()
    hours_elapsed = (now - last_train_time).total_seconds() / 3600
    
    return hours_elapsed > MIN_HOURS_BETWEEN  # 6 hours
```

**Training Process** (Lines 41-128):
```python
def train_model(db: Session):
    # STEP 1: Fetch all impressions
    impressions = db.query(RecommendationImpression).all()
    
    # STEP 2: Check thresholds
    if len(impressions) < 80 or accepts < 15:
        return False, "not_enough_data"
    
    # STEP 3: Build feature matrix
    X, y = [], []
    for imp in impressions:
        food = db.query(FoodItem).filter_by(food_id=imp.food_id).first()
        features = extract_features(imp, food)
        X.append(features)
        y.append(1 if imp.added else 0)  # Label: accepted=1, rejected=0
    
    # STEP 4: Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # STEP 5: Train RandomForest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)
    
    # STEP 6: Evaluate
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    
    # STEP 7: Save model
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    # STEP 8: Reload in memory
    load_model_and_scaler()
```

### Mobile Files (`/mobile`)

#### `src/api.js` - Backend Communication
**Environment Detection** (Lines 14-27):
```javascript
const API_BASE = (() => {
  // Production: Use Expo config
  const prodUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_API_URL;
  if (prodUrl) return prodUrl;
  
  // Development: Use local IP
  if (Platform.OS === "android") {
    return `http://10.0.2.2:8000`;  // Android emulator
  }
  return `http://172.20.10.2:8000`;  // iOS simulator/real device
})();
```

#### `src/openfood.js` - OpenFoodFacts Integration
**Barcode Lookup** (Lines 36-68):
```javascript
export async function getProductFromOpenFoodFacts(barcode) {
  const url = `https://world.openfoodfacts.org/api/v0/product/${barcode}.json`;
  const response = await fetch(url);
  const json = await response.json();
  
  if (json.status !== 1) return null;  // Product not found
  
  const product = json.product;
  const nutriments = product.nutriments;
  
  // Extract and normalize nutrients
  return {
    barcode,
    product_name: product.product_name,
    nutrients_per_100g: {
      Calories_kcal: nutriments["energy-kcal_100g"],
      Protein_g: nutriments["proteins_100g"],
      Sodium_mg: nutriments["sodium_100g"] * 1000,  // g → mg conversion
      // ... other nutrients
    }
  };
}
```

#### `app/(tabs)/ScannerScreen.js` - Barcode Capture
**Scanning Flow** (Lines 50-120):
```javascript
async function handleBarcodeScan({ data: barcode }) {
  setScanned(true);  // Prevent multiple scans
  
  try {
    // STEP 1: Fetch from OpenFoodFacts
    const product = await getProductFromOpenFoodFacts(barcode);
    
    if (!product) {
      alert("Product not found in database");
      return;
    }
    
    // STEP 2: Check if already in local DB
    const localResults = await API.searchFoods(product.product_name, 5);
    
    if (localResults.length > 0) {
      // Found → Navigate to food log screen with search
      router.push(`/FoodLogScreen?searchQuery=${product.product_name}`);
    } else {
      // Not found → Add to DB and log
      const uid = await AsyncStorage.getItem("user_id");
      
      await API.createFoodAndLog({
        user_id: parseInt(uid),
        food_name: product.product_name,
        Calories_kcal: product.nutrients_per_100g.Calories_kcal,
        Protein_g: product.nutrients_per_100g.Protein_g,
        // ... other nutrients
        quantity: 1.0
      });
      
      alert(`Added and logged: ${product.product_name}`);
      router.push("/(tabs)");  // Back to dashboard
    }
  } catch (error) {
    alert(`Scan error: ${error.message}`);
  }
}
```

---

## 2. Database Design (Tables, PK, FK)

### Schema Diagram
```
┌─────────────────┐
│      User       │
│─────────────────│
│ user_id (PK)    │◄──────┐
│ username        │       │
│ age, gender     │       │
│ height, weight  │       │
│ has_diabetes    │       │
└─────────────────┘       │
                          │ FK: user_id
┌─────────────────┐       │
│   FoodItem      │       │
│─────────────────│       │
│ food_id (PK)    │◄──┐   │
│ food_name       │   │   │
│ Calories_kcal   │   │   │
│ Protein_g       │   │   │
│ (11 nutrients)  │   │   │
└─────────────────┘   │   │
                      │   │
                      │   │ FK: food_id
                      │   │
┌─────────────────────┴───┴────────┐
│         FoodLog                  │
│──────────────────────────────────│
│ log_id (PK)                      │
│ user_id (FK → User)              │
│ food_id (FK → FoodItem)          │
│ quantity                         │
│ logged_at (timestamp)            │
└──────────────────────────────────┘
                      │
                      │
                      │ FK: user_id, food_id
┌─────────────────────▼────────────┐
│  RecommendationImpression        │
│──────────────────────────────────│
│ id (PK)                          │
│ user_id (FK → User)              │
│ food_id (FK → FoodItem)          │
│ deficits (JSON text)             │
│ rank (integer 1-10)              │
│ rule_score (float)               │
│ added (boolean - ML label)       │
│ shown_at (timestamp)             │
└──────────────────────────────────┘
```

### Relationship Types
- **User ↔ FoodLog**: One-to-Many (1 user has N logs)
- **FoodItem ↔ FoodLog**: One-to-Many (1 food can be logged N times)
- **User ↔ RecommendationImpression**: One-to-Many
- **FoodItem ↔ RecommendationImpression**: One-to-Many

### Storage Location
- **Development**: `backend/nutri_indian.db` (SQLite file)
- **Production (Railway)**: `/data/nutri_indian.db` (persistent volume)

---

## 3. Barcode Scanning Flow

### Complete Data Flow
```
┌──────────────┐
│ Mobile App   │
│ ScannerScreen│
└──────┬───────┘
       │ 1. User points camera at barcode
       ▼
┌──────────────┐
│ expo-camera  │ Captures barcode number (e.g., "8901030543210")
└──────┬───────┘
       │ 2. Barcode detected
       ▼
┌────────────────────────────────┐
│ OpenFoodFacts API              │
│ world.openfoodfacts.org        │
└──────┬─────────────────────────┘
       │ 3. Returns product JSON
       │ {
       │   "product": {
       │     "product_name": "Maggi Noodles",
       │     "nutriments": {
       │       "energy-kcal_100g": 350,
       │       "proteins_100g": 8.5,
       │       ...
       │     }
       │   }
       │ }
       ▼
┌──────────────┐
│ openfood.js  │ Normalizes data (e.g., sodium g → mg)
└──────┬───────┘
       │ 4. Normalized nutrition object
       ▼
┌──────────────┐
│ API.searchFoods() │ Check if product exists in local DB
│                   │
└──────┬───────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
Found   Not Found
   │       │
   │       └──► 5. API.createFoodAndLog()
   │                    │
   │                    ▼
   │            ┌──────────────────┐
   │            │ Backend:         │
   │            │ POST /foods/     │
   │            │ create-and-log   │
   │            └────────┬─────────┘
   │                     │
   │                     ▼
   │            ┌─────────────────────┐
   │            │ Database Transaction│
   │            │ 1. INSERT FoodItem  │
   │            │ 2. INSERT FoodLog   │
   │            │ 3. COMMIT both      │
   │            └─────────────────────┘
   │
   └──► Navigate to FoodLogScreen with search query
```

### Key Code: Atomic Transaction
**Why it matters**: If we create food but fail to log it, we get orphan foods. If we log before creating, we get FK constraint errors.

**Solution** (`foods.py`):
```python
db.add(food_item)
db.flush()  # ← Gets food_id but doesn't commit
food_id = food_item.food_id

db.add(FoodLog(food_id=food_id, ...))
db.flush()

db.commit()  # ← Both operations commit together (atomic)
```

---

## 4. Food Logging System

### Where Logs Are Stored

**Database Table**: `food_log`
```sql
CREATE TABLE food_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    quantity REAL DEFAULT 1.0,
    unit TEXT,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES food_items(food_id)
);
```

**File Location**:
- Development: `backend/nutri_indian.db` (local file)
- Production: `/data/nutri_indian.db` (Railway volume)

### Log Creation Flow
```
Mobile: User clicks "Add" on a food
  ↓
API.addFoodLog({user_id, food_id, quantity})
  ↓
POST /food-logs
  ↓
backend/app/api/food_logs.py: add_food_log()
  ↓
entry = FoodLog(user_id=1, food_id=42, quantity=1.5)
db.add(entry)
db.commit()
  ↓
Returns: {ok: true, log_id: 123}
  ↓
Mobile refreshes: fetchLogs()
  ↓
GET /food-logs/today?user_id=1
  ↓
Returns: [
  {log_id: 123, food_name: "Paneer", Calories_kcal: 260, ...},
  {log_id: 122, food_name: "Rice", Calories_kcal: 180, ...}
]
```

### Today's Logs Query
**Backend** (`main.py` lines 485-530):
```python
@app.get("/food-logs/today")
def get_today_logs(user_id: int, db: Session):
    # Calculate today's date range in UTC
    today_utc = datetime.utcnow().date()
    start_of_day = datetime.combine(today_utc, time.min)
    end_of_day = datetime.combine(today_utc, time.max)
    
    # Join FoodLog with FoodItem to get nutrition data
    logs = (
        db.query(FoodLog, FoodItem)
        .join(FoodItem, FoodItem.food_id == FoodLog.food_id)
        .filter(FoodLog.user_id == user_id)
        .filter(FoodLog.logged_at >= start_of_day)
        .filter(FoodLog.logged_at <= end_of_day)
        .all()
    )
    
    results = []
    for log, food in logs:
        qty = log.quantity
        results.append({
            "log_id": log.log_id,
            "food_name": food.food_name,
            "Calories_kcal": (food.Calories_kcal or 0) * qty,  # Scaled by quantity
            "Protein_g": (food.Protein_g or 0) * qty,
            # ... all other nutrients scaled
        })
    
    return results
```

---

## 5. Recommendation Engine (Automatic System)

### Thresholds & Configuration
**File**: `ml/config.py`
```python
MIN_IMPRESSIONS = 80        # Need 80 data points before training
MIN_ACCEPTS = 15            # Need 15 positive labels (accepted foods)
MIN_HOURS_BETWEEN = 6       # Train at most every 6 hours
MODEL_PATH = "/data/ml_artifacts/model.pkl"
SCALER_PATH = "/data/ml_artifacts/scaler.pkl"
LAST_TRAIN_PATH = "/data/ml_artifacts/last_train.txt"
```

### Automatic Workflow

#### Phase 0: Pure Rules (No ML)
```
User Count: Impressions < 80
Mode: 100% rule-based scoring
Action: Collect impression data silently
```

#### Phase 1: Training Triggered
```
Trigger Conditions:
  ✓ impression_count >= 80
  ✓ accepts >= 15
  ✓ hours_since_last_train >= 6

Action: train_model(db)
  1. Fetch all impressions
  2. Extract features (10D vectors)
  3. Train RandomForest
  4. Evaluate AUC
  5. Save model.pkl, scaler.pkl
  6. Write timestamp to last_train.txt
  7. Reload in memory (load_model_and_scaler())
```

#### Phase 2: Hybrid Scoring
```
User Count: Model loaded
Mode: 70% rules + 30% ML
Action: For each recommendation:
  rule_score = score_food(food, deficits)
  ml_prob = MODEL.predict_proba(features)
  final = 0.7 × rule_score + 0.3 × ml_prob × 100
```

### Rule-Based Scoring Algorithm
**File**: `main.py` lines 704-850 (approx)

```python
def score_food(food, deficits, conditions):
    score = 0
    reasons = []
    
    # MACRONUTRIENT SCORING
    score += min(food.Calories_kcal, deficits["Calories_kcal"]) * 0.2
    score += min(food.Protein_g, deficits["Protein_g"]) * 4.0  # Protein priority
    score += min(food.Carbohydrates_g, deficits["Carbohydrates_g"]) * 1.0
    score += min(food.Fats_g, deficits["Fats_g"]) * 0.5
    
    # MICRONUTRIENT BONUSES
    if food.Fibre_g >= 3:
        score += 10
        if food.Fibre_g >= 5:
            reasons.append("High fiber")
    
    if food.FreeSugar_g < 5:
        score += 8
        reasons.append("Low sugar")
    
    if food.Sodium_mg < 200:
        score += 5
        reasons.append("Low sodium")
    
    # MINERAL SCORING
    if deficits["Iron_mg"] > 0 and food.Iron_mg > 2:
        score += min(food.Iron_mg, deficits["Iron_mg"]) * 2
        reasons.append("Good iron source")
    
    # PENALTIES
    if food.Fats_g > 20:
        score -= food.Fats_g * 2
    
    # JUNK FOOD PENALTY
    junk_words = ["burfi", "laddu", "cake", "sweet", "cookie"]
    if any(word in food.food_name.lower() for word in junk_words):
        score -= 80  # Heavy penalty
    
    # HEALTH CONDITION PENALTIES
    if conditions.get("has_diabetes") or conditions.get("has_pcos"):
        if food.Carbohydrates_g > 30:
            score -= 30
        if food.FreeSugar_g > 10:
            score -= 25
    
    if conditions.get("has_hypertension"):
        if food.Sodium_mg > 400:
            score -= 25
    
    return score, reasons
```

### Impression Recording
**When**: Every time recommendations are shown
**File**: `main.py` (recommendation endpoint)

```python
# After generating top 10 recommendations
for rank, (food, score) in enumerate(top_10, start=1):
    impression = RecommendationImpression(
        user_id=req.user_id,
        food_id=food.food_id,
        deficits=json.dumps(deficits),  # Store current state
        rank=rank,
        rule_score=score,
        added=False  # Default: not accepted yet
    )
    db.add(impression)
db.commit()
```

**When User Accepts**:
```python
@app.put("/impressions/{id}/mark-added")
def mark_impression_added(id: int, db: Session):
    impression = db.query(RecommendationImpression).get(id)
    impression.added = True  # ← Positive label for ML
    impression.added_at = datetime.now()
    db.commit()
```

---

## 6. Machine Learning Training Pipeline

### Training Data Structure
```
RecommendationImpression Table:
┌────┬─────────┬─────────┬──────────────────────┬──────┬────────────┬───────┐
│ id │ user_id │ food_id │ deficits (JSON)      │ rank │ rule_score │ added │
├────┼─────────┼─────────┼──────────────────────┼──────┼────────────┼───────┤
│ 1  │ 1       │ 42      │ {"Protein_g": 45...} │ 1    │ 85.2       │ True  │ ← User accepted
│ 2  │ 1       │ 53      │ {"Protein_g": 45...} │ 2    │ 78.1       │ False │ ← User ignored
│ 3  │ 1       │ 27      │ {"Protein_g": 45...} │ 3    │ 72.5       │ False │
│ 4  │ 1       │ 91      │ {"Protein_g": 30...} │ 1    │ 90.3       │ True  │
...
│ 85 │ 2       │ 15      │ {"Protein_g": 60...} │ 5    │ 65.0       │ False │
```

### Feature Matrix Construction
```python
# For each impression row:
row_1_features = [
    45/100,      # Protein deficit normalized
    20/80,       # Fat deficit
    150/200,     # Carb deficit
    42/500,      # Food's calories
    25/30,       # Food's protein
    ...
    1/10,        # Rank (position 1)
    85.2/100     # Rule score
]

X = [row_1_features, row_2_features, ..., row_85_features]  # (85, 10) matrix
y = [1, 0, 0, 1, ..., 0]  # Labels: 1=accepted, 0=rejected
```

### Training Process Visualization
```
check_and_retrain_in_background()
  │
  ├─► should_retrain(db)?
  │     │
  │     ├─► Check impression count >= 80? ✓
  │     ├─► Check accepts >= 15? ✓
  │     └─► Check hours >= 6 since last train? ✓
  │
  ├─► train_model(db)
  │     │
  │     ├─► Fetch all RecommendationImpressions
  │     │
  │     ├─► Build X (features) and y (labels)
  │     │
  │     ├─► scaler = StandardScaler()
  │     ├─► X_scaled = scaler.fit_transform(X)
  │     │
  │     ├─► X_train, X_test = train_test_split(X_scaled, y)
  │     │
  │     ├─► model = RandomForestClassifier(...)
  │     ├─► model.fit(X_train, y_train)
  │     │
  │     ├─► auc = roc_auc_score(y_test, predictions)
  │     │   Output: "AUC: 0.752"
  │     │
  │     ├─► joblib.dump(model, "/data/ml_artifacts/model.pkl")
  │     ├─► joblib.dump(scaler, "/data/ml_artifacts/scaler.pkl")
  │     ├─► write_timestamp("/data/ml_artifacts/last_train.txt")
  │     │
  │     └─► load_model_and_scaler()  # Reload in memory
  │
  └─► Next recommendation uses hybrid scoring
```

---

## 7. Complete Data Flow Diagram

### End-to-End User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONBOARDING FLOW                              │
└─────────────────────────────────────────────────────────────────┘
Mobile: setup.js
  │
  ├─► User enters: username, age, weight, height, health conditions
  │
  ├─► API.computeGoals() → POST /goals/compute
  │     Backend calculates: BMR, TDEE, macros, micros
  │     Returns: {daily_calories: 2000, protein_g: 100, ...}
  │
  ├─► API.check-username() → POST /users/check-username
  │     If exists: return user_id (login)
  │     If new: API.register() → POST /users/register
  │
  └─► AsyncStorage.multiSet([
        ["user_id", "1"],
        ["username", "john_doe"],
        ["nutrimate_goals", "{daily_calories: 2000, ...}"]
      ])

┌─────────────────────────────────────────────────────────────────┐
│                    FOOD LOGGING FLOW                            │
└─────────────────────────────────────────────────────────────────┘
Mobile: FoodLogScreen.js
  │
  ├─► User types "paneer" → API.searchFoods("paneer")
  │     GET /foods?query=paneer&limit=20
  │     Backend: db.query(FoodItem).filter(food_name LIKE '%paneer%')
  │     Returns: [{food_id: 42, food_name: "Paneer", Calories_kcal: 260}]
  │
  ├─► User clicks "Add" → API.addFoodLog({user_id: 1, food_id: 42, quantity: 1})
  │     POST /food-logs
  │     Backend INSERT INTO food_log: (user_id=1, food_id=42, quantity=1, logged_at=NOW())
  │     Returns: {ok: true, log_id: 543}
  │
  └─► Mobile refreshes → API.getTodayLogs(user_id=1)
        GET /food-logs/today?user_id=1
        Backend: JOIN food_log + food_items WHERE date=today
        Returns: [{log_id: 543, food_name: "Paneer", Calories_kcal: 260}]

┌─────────────────────────────────────────────────────────────────┐
│                 RECOMMENDATION FLOW                             │
└─────────────────────────────────────────────────────────────────┘
Mobile: RecommendScreen.js
  │
  ├─► Fetch goals from AsyncStorage
  ├─► Fetch today's logs → API.getTodayLogs()
  │
  ├─► Calculate totals: sum(logs.Calories_kcal), sum(logs.Protein_g), ...
  │
  ├─► API.generateRecommendations({
        user_id: 1,
        daily_calories: 2000,
        protein_g: 100,
        current_totals: {Calories_kcal: 1200, Protein_g: 45}
      })
  │
  ├─► Backend: POST /recommendations/generate
  │     │
  │     ├─► Calculate deficits:
  │     │     Protein deficit = 100 - 45 = 55g
  │     │     Calorie deficit = 2000 - 1200 = 800 kcal
  │     │
  │     ├─► Fetch ALL foods: db.query(FoodItem).all()
  │     │
  │     ├─► For each food:
  │     │     │
  │     │     ├─► rule_score = score_food(food, deficits, conditions)
  │     │     │
  │     │     ├─► IF model_loaded:
  │     │     │     features = extract_features(food, deficits)
  │     │     │     ml_prob = MODEL.predict_proba(features)
  │     │     │     final_score = 0.7 × rule_score + 0.3 × ml_prob
  │     │     │   ELSE:
  │     │     │     final_score = rule_score
  │     │     │
  │     │     └─► scored_foods.append((food, final_score))
  │     │
  │     ├─► Sort by score DESC → Take top 10
  │     │
  │     ├─► Record impressions:
  │     │     FOR each top_10 food:
  │     │       INSERT INTO recommendation_impressions (
  │     │         user_id, food_id, deficits, rank, rule_score, added=False
  │     │       )
  │     │
  │     └─► Return: [
  │           {food_name: "Chicken Breast", score: 95.2, reasons: ["High protein"]},
  │           {food_name: "Spinach", score: 87.5, reasons: ["Good iron source"]},
  │           ...
  │         ]
  │
  └─► Mobile displays list with reasoning badges

┌─────────────────────────────────────────────────────────────────┐
│              ML TRAINING (BACKGROUND)                           │
└─────────────────────────────────────────────────────────────────┘
Triggered by: Periodic check OR after impression recording
  │
  ├─► should_retrain(db)?
  │     Check: impressions >= 80, accepts >= 15, hours >= 6
  │
  ├─► IF True: train_model(db)
  │     │
  │     ├─► Extract features from all impressions
  │     ├─► Train RandomForest on (X, y)
  │     ├─► Evaluate AUC
  │     ├─► Save model.pkl, scaler.pkl
  │     ├─► Update last_train.txt timestamp
  │     └─► Reload model in memory
  │
  └─► Next recommendations use hybrid scoring automatically
```

---

## Summary

### Critical Files by Function

**Database Schema**: `app/models.py`  
**API Logic**: `app/api/main.py`  
**Food CRUD**: `app/api/foods.py`  
**User Auth**: `app/api/users.py`  
**ML Inference**: `ml/predictor.py`  
**ML Training**: `ml/trainer.py`  
**Mobile API Client**: `src/api.js`  
**Barcode Integration**: `src/openfood.js`  

### Data Storage Locations

**SQLite Database**: `/data/nutri_indian.db` (production) or `backend/nutri_indian.db` (dev)  
**ML Model**: `/data/ml_artifacts/model.pkl`  
**ML Scaler**: `/data/ml_artifacts/scaler.pkl`  
**Training Timestamp**: `/data/ml_artifacts/last_train.txt`  
**Mobile Cache**: AsyncStorage (device local storage)

### Automatic Systems

1. **ML Retraining**: Triggers every 6 hours if thresholds met (80 impressions, 15 accepts)
2. **Hybrid Scoring**: Automatically blends rules + ML after first training
3. **Impression Recording**: Every recommendation generates training data
4. **Daily Reset**: Logs filtered by UTC date for "today" calculation

---

**End of Technical Walkthrough**
