# NutriMate v2: Follow-Up/Deep-Dive Questions

These are **harder follow-up questions** that professors typically ask after hearing your initial answers. They test deeper understanding and problem-solving ability.

---

## Backend Follow-Up Questions

### From: "We use FastAPI framework"
**Q1**: Why FastAPI over Flask or Django? What specific features made you choose it?
**Answer**: FastAPI provides:
- **Automatic API documentation** (Swagger/OpenAPI) - saves development time
- **Type validation** with Pydantic - catches errors before runtime
- **Async support** - can handle concurrent requests efficiently
- **Faster performance** than Flask (uses Starlette/Uvicorn ASGI)
- Django is overkill for REST APIs (built for full-stack web apps)

**Q2**: What is ASGI and how is it different from WSGI?
**Answer**: 
- **WSGI** (Web Server Gateway Interface): Synchronous, one request at a time
- **ASGI** (Async Server Gateway Interface): Supports async/await, handles concurrent connections
- FastAPI uses **Uvicorn** (ASGI server) which enables websockets and handles I/O-bound tasks better

### From: "We use SQLite database"
**Q3**: What are the limitations of SQLite? When would you migrate to PostgreSQL?
**Answer**: SQLite limitations:
- **No concurrent writes** - only one write transaction at a time
- **Type system** is flexible (can store wrong data types)
- **No built-in user management** or role-based access
- Migrate to PostgreSQL when:
  - Multiple users writing simultaneously
  - Need advanced features (JSON queries, full-text search)
  - Database size > 1GB (SQLite handles up to ~140TB but performance degrades)

