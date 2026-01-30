# 🥗 NutriMate

A **personalized nutrition tracking and recommendation system** that actively suggests foods to help you close nutritional gaps.

## Overview

Unlike simple calorie trackers, NutriMate provides intelligent, real-time food recommendations based on your nutritional deficits throughout the day.

### Key Features

- Create personalized health profiles (age, height, weight, activity level, goals)
- Receive daily calorie and macro targets
- Log foods throughout the day
- Track consumed vs target nutrients
- Get **real-time food recommendations** based on nutritional deficits

---

## 🏗 Architecture

NutriMate uses a **client-server architecture** with the following components:

### Frontend (React Native / Expo)

**Handles:**
- Setup UI
- Food search and logging
- Home dashboard
- Recommendations UI
- Profile edit/reset

**Local Storage:**
- `nutrimate_profile`
- `nutrimate_goals`

**Backend Integration:**
- Food search
- Logging
- Daily totals
- Recommendations

### Backend (FastAPI + SQLAlchemy)

**Handles:**
- Nutrition computation
- Persistent storage
- Recommendation logic

**Stack:**
- FastAPI
- SQLAlchemy ORM
- PostgreSQL / SQLite
- Pandas/Numpy (nutrition math)
- Rule-based recommendation engine (current)

---

## 📱 Frontend Flow

### 1. Setup Screen

Users enter their profile information:
- Name
- Age
- Gender
- Height
- Weight
- Activity level
- Goal (maintain / loss / gain)

**API Call:** `POST /compute-goals`

**Backend Returns:**
- BMR (Basal Metabolic Rate)
- TDEE (Total Daily Energy Expenditure)
- Daily calories
- Protein / carbs / fats targets

Data is stored in AsyncStorage as the **source of truth** for daily targets.

### 2. Home Screen

On load:
1. Reads `nutrimate_goals` from local storage
2. Fetches today's logs: `GET /food-logs/today`
3. Displays:
   - Total calories consumed
   - Protein / carbs / fats progress
   - List of today's foods

Home screen auto-refreshes when tab regains focus.

### 3. Log Screen

**Search Foods:** `GET /foods?query=pineapple`

Results display:
- Food name
- Calories
- Protein

**Add Food:** `POST /food-logs`

**Delete Food:** `DELETE /food-logs/{log_id}`

### 4. Recommendations Screen

**Core Feature Flow:**

1. Fetch today's logs: `GET /food-logs/today`
2. Combine with stored goals
3. Request recommendations: `POST /recommendations/generate`

**Backend Returns:**
- Totals
- Targets
- Recommended foods

Frontend renders list with:
- Food name
- Score
- "Add to Log" button

When user adds a recommended food, recommendations refresh automatically.

### 5. Profile Screen

Allows users to:
- Edit profile
- Reset profile (clears AsyncStorage)
- Force re-setup

---

## 🗄 Database Schema

### Foods Table

Contains nutrition per serving:
- `food_id`
- `food_name`
- `Calories_kcal`
- `Protein_g`
- `Fats_g`
- `Carbohydrates_g`

**Data Sources:**
- IFCT (Indian foods)
- USDA

### FoodLogs Table

Stores user intake:
- `log_id`
- `user_id`
- `food_id`
- `quantity`
- `logged_at`

Every "Add" operation inserts one row.

---

## ⚙ Backend Core Pipelines

### 1. Goal Computation

**Endpoint:** `POST /compute-goals`

**BMR Calculation:** Uses Mifflin St Jeor equation

**TDEE Calculation:** BMR × activity factor

**Goal Adjustments:**
- Weight loss → calorie deficit
- Weight gain → calorie surplus
- Maintain → TDEE

**Macro Distribution:**
- Protein: weight-based calculation
- Fat: percentage of calories
- Carbs: remaining calories

**Returns:**
```json
{
  "daily_calories": 2000,
  "protein_g": 120,
  "fat_g": 67,
  "carbs_g": 250
}
```

### 2. Food Logging

**Add:** `POST /food-logs`

**Delete:** `DELETE /food-logs/{id}`

**Fetch Today:** `GET /food-logs/today`

Backend joins FoodLogs + Foods tables to produce complete nutrition data.

### 3. Daily Totals

**Function:** `compute_totals_from_logs()`

Process:
- Loops through today's logs
- Multiplies nutrients × quantity
- Sums everything

**Produces:**
```json
{
  "Calories_kcal": 1200,
  "Protein_g": 60,
  "Fats_g": 40,
  "Carbohydrates_g": 150
}
```

---

## 🧠 Recommendation Engine

### Current Implementation: Rule-Based Scoring

**Not ML yet** — uses a rule-based scoring system.

### Algorithm Flow

#### Step 1: Calculate Deficits
```
deficits = targets - totals
```

Example: If protein target = 120g and consumed = 40g → deficit = 80g

#### Step 2: Iterate All Foods
Backend loads entire Foods table for scoring.

#### Step 3: Filter Junk
Removes:
- Very low calorie foods
- High carb + low protein items
- Desserts
- Sweets (burfi, etc.)

#### Step 4: Score Each Food
**Function:** `score_food(food, deficits)`

**Scoring Weights:**
- Protein × 4
- Carbs × 1
- Fat × 0.5
- Calories × 0.2

**Additional Logic:**
- Penalizes sweets
- Penalizes fat bombs
- Rejects poor protein density
- Bonus for keywords (dal, paneer, egg, etc.)

#### Step 5: Sort and Return Top N
Returns top 5 foods with:
```json
{
  "food_id": 123,
  "food_name": "Grilled Chicken",
  "score": 85.5
}
```

---

## 🔄 Data Flow

The system creates a **closed feedback loop**:

```
User eats → Logs food
    ↓
Backend stores log
    ↓
Home recomputes totals
    ↓
Deficits change
    ↓
Recommendations change
    ↓
User eats suggested food
    ↓
Loop continues
```

---

## 🚧 Current Limitations

- No portion-size optimization
- No personalization memory
- No diversity control
- Rule-based (not ML)
- No cuisine preference
- No allergy filters

**Note:** Architecture already supports future ML integration.

---

## 🚀 Future Roadmap: ML Path

### Planned ML Implementation

**Training Data:**
- User deficits
- User history
- Food acceptance rate

**Prediction Goal:**
> "What food will this user most likely eat that fixes their nutritional deficits?"

This will transform the system into a true AI-powered recommendation engine.

---

## ✅ Summary

NutriMate is a **full-stack nutrition system** featuring:

- Personalized daily targets
- Real-time food logging
- Dynamic deficit computation
- Intelligent food recommendation loop

**Status:** Production-grade architecture with rule-based recommendations. ML layer is the next evolution.

---

## 🛠 Tech Stack

**Frontend:**
- React Native
- Expo
- AsyncStorage

**Backend:**
- FastAPI
- SQLAlchemy ORM
- PostgreSQL / SQLite
- Pandas
- NumPy

**Data:**
- IFCT (Indian Food Composition Tables)
- USDA Food Database

