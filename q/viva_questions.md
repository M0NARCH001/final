# NutriMate v2: Potential Viva/Interview Questions

## Backend Questions (10)

### 1. How does the backend work and what framework did you use?
**Answer**: The backend is built using **FastAPI**, a modern Python web framework. It follows a REST API architecture where the mobile app makes HTTP requests to various endpoints. FastAPI handles routing, request validation using Pydantic models, and dependency injection for database sessions.

### 2. What database did you use and why?
**Answer**: We used **SQLite** with **SQLAlchemy ORM**. SQLite was chosen because:
- Lightweight and serverless (no separate DB server needed)
- File-based storage suitable for this project's scale
- Easy deployment on Railway with persistent volumes
- SQLAlchemy provides ORM abstraction for clean Python code

### 3. Explain the database schema - what are the main tables?
**Answer**: Four main tables:
- **User**: Stores biometrics, health conditions, and activity level
- **FoodItem**: Contains 1000+ foods with 11 nutritional fields (calories, protein, carbs, etc.)
- **FoodLog**: Records user's daily food intake (foreign key to User and FoodItem)
- **RecommendationImpression**: Training data for ML - tracks which recommendations users accept/reject

### 4. How do you calculate nutritional targets (BMR/TDEE)?
**Answer**: We use the **Mifflin-St Jeor equation** in `goals.py`:
- Calculate BMR based on weight, height, age, and gender
- Multiply BMR by activity multiplier (1.2 to 1.75) to get TDEE
- Adjust for weight loss/gain goals using 7700 kcal/kg rule
- Derive macros: Protein (1.6-2.0g/kg), Fat (25% of calories), Carbs (remainder)

### 5. What is the `/foods/create-and-log` endpoint and why is it important?
**Answer**: It's a **combined atomic transaction** that creates a new food item AND logs it in one operation. This prevents:
- Race conditions where food creation succeeds but logging fails
- Duplicate foods from multiple clicks
- Data inconsistency between FoodItem and FoodLog tables
Uses `db.flush()` to get the `food_id` before committing both operations together.

### 6. How does the backend handle CORS for mobile app communication?
**Answer**: FastAPI's `CORSMiddleware` is configured in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Currently open for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```
In production, this should be restricted to specific mobile app origins.

### 7. Explain the recommendation scoring algorithm.
**Answer**: Two-phase scoring:
- **Rule-based**: Foods scored based on nutritional deficits (protein +4pts/g, fiber +10pts if ≥3g, low sugar +8pts)
- **Hybrid (if ML trained)**: `Final = 0.7 × RuleScore + 0.3 × MLProbability × 100`
- Penalties applied for junk food (-80pts) and health conditions (e.g., high carbs penalized for diabetes)

### 8. How do you handle user authentication?
**Answer**: **Username-based passwordless authentication**:
- `/users/check-username` checks if username exists
- If exists → returns `user_id` (acts like login)
- If new → `/users/register` creates account
- Mobile app stores `user_id` in AsyncStorage for session persistence
*Note: Not secure for production - should add password hashing or OAuth*

### 9. What happens when the backend starts up (lifespan events)?
**Answer**: The `lifespan` context manager in `main.py`:
1. Checks if ML components are available (`ML_AVAILABLE` flag)
2. Calls `load_model_and_scaler()` to load trained RandomForest model from disk
3. Initializes model in memory for fast inference
4. Logs startup status to console

### 10. How does the backend integrate with external APIs?
**Answer**: **OpenFoodFacts API** integration:
- Mobile app directly calls OpenFoodFacts (not through backend)
- Backend provides `/foods/create-and-log` to save scanned products
- Nutrient mapping happens in mobile (`openfood.js`) to normalize different field names (e.g., `energy-kcal_100g` → `Calories_kcal`)

---

## Mobile (React Native/Expo) Questions (10)