**Q4**: How do you handle database migrations when schema changes?
**Answer**: Currently using SQLAlchemy's `create_all()` which only creates missing tables. For production:
- Use **Alembic** (SQLAlchemy's migration tool)
- Generate migration scripts: `alembic revision --autogenerate`
- Apply migrations: `alembic upgrade head`
- Our `/migrate-db` endpoint is a temporary solution for adding columns

### From: "BMR calculated using Mifflin-St Jeor equation"
**Q5**: Why not use Harris-Benedict equation? What's the difference?
**Answer**: 
- **Mifflin-St Jeor** (1990): More accurate for modern populations, especially overweight individuals
- **Harris-Benedict** (1919): Older formula, tends to overestimate for sedentary people
- Mifflin-St Jeor error margin: ±10%, Harris-Benedict: ±15%

**Q6**: Your activity multipliers are fixed (1.2, 1.55, 1.75). How would you make this more accurate?
**Answer**: Could improve by:
- Integrating **step counter** (Google Fit/Apple Health API) for actual activity
- Using PAL (Physical Activity Level) formula based on hours of activity per week
- Machine learning to learn user's actual TDEE from weight change trends

### From: "Hybrid scoring: 70% rules + 30% ML"
**Q7**: Why 70-30 split specifically? Did you experiment with other ratios?
**Answer**: 
- **70% rules ensures** nutritional correctness (can't recommend junk food even if user likes it)
- **30% ML** adds personalization without overriding health logic
- Alternative: Could make ratio dynamic based on model confidence (AUC score)
- If AUC > 0.8 → increase ML weight to 50%

**Q8**: What if the ML model recommends unhealthy foods the user previously accepted?
**Answer**: **Rules act as safety guardrails**:
- Junk food penalty (-80 points) in rules
- Even if ML predicts 100% probability, hybrid score = 0.7×(-80) + 0.3×100 = -26 (still negative)
- Condition-based penalties (diabetes gets -30 for high carbs) apply BEFORE hybrid calculation

### From: "Username-based authentication without passwords"
**Q9**: This is a major security flaw. How would you implement proper authentication?
**Answer**: Production approach:
1. **Add password field** to User table with bcrypt hashing
2. Implement **JWT tokens**:
   - Login returns access token (short-lived, 15min) + refresh token (long-lived, 7 days)
   - Mobile stores tokens in secure storage (not AsyncStorage)
3. Add middleware to verify JWT on protected routes
4. Alternative: **OAuth 2.0** (Google/Apple Sign-In)

**Q10**: How do you prevent SQL injection attacks?
**Answer**: 
- **SQLAlchemy ORM** automatically parameterizes queries
- Never use raw SQL strings with f-strings
- Example (safe): `db.query(User).filter(User.username == username)`
- Example (unsafe): `db.execute(f"SELECT * FROM user WHERE username='{username}'")`

---

## Mobile/Expo Follow-Up Questions

### From: "Using AsyncStorage for local data"
**Q11**: AsyncStorage is unencrypted. What if user data is sensitive?
**Answer**: For sensitive data, use:
- **Expo SecureStore**: Uses iOS Keychain/Android Keystore (encrypted)
- Encrypt before storing: `expo-crypto` or `react-native-aes-crypto`
- Only store non-sensitive data in AsyncStorage (goals, preferences)

**Q12**: What happens if AsyncStorage is cleared (e.g., app cache cleared)?
**Answer**: User loses:
- Local session (`user_id`) → forced to re-login
- Cached goals → need to re-fetch from backend
**Solution**: 
- Add backend endpoint `/users/{user_id}/goals` to restore data
- Implement auto-sync on app launch

### From: "Using Expo Router for navigation"
**Q13**: How is Expo Router different from React Navigation?
**Answer**: 
- **Expo Router**: File-based routing (like Next.js) - folder structure defines routes
- **React Navigation**: Programmatic routing - define routes in code
- Expo Router benefits:
  - Easier to understand (file = route)
  - Built-in deep linking
  - Type-safe with TypeScript

**Q14**: How do you handle deep linking (e.g., opening app from barcode URL)?
**Answer**: Expo Router auto-handles:
- URL scheme: `nutrimate://scan?barcode=123456`
- Maps to `app/scan.js` with param `useLocalSearchParams()`
- Configure in `app.json`: `"scheme": "nutrimate"`

### From: "FlatList for rendering food logs"
**Q15**: What's the advantage of FlatList over ScrollView with .map()?
**Answer**: 
- **FlatList**: Virtualizes items (only renders visible items + buffer)
- **ScrollView**: Renders ALL items upfront
- Performance: FlatList handles 1000s of items smoothly
- Memory: FlatList uses ~constant memory, ScrollView grows with data

**Q16**: How would you implement pagination for search results?
**Answer**: 
- Backend: Add `offset` and `limit` params to `/foods` endpoint
- Mobile: Use FlatList's `onEndReached` callback
- Load more when user scrolls to bottom:
```javascript
onEndReached={() => {
  if (!loading) fetchMoreResults();
}}
```

### From: "Expo Camera for barcode scanning"
**Q17**: What barcode formats does expo-camera support?
**Answer**: 
- Common: **EAN-13** (groceries), **UPC-A** (US products), **QR codes**
- Configure in Camera component: `barCodeTypes={[BarCodeScanner.Constants.BarCodeType.ean13]}`
- OpenFoodFacts primarily uses EAN-13 and UPC-A

**Q18**: How do you handle camera permissions?
**Answer**: 
```javascript
const [permission, requestPermission] = Camera.useCameraPermissions();
if (!permission?.granted) {
  await requestPermission();
}
```
- iOS: Add description to `app.json`: `"NSCameraUsageDescription": "Scan barcodes"`
- Android: Auto-adds to manifest

### From: "OpenFoodFacts API integration"
**Q19**: What if OpenFoodFacts API is down or rate-limited?
**Answer**: Implement fallbacks:
- **Timeout**: 5 second timeout on API call
- **Retry with exponential backoff**: 3 attempts with 2s, 4s, 8s delays
- **Fallback to manual entry**: Show form to enter nutrition manually
- **Caching**: Store successful lookups in local DB

**Q20**: How do you handle products with missing nutritional data on OpenFoodFacts?
**Answer**: 
- Check if `nutriments` fields are null: `nutrition.protein_100g ?? null`
- Display warning: "Some nutrition data missing"
- Allow user to edit/complete data before logging
- Use estimation: If calories missing but macros present, calculate from 4-4-9 rule

---

## ML Engine Follow-Up Questions

### From: "Using RandomForest with 100 trees"
**Q21**: Why not use neural networks instead of RandomForest?
**Answer**: RandomForest is better for this use case:
- **Small dataset** (80-1000 impressions) - neural nets need 10,000+
- **Interpretable** - can see feature importance
- **No GPU required** - trains in seconds on CPU
- **Robust to overfitting** - ensemble method
- Neural nets would be overkill and likely overfit

**Q22**: How did you choose max_depth=8? Did you tune hyperparameters?
**Answer**: 
- **Max_depth=8** prevents overfitting on small dataset
- Could implement **GridSearchCV** to optimize:
```python
from sklearn.model_selection import GridSearchCV
params = {'max_depth': [6, 8, 10], 'n_estimators': [50, 100, 150]}
grid = GridSearchCV(RandomForestClassifier(), params, cv=3)
```
- Currently using empirical defaults suitable for ~100-500 samples

### From: "Model retrains every 6 hours if conditions met"
**Q23**: Won't frequent retraining cause model instability?
**Answer**: Safeguards in place:
- **Minimum 6 hour cooldown** prevents constant retraining
- **Minimum 80 impressions** ensures stable distribution
- **Train-test split** uses stratification and random_state=42 for consistency
- Could add: **Model versioning** - keep previous model if new AUC < old AUC - 0.05

**Q24**: How do you handle the cold start problem (new users with 0 impressions)?
**Answer**: **Phased rollout**:
- **Phase 0** (<80 impressions): 100% rule-based for ALL users
- **Phase 1** (≥80 impressions): Shared global model trained on all users
- **Phase 2** (future): Per-user models or user clustering

### From: "Features are normalized (e.g., calories/500)"
**Q25**: Why normalize manually instead of letting StandardScaler handle it?
**Answer**: 
- **Double normalization**: Manual scaling (0-2 range) THEN StandardScaler (z-score)
- Manual scaling brings features to similar magnitude BEFORE z-score
- Prevents extreme outliers (e.g., 5000 calorie foods) from skewing scaler
- Could simplify by using only StandardScaler, but current approach is more robust

**Q26**: What if a food has calories > 500 (your normalization divisor)?
**Answer**: 
- Feature goes > 1.0 (e.g., 800 calories → 1.6)
- **This is okay** - StandardScaler handles any range
- Normalization divisors (500, 100, etc.) are based on typical food values
- Alternative: Use **MinMaxScaler** to force 0-1 range

### From: "AUC score of 0.75"
**Q27**: Is 0.75 AUC good? What would indicate a failing model?
**Answer**: 
- **0.5**: Random guessing (model is useless)
- **0.7-0.8**: Good performance (our range)
- **0.8-0.9**: Excellent (difficult with small datasets)
- **> 0.9**: Suspiciously high (might be overfitting)
- Would retrain if AUC < 0.65

**Q28**: How do you handle class imbalance (more rejects than accepts)?
**Answer**: 
- **`class_weight="balanced"`** in RandomForest automatically adjusts for imbalance
- Formula: `weight_class = n_samples / (n_classes × n_class_samples)`
- Minority class (accepts) gets higher weight during training
- Alternative: **SMOTE** (Synthetic Minority Oversampling) but overkill for this

### From: "Model saved with Joblib"
**Q29**: Why Joblib instead of pickle?
**Answer**: 
- **Joblib optimized for numpy arrays** (faster for scikit-learn models)
- **Compression**: `joblib.dump(model, compress=3)` saves space
- **Security**: Joblib is safer than pickle (less arbitrary code execution risk)
- Both work, but Joblib is scikit-learn's recommended serialization

**Q30**: How would you deploy multiple model versions for A/B testing?
**Answer**: 
- Save models with version numbers: `model_v1.pkl`, `model_v2.pkl`
- Add `model_version` field to User table
- Route 50% users to v1, 50% to v2
- Compare acceptance rates in RecommendationImpression table
- Promote winning model to 100% after 1 week

---

**Study Tip**: Practice explaining these with diagrams on a whiteboard. Draw the data flow, formula derivations, and architecture for best retention!
