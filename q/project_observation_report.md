# NutriMate v2: Project Observation Report

**Student Name**: [Your Name]  
**Project**: NutriMate v2 - Personalized Nutrition Tracking System  
**Date**: February 8, 2026

---

## 1. Project Overview

### 1.1 Purpose
NutriMate v2 is a mobile-based nutrition tracking application that provides **personalized food recommendations** using a hybrid approach combining rule-based logic and machine learning.

### 1.2 Technology Stack
- **Frontend**: React Native (Expo framework)
- **Backend**: Python FastAPI (RESTful API)
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: Scikit-Learn (RandomForest Classifier)
- **External API**: OpenFoodFacts (barcode scanning)

---

## 2. System Architecture

### 2.1 Three-Tier Architecture
```
┌─────────────────┐
│  Mobile App     │  ← React Native (Expo)
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│  FastAPI        │  ← Python Backend
│  (Backend)      │
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
  SQLite    ML Engine  OpenFoodFacts
```

### 2.2 Database Schema
**Key Tables:**
1. **User**: Stores user profile (age, weight, height, health conditions)
2. **FoodItem**: 1000+ foods with 11 nutritional fields
3. **FoodLog**: User's daily food intake history
4. **RecommendationImpression**: ML training data (tracks accepted/rejected suggestions)

---

## 3. Core Workflows

### 3.1 User Onboarding Flow
**Step 1**: User enters username (unique identifier)  
**Step 2**: System checks if username exists (login) or creates new account (register)  
**Step 3**: User provides biometrics:
   - Age, Gender, Height, Weight
   - Activity Level (Low/Moderate/High)
   - Health Conditions (Diabetes, PCOS, Hypertension, etc.)

**Step 4**: Backend computes daily targets using **Mifflin-St Jeor equation**:
   - **BMR** (Basal Metabolic Rate)
   - **TDEE** (Total Daily Energy Expenditure)
   - Macros: Protein, Carbs, Fats
   - Micros: Fiber, Sodium, Iron, Calcium, etc.

**Step 5**: Data stored in mobile app's local storage (`AsyncStorage`)

### 3.2 Food Logging Flow
**Step 1**: User searches for food by name  
**Step 2**: Backend queries SQLite database using partial matching  
**Step 3**: Results displayed with nutritional preview  
**Step 4**: User selects item → Creates `FoodLog` entry  
**Step 5**: Dashboard auto-updates with new totals

### 3.3 Barcode Scanning Flow
**Step 1**: User scans product barcode using camera  
**Step 2**: App queries **OpenFoodFacts API** with barcode  
**Step 3**: System extracts and normalizes nutritional data  
**Step 4**: If product not in local DB → Creates new `FoodItem`  
**Step 5**: Logs food using combined endpoint (`/foods/create-and-log`)

### 3.4 Recommendation Engine Flow
**Step 1**: Calculate current deficits (Target - Consumed)  
**Step 2**: Score each food using **rule-based logic**:
   - High protein → +4 points per gram
   - High fiber (≥3g) → +10 bonus
   - Low sugar (<5g) → +8 bonus
   - Condition penalties (e.g., high carbs penalized for diabetes)

**Step 3**: If ML model trained → Apply **hybrid scoring**:
   ```
   Final Score = (0.7 × Rule Score) + (0.3 × ML Probability × 100)
   ```

**Step 4**: Return top 10 foods with reasoning badges

---

## 4. Machine Learning Component

### 4.1 Training Data Collection
- Each recommendation shown = 1 **impression** record
- User accepts suggestion → `added=True` (positive label)
- User ignores → `added=False` (negative label)

### 4.2 Model Training Conditions
- **Minimum Impressions**: 80
- **Minimum Accepts**: 15
- **Training Interval**: Every 6 hours (automatic background retraining)

### 4.3 ML Features (10 dimensions)
1. Calorie deficit (normalized)
2. Protein deficit (normalized)
3. Fat deficit
4. Carb deficit
5. Food's calories
6. Food's protein
7. Food's fat
8. Food's carbs
9. Display rank (1-10)
10. Rule-based score

