# NutriMate v2 - ML Architecture & Regional Food Dataset Description

## 1. ML Architecture Overview

NutriMate v2 uses a **hybrid recommendation engine** that blends rule-based nutritional scoring (70%) with a machine-learned user preference model (30%). The ML pipeline is built with **scikit-learn** and follows a phased rollout strategy.

### 1.1 Core ML Components

| Component | File | Purpose |
|-----------|------|---------|
| Trainer | `backend/ml/trainer.py` | Trains RandomForest model on user interaction data |
| Predictor | `backend/ml/predictor.py` | Runs inference and computes hybrid scores |
| Config | `backend/ml/config.py` | ML constants, paths, logging setup |
| Git Push | `backend/ml/git_push.py` | Auto-pushes trained model artifacts to GitHub |

### 1.2 Model Details

- **Algorithm**: Random Forest Classifier (scikit-learn)
- **Hyperparameters**:
  - `n_estimators`: 100 trees
  - `max_depth`: 8 (prevents overfitting)
  - `class_weight`: "balanced" (handles class imbalance)
- **Feature Vector**: 12-dimensional input per food item
- **Serialization**: joblib (`rf_recommender.joblib`, `scaler.joblib`)
- **Scaling**: StandardScaler for feature normalization

### 1.3 Feature Engineering (12 Features)

| # | Feature | Category | Description |
|---|---------|----------|-------------|
| 1 | deficit_calories | Deficit (normalized) | Remaining calorie gap for the day |
| 2 | deficit_protein | Deficit (normalized) | Remaining protein gap |
| 3 | deficit_fats | Deficit (normalized) | Remaining fat gap |
| 4 | deficit_carbs | Deficit (normalized) | Remaining carbs gap |
| 5 | food_calories | Food (normalized) | Calorie content of the food item |
| 6 | food_protein | Food (normalized) | Protein content of the food item |
| 7 | food_fats | Food (normalized) | Fat content of the food item |
| 8 | food_carbs | Food (normalized) | Carb content of the food item |
| 9 | rank | Context | Ranking position in recommendation list |
| 10 | rule_score | Context | Score from rule-based scoring engine |
| 11 | is_region_match | Region | 1.0 if user's region matches food's region |
| 12 | has_specific_region | Region | 1.0 if food has a specific region (not "All India") |

### 1.4 Training Pipeline

**Training Data Source**: `RecommendationImpression` table in the database, which logs every recommendation shown to a user and whether the user accepted it.

**Automatic Training Triggers** (all conditions must be met):
- >= 80 total impressions recorded
- >= 15 accepted recommendations
- >= 6 hours since last training run

**Training Workflow**:
1. Fetch all impressions with known outcomes (accepted or not)
2. Extract 12-dimensional feature vectors
3. Split data (train/test)
4. Train RandomForest with StandardScaler
5. Evaluate with ROC-AUC score
6. Save model artifacts via joblib
7. Auto-push artifacts to GitHub with performance metrics in commit message
8. Reload model in memory for live inference

**Retry Logic**: Exponential backoff on training failure.

### 1.5 Phased Rollout Strategy

| Phase | Condition | Scoring Method |
|-------|-----------|----------------|
| Phase 0 (Cold Start) | < 80 impressions | 100% rule-based scoring |
| Phase 1 (Training) | >= 80 impressions + >= 15 accepts | Model trains automatically |
| Phase 2 (Hybrid) | Model available | 70% rule-based + 30% ML probability |

### 1.6 Rule-Based Scoring Engine (70% Weight)

Located in `backend/app/api/main.py` - `score_food()` function.

**Macronutrient Scoring Weights**:
- Calories: `min(food_kcal, deficit_kcal) x 0.2`
- Protein: `min(food_protein, deficit_protein) x 4.0` (highest priority)
- Carbs: `min(food_carbs, deficit_carbs) x 1.0`
- Fats: `min(food_fat, deficit_fat) x 0.5`

**Micronutrient Bonuses**:
- Fiber >= 3g: +10 points
- Sugar < 5g: +8 points
- Sodium < 200mg: +5 points
- Iron > 2mg: scaled bonus
- Calcium > 50mg: scaled bonus
- Vitamin C > 10mg: scaled bonus

**Penalties**:
- High fat (>20g): -fat x 2
- Junk foods (sweets, pastries): -80 points
- Health-condition specific penalties (diabetes, PCOS, hypertension)

