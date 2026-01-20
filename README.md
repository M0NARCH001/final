# NutriMate 🥗 — Personalized AI Diet Assistant

NutriMate is a nutrition-aware diet assistant that helps users **log food intake**, **calculate daily nutrient consumption**, compare it against **Recommended Dietary Allowance (RDA)**, and generate **food recommendations** based on nutrient gaps.

Unlike many diet apps, NutriMate focuses on:
- **Nutrient-based guidance (not just calories)**
- **RDA comparison**
- **Explainable recommendations**
- **Backend-first scalable architecture**

---

## ✨ Features

### ✅ Implemented
- Unified food database (Indian foods + USDA foods)
- Fast food search API (partial match, structured results)
- Food logging system
  - Add food log
  - View logs by date / today
  - Delete log
- Daily nutrition computation (calories, macros, micronutrients)
- RDA comparison module
  - % RDA achieved per nutrient
  - deficit/excess flags
- Recommendation engine (rule-based baseline)
  - identifies nutrient gaps
  - ranks foods to reduce deficiencies
  - explainable scoring
- FastAPI backend with modular routes
- React Native / Expo mobile app
  - Home / Food Log / Report screens
  - Recommendations generation + add-to-log flow

### 🛠 Planned
- ML-based personalization (accept/reject feedback learning)
- Barcode scanning + OpenFoodFacts integration
- Offline caching
- Recipe suggestions
- Trend analytics (weekly/monthly nutrient trends)

---

## 🧠 How NutriMate Works

1. User logs foods (serving-based, no weighing needed)
2. Backend calculates total nutrition intake
3. Intake is compared to RDA values based on life stage
4. Nutrient deficits are detected
5. Recommendation engine scores foods to close gaps
6. User can add recommendations back into their daily log

---

## 🧱 Tech Stack

### Backend
- Python + FastAPI
- SQLAlchemy ORM
- SQLite (dev)
- Pandas / NumPy for nutrition computation

### Mobile
- React Native (Expo)
- Expo Router
- Fetch-based API client

---

## 📁 Project Structure
Nutrimate-v2/
backend/
app/
api/
db/
models.py
scripts/
Datasets/
.env.example
mobile/
app/
(tabs)/
src/

---

## 🚀 Running the Project Locally

## 1) Backend Setup

### Create a virtual environment
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```
Install dependencies
```bash
pip install -r requirements.txt
```
Run FastAPI server
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```
Server runs at:
http://127.0.0.1:8000
Mobile (phone) will use your laptop IP, example:
http://192.168.x.x:8000
2) Datasets Setup
Datasets are not committed into GitHub due to file limits.
See:
backend/Datasets/README.md
3) Mobile Setup (Expo)
```bash
cd mobile
npm install
npx expo start
```
API Base URL
Update your dev machine IP in:
mobile/src/api.js
Example:
```bash
const DEV_MACHINE_IP = "192.168.29.117";
```
## 📌 API Endpoints (Backend)
Foods
```bash
GET /foods?query=rice&limit=20
```
Food Logs
```bash
POST /food-logs
GET /food-logs/today?user_id=1
GET /food-logs?user_id=1&date=YYYY-MM-DD
DELETE /food-logs/{log_id}
```
Reports
```bash
POST /reports/daily
GET /reports/today?user_id=1 (optional / fallback used if supported)
```
Recommendations
```bash
POST /recommendations/generate
```
## 🧪 Recommendation Engine (Baseline)
Current recommendation system is rule-based and explainable:
Find nutrient deficits: RDA - Intake
Score foods based on how much they reduce deficits
Penalize for excess sodium/sugar
Normalize by calories
Return Top-K foods
Future version will add ML ranking on user acceptance feedback.
## 🖼 Screenshots
(Add screenshots here later)
Home Screen
Food Log Screen
Report Screen
Recommendations
## 👨💻 Author
Veerendra Virothi
NutriMate — Personalized AI Diet Assistant
## 📜 License
This project is built for learning / portfolio purposes.