### 1. What framework did you use for the mobile app and why?
**Answer**: **React Native with Expo**. Benefits:
- Cross-platform (iOS + Android from single codebase)
- Expo provides managed workflow with built-in APIs (Camera, AsyncStorage)
- Expo Router for file-based routing
- Fast development with hot reload
- Easy deployment via Expo EAS (Expo Application Services)

### 2. How does the mobile app store user data locally?
**Answer**: Using **AsyncStorage** (React Native's key-value storage):
- `user_id`: Unique identifier from backend
- `username`: For display and re-authentication
- `nutrimate_profile`: User biometrics and health conditions
- `nutrimate_goals`: Computed daily targets (calories, macros, micros)
Data persists across app restarts for offline viewing.

### 3. Explain the user onboarding flow in detail.
**Answer**: (`setup.js`)
1. User enters username and biometrics
2. App validates username format (3-20 chars, alphanumeric)
3. Calls `API.computeGoals()` to get targets from backend
4. Calls `API.check-username()` to see if user exists
5. If new → `API.register()`, if existing → login with existing `user_id`
6. Stores data in AsyncStorage
7. Navigates to `/(tabs)` dashboard using Expo Router

### 4. How does the barcode scanner work?
**Answer**: 
1. Uses `expo-camera` to access device camera
2. User scans product barcode → extracts barcode number
3. Calls `getProductFromOpenFoodFacts(barcode)` from `openfood.js`
4. Maps OpenFoodFacts JSON to Nutrimate schema (handles mg/g conversion for sodium)
5. If product not in DB → calls `API.createFoodAndLog()` to add and log in one step
6. Navigates to FoodLogScreen with pre-filled search

### 5. What is Expo Router and how is it used in this project?
**Answer**: **File-based routing system** (like Next.js for mobile):
- `app/(tabs)/index.js` → Dashboard at `/`
- `app/(tabs)/FoodLogScreen.js` → Food logging tab
- `app/setup.js` → Setup screen at `/setup`
- Navigation uses `useRouter()` hook: `router.replace('/(tabs)')`
- URL params: `useLocalSearchParams()` to get barcode data

### 6. How does the app refresh data when navigating between screens?
**Answer**: Using **`useFocusEffect`** hook from React Navigation:
```javascript
useFocusEffect(
  useCallback(() => {
    fetchLogs(); // Runs every time screen comes into focus
  }, [])
);
```
This ensures Dashboard updates when user logs food in another tab.

### 7. Explain how the mobile app communicates with the backend.
**Answer**: Centralized API client in `src/api.js`:
- Detects environment (dev vs production)
- Dev: Uses local IP (`172.20.10.2:8000`) or Android emulator IP (`10.0.2.2`)
- Production: Reads from `expo-constants` (set in `app.json`)
- All endpoints wrapped in functions: `API.searchFoods()`, `API.addFoodLog()`, etc.
- Uses native `fetch()` with JSON headers

### 8. What UI components are used to display nutritional progress?
**Answer**:
- **CalorieProgressCircle**: Custom circular progress indicator (SVG-based or Canvas)
- **ProgressBar**: Horizontal bars showing macro/micro completion percentages
- **WarningBadge**: Colored alerts for high sugar/sodium or low minerals
- FlatList for efficient rendering of food logs (virtualized scrolling)

### 9. How do you handle errors in the mobile app?
**Answer**:
- Try-catch blocks around API calls
- User-friendly alerts: `alert(e.message || "Setup failed")`
- Fallback values: `Array.isArray(logs) ? logs : []` to prevent crashes
- Validation before API calls (e.g., check if username is empty)

### 10. What dependencies are critical for this mobile app?
**Answer**:
- **expo-router**: File-based navigation
- **expo-camera**: Barcode scanning
- **@react-native-async-storage/async-storage**: Local data persistence
- **axios** (listed but using native fetch): HTTP client
- **@react-native-community/slider**: Weight/days input slider
- **react-native-safe-area-context**: Handle notches/safe areas

---

## ML Engine Questions (10)

### 1. What machine learning algorithm did you use and why?
**Answer**: **RandomForestClassifier** from Scikit-Learn because:
- Handles non-linear relationships between features
- Resistant to overfitting (ensemble of 100 trees)
- Works well with small datasets (80+ impressions)
- Provides feature importance for debugging
- No need for extensive hyperparameter tuning

### 2. What are the ML model's hyperparameters?
**Answer**: (from `ml/trainer.py`)
```python
RandomForestClassifier(
    n_estimators=100,      # 100 decision trees
    max_depth=8,           # Limit tree depth to prevent overfitting
    class_weight="balanced", # Handle imbalanced accepts/rejects
    random_state=42,       # Reproducible results
    n_jobs=-1              # Use all CPU cores
)
```

### 3. What data is used to train the ML model?
**Answer**: **RecommendationImpression** table records:
- Each time a food is recommended → 1 impression created
- User accepts (logs the food) → `added=True` (positive label)
- User ignores → `added=False` (negative label)
- Also stores: deficits at time of recommendation, rank, rule_score
Model learns which foods users prefer given their current nutritional state.

### 4. What are the 10 features used by the ML model?
**Answer**: (from `ml/predictor.py`)
1. Calorie deficit (normalized by 500)
2. Protein deficit (normalized by 100)
3. Fat deficit (normalized by 80)
4. Carb deficit (normalized by 200)
5. Food's calories (normalized by 500)
6. Food's protein (normalized by 30)
7. Food's fat (normalized by 20)
8. Food's carbs (normalized by 60)
9. Display rank (1-10, normalized by 10)
10. Rule-based score (normalized by 100)

### 5. When does the model retrain automatically?
**Answer**: Conditions in `ml/trainer.py`:
- **Data threshold**: ≥80 impressions AND ≥15 accepts
- **Time threshold**: At least 6 hours since last training
- Triggered by `check_and_retrain_in_background()` function
- Uses `last_train.txt` file to track last training timestamp

### 6. How is the hybrid scoring calculated?
**Answer**: 
```python
# Phase 1: When no ML model
score = rule_based_score  # 100% rules

# Phase 2: After training ≥80 impressions
ml_probability = model.predict_proba(features)[0, 1]
hybrid_score = (0.7 × rule_score) + (0.3 × ml_probability × 100)
```
This gives 70% weight to nutritional logic, 30% to learned user preferences.

### 7. What preprocessing is applied to the features?
**Answer**: **StandardScaler** from Scikit-Learn:
- Normalizes features to zero mean and unit variance
- Formula: `z = (x - mean) / std_dev`
- Prevents features with larger scales (like calories) from dominating
- Scaler is saved to disk (`scaler.pkl`) and loaded for inference

### 8. How do you evaluate the ML model's performance?
**Answer**: 
- **Metric**: ROC-AUC (Area Under Receiver Operating Characteristic curve)
- **Typical score**: ~0.75 AUC
- **Interpretation**: Model has 75% probability of ranking accepted food higher than rejected food
- Uses 80-20 train-test split with stratification to maintain class balance

### 9. What happens if the ML model fails to load?
**Answer**: **Graceful fallback** in `ml/predictor.py`:
```python
if MODEL is None or SCALER is None:
    return None  # Caller uses rule_score
```
System automatically falls back to 100% rule-based scoring. This ensures recommendations always work even if:
- Model file is corrupted
- Not enough training data yet
- Model training failed

### 10. How are the ML artifacts stored and loaded?
**Answer**: Using **Joblib** (Scikit-Learn's serialization):
- Training: `joblib.dump(model, MODEL_PATH)` saves to `/data/ml_artifacts/model.pkl`
- Loading: `joblib.load(MODEL_PATH)` on startup
- Persistent storage on Railway via mounted volume
- Also saves scaler and last training timestamp
- Model reloaded after each retraining to update in-memory predictions

---

**Note**: These questions cover the full project scope. Practice explaining the workflows, architecture diagrams, and formulas from the observation report for best preparation.