**Filters (excluded from recommendations)**:
- Ultra-low calorie foods (<40 kcal)
- Condiments (masala, chutney, pickle, papad, sauce, etc.)

### 1.7 Hybrid Score Computation

```
final_score = (0.70 x rule_score) + (0.30 x ml_probability x 100)
```

If ML model is not loaded or not yet trained, the system gracefully falls back to 100% rule-based scoring.

### 1.8 Inference Flow

1. API receives recommendation request with user_id
2. Calculate daily nutritional deficits (target - consumed)
3. Score all eligible foods via rule-based engine
4. If ML model is loaded:
   - Extract 12-feature vector per food
   - Scale features via StandardScaler
   - Get probability from RandomForest
   - Blend with rule score
5. Return top 5 foods with reasoning badges ("High Protein", "Low Sugar", etc.)
6. Log impressions for future training

### 1.9 ML Artifacts Storage

- **Local development**: `backend/ml_artifacts/`
- **Railway (production)**: `/data/ml_artifacts/` (persistent volume)
- **GitHub backup**: `backend/ml_artifacts/` in the repository (auto-pushed after training)

### 1.10 ML Dependencies

- `scikit-learn` - RandomForest, StandardScaler, train_test_split, roc_auc_score
- `joblib` - Model serialization/deserialization
- `numpy` - Array operations and feature vector construction

---

## 2. Regional Food Datasets

### 2.1 Dataset Status: CREATED

The regional food dataset **has been created** and is seeded into the SQLite database (`backend/nutri_indian.db`, ~434 KB). It contains **100+ Indian dishes** across **7 regional categories**.

### 2.2 Data Sources

| Source | Type | Status |
|--------|------|--------|
| Hardcoded Indian Foods | Python seed script | Active - `backend/scripts/seed_indian_foods.py` |
| IFCT (Indian Food Composition Tables) | CSV preprocessing | Referenced in `preprocess_all.py` (CSV files not in repo) |
| USDA Foods Database | CSV preprocessing | Referenced in `preprocess_all.py` (CSV files not in repo) |
| OpenFoodFacts API | Live barcode lookup | Active - `mobile/src/openfood.js` |

### 2.3 Regional Coverage

| Region | Example Foods | Count |
|--------|--------------|-------|
| Tamil Nadu (South Indian) | Idli, Dosa, Sambar, Chettinad Chicken, Rasam, Pongal | 15+ |
| Andhra Pradesh / Telangana | Pesarattu, Hyderabadi Biryani, Gongura Pachadi, Pulihora | 12+ |
| Kerala | Puttu, Kadala Curry, Appam with Stew, Karimeen Pollichathu | 12+ |
| Karnataka | Bisi Bele Bath, Mysore Dosa, Ragi Mudde, Neer Dosa | 12+ |
| Maharashtra | Misal Pav, Vada Pav, Pav Bhaji, Puran Poli, Poha | 12+ |
| Punjab / North India | Chole Bhature, Butter Chicken, Sarson Saag, Paneer Tikka | 15+ |
| All India (Generic) | Dal, Rice, Roti, Raita, Salad, Curd | 20+ |

### 2.4 Database Schema

#### `food_items` Table
| Column | Type | Description |
|--------|------|-------------|
| food_id | Integer (PK) | Unique food identifier |
| food_name | Text | Display name |
| main_name | Text | Canonical name |
| subcategories_json | Text | JSON array of subcategories |
| region | Text | Legacy region field |
| region_id | Integer (FK) | Foreign key to regions table |
| Calories_kcal | Float | Energy in kcal |
| Protein_g | Float | Protein in grams |
| Carbohydrates_g | Float | Carbs in grams |
| Fats_g | Float | Fat in grams |
| FreeSugar_g | Float | Free sugar in grams |
| Fibre_g | Float | Dietary fiber in grams |
| Sodium_mg | Float | Sodium in milligrams |
| Calcium_mg | Float | Calcium in milligrams |
| Iron_mg | Float | Iron in milligrams |
| VitaminC_mg | Float | Vitamin C in milligrams |
| Folate_ug | Float | Folate in micrograms |
| serving_unit | Text | Default serving unit |
| serving_weight_g | Float | Weight per serving in grams |
| cuisine_type | Text | Cuisine classification |
| source | Text | Data source (e.g., NIN/IFCT) |

#### `regions` Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique region identifier |
| name | Text (unique) | Region name |
| description | Text | Region description |

**Seeded Regions**: All India, Tamil Nadu, Andhra Pradesh, Kerala, Karnataka, Maharashtra, Punjab