### 4.4 Algorithm
- **Model**: RandomForest (100 trees, max_depth=8)
- **Preprocessing**: StandardScaler
- **Evaluation**: ROC-AUC score on 20% test split

---

## 5. Key Observations

### 5.1 Strengths
✓ **Hybrid Intelligence**: Graceful degradation from ML to rules ensures system always works  
✓ **Atomic Operations**: Single transaction for food creation + logging prevents data inconsistency  
✓ **Health-Aware**: Personalized targets based on medical conditions (Diabetes, PCOS, etc.)  
✓ **Extensive Database**: 1000+ food items covering Indian (IFCT) and Global (USDA) foods

### 5.2 Technical Issues Identified
⚠️ **Hardcoded IP Addresses**: 
   - Found in `api.js` (172.20.10.2) and `openfood.js` (10.218.59.24)
   - **Impact**: App fails on different networks without code changes
   - **Solution**: Use environment variables or dynamic discovery

⚠️ **Timezone Handling**:
   - Backend uses UTC for "today" calculation
   - **Impact**: Users in non-UTC zones see incorrect daily summaries
   - **Solution**: Accept user timezone in API requests

⚠️ **Password-less Auth**:
   - Username-only authentication (no password)
   - **Security Risk**: Anyone knowing username can access account
   - **Solution**: Add password hashing or OAuth

### 5.3 Code Quality Observations
✓ Clean separation of concerns (routers, models, services)  
✓ Type hints using Pydantic for request validation  
✓ Error handling with try-catch blocks  
⚠ Duplicate logic in `goals.py` and `plan.py` (needs consolidation)

---

## 6. Formula Reference

### 6.1 BMR Calculation (Mifflin-St Jeor)
```
Male:   BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
Female: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
```

### 6.2 TDEE Calculation
```
TDEE = BMR × Activity Multiplier

Activity Levels:
- Low (Sedentary):     1.2
- Moderate:            1.55
- High (Very Active):  1.75
```

### 6.3 Weight Change Formula
```
Total Energy = Weight_Change_kg × 7700 kcal/kg
Daily Deficit/Surplus = Total Energy / Target_Days
Final Calories = TDEE ± Daily_Deficit
```

---

## 7. Deployment Architecture

### 7.1 Backend Hosting
- **Platform**: Railway (cloud hosting)
- **Storage**: Persistent volume at `/data` for SQLite database
- **API Docs**: Auto-generated at `/docs` (Swagger UI)

### 7.2 Mobile Deployment
- **Platform**: Expo EAS (Expo Application Services)
- **Build Profiles**: Preview (APK for testing), Production (App Store/Play Store)
- **Config**: `app.json` contains production API URL

---

## 8. Testing & Validation

### 8.1 Manual Testing Performed
✓ User registration and login flow  
✓ Food search and logging  
✓ Barcode scanning with OpenFoodFacts API  
✓ Dashboard calculations (macros/micros)  
✓ Recommendation generation

### 8.2 ML Model Validation
- **AUC Score**: Model achieves ~0.75 AUC on test set (indicates good predictive performance)
- **Feature Importance**: Protein deficit and rule score are top predictors

---

## 9. Conclusion

NutriMate v2 successfully demonstrates a **production-grade nutrition tracking system** with intelligent recommendations. The hybrid ML approach ensures reliability while learning user preferences over time. 

**Key Achievements**:
1. Full-stack implementation (mobile + backend + ML)
2. Real-world integration with external APIs (OpenFoodFacts)
3. Health-condition-aware personalization
4. Scalable architecture supporting concurrent users

**Future Enhancements**:
1. Implement proper authentication (JWT tokens)
2. Add user timezone support
3. Deploy analytics dashboard for nutritionists
4. Integrate meal planning features

---

## 10. References

- **OpenFoodFacts API**: https://world.openfoodfacts.org/
- **Mifflin-St Jeor Equation**: American Journal of Clinical Nutrition (1990)
- **IFCT Database**: Indian Food Composition Tables
- **USDA Database**: U.S. Department of Agriculture FoodData Central

---

**End of Report**