#### `rda` Table (Recommended Dietary Allowances)
| Column | Type | Description |
|--------|------|-------------|
| life_stage | Text | Age/gender category |
| Calories_kcal - Folate_ug | Float | RDA values for all 11 tracked nutrients |

### 2.5 Nutritional Coverage (11 Nutrients Tracked)

**Macronutrients** (4): Calories, Protein, Carbohydrates, Fats
**Sugars** (1): Free Sugar
**Micronutrients** (6): Fiber, Sodium, Calcium, Iron, Vitamin C, Folate

### 2.6 Data Seeding Scripts

| Script | Purpose |
|--------|---------|
| `backend/scripts/seed_indian_foods.py` | Seeds 100+ hardcoded Indian regional foods with full nutrition data |
| `backend/scripts/preprocess_all.py` | Preprocesses external CSV datasets (IFCT, USDA) |
| `backend/scripts/import_foods.py` | Bulk imports preprocessed CSV data into SQLite |
| `backend/scripts/import_rda.py` | Imports RDA standards |
| `backend/scripts/migrate_region_fk.py` | Migrates region text field to normalized FK relationship |

### 2.7 External Data Integration

**OpenFoodFacts (Barcode Scanning)**:
- API: `https://world.openfoodfacts.org/api/v0/product/{barcode}.json`
- Dynamically enriches the database when users scan new products
- Maps OpenFoodFacts nutriment fields to NutriMate's 11-nutrient schema
- Handles per-100g and per-serving calculations

---

## 3. Nutritional Intelligence

### 3.1 BMR Calculation (Mifflin-St Jeor Equation)
- Male: `(10 x weight_kg) + (6.25 x height_cm) - (5 x age) + 5`
- Female: `(10 x weight_kg) + (6.25 x height_cm) - (5 x age) - 161`

### 3.2 TDEE = BMR x Activity Multiplier
| Activity Level | Multiplier |
|---------------|------------|
| Sedentary | 1.2 |
| Lightly Active | 1.375 |
| Moderately Active | 1.55 |
| Very Active | 1.725 |
| Extra Active | 1.75 |

### 3.3 Health Condition Adjustments
| Condition | Nutritional Adjustments |
|-----------|------------------------|
| Diabetes | Lower carbs (40%), reduced sugar targets, scoring penalties for high-carb foods |
| Hypertension | Sodium restrictions, penalties for high-sodium foods |
| PCOS | Lower carbs, higher protein ratios |
| Muscle Gain | Higher protein (2.0-2.2 g/kg), increased calorie targets |
| Heart Health | Higher healthy fat allowance, fiber emphasis |

---

## 4. Architecture Diagram (Text)

```
+------------------+     +-------------------+     +------------------+
|   Mobile App     |     |   FastAPI Backend  |     |   SQLite DB      |
|   (Expo/RN)      |<--->|   (Python)         |<--->|  nutri_indian.db |
+------------------+     +-------------------+     +------------------+
| - Dashboard      |     | - Food Search API  |     | - food_items     |
| - Food Logging   |     | - Recommendation   |     | - regions        |
| - Barcode Scan   |     |   Engine           |     | - food_log       |
| - Recommendations|     | - Daily Summary    |     | - users          |
| - Profile/Setup  |     | - User Management  |     | - rda            |
+------------------+     | - ML Pipeline      |     | - impressions    |
        |                 +-------------------+     +------------------+
        |                         |
        v                         v
+------------------+     +-------------------+
| OpenFoodFacts    |     |   ML Artifacts     |
| API (Barcode)    |     | (joblib models)    |
+------------------+     +-------------------+
                                  |
                                  v
                          +-------------------+
                          |   GitHub Backup    |
                          | (Auto-push models) |
                          +-------------------+
```

---

## 5. Summary

| Aspect | Status | Details |
|--------|--------|---------|
| ML Model | Implemented | RandomForest with 12 features, hybrid scoring |
| Training Pipeline | Automated | Background training with auto-triggers |
| Regional Food Data | Created | 100+ Indian foods across 7 regions |
| Nutrition Tracking | 11 nutrients | Macros + micros with RDA standards |
| Barcode Integration | Active | OpenFoodFacts API for dynamic data enrichment |
| Health Personalization | 5 conditions | Diabetes, Hypertension, PCOS, Muscle Gain, Heart Health |
| Model Deployment | Automated | joblib serialization + GitHub auto-push |
