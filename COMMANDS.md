# NutriMate v2 — Commands & Live API Reference

## Run Backend (Local)

```bash
cd backend
pip install -r requirements.txt      # first time only
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

---

## Run Mobile App (Local)

```bash
cd mobile
npm install                           # first time only
npx expo start --lan                  # scan QR with Expo Go
npx expo start --tunnel               # if LAN doesn't work
```

For physical device testing with Expo Go, make sure the phone and laptop are on the same Wi-Fi.  
Update `DEV_MACHINE_IP` in `mobile/src/api.js` to your laptop's local IP.

---

## Build APK (EAS)

```bash
cd mobile
npx eas-cli build --profile preview --platform android --non-interactive
```

Latest APK (commit 005f917):  
https://expo.dev/accounts/venkat1202/projects/mobile/builds/e8665902-9dc4-42fe-9bbe-e88e86e2f9b7

---

## Production

**Backend (Railway):** https://final-production-2323.up.railway.app  
**Mobile:** EAS internal distribution (APK link above)

Railway auto-deploys on every push to `main`. DB migrations run automatically on startup.

---

## Live API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user with full profile + password |
| POST | `/auth/login` | Login with username + password, returns full profile |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/{user_id}` | Get user by ID |
| PUT | `/users/{user_id}` | Update user profile |
| POST | `/users/check-username` | Check if username is available |
| POST | `/users/register` | Legacy register (no password) |
| GET | `/users/by-username/{username}` | Get user by username |
| GET | `/users/admin/list` | All users — admin view (JSON) |
| GET | `/users/admin/export.csv` | Download all users as CSV |

### Foods
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/foods/search?q=&limit=` | Search foods by name |
| GET | `/foods/{food_id}` | Get food details by ID |
| POST | `/foods` | Add new food item |

### Food Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/food-logs` | Log a food item for a user |
| GET | `/food-logs/today/{user_id}` | Get today's food logs for user |
| GET | `/food-logs/{user_id}` | Get all logs for user |
| DELETE | `/food-logs/{log_id}` | Delete a food log entry |

### Recommendations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/recommendations/generate` | Generate personalised food recommendations |
| POST | `/impressions/batch` | Log which recommendations were shown (ML training data) |
| POST | `/impressions/{impression_id}/add` | Mark a recommendation as added by user |

### Goals & Nutrition
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/compute` | Compute BMR/TDEE and daily macro targets |
| POST | `/goals/compute` | Same as /compute (alias) |
| POST | `/report` | Generate daily nutrition report vs targets |

### Utility
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — returns `{"ok": true}` |
| GET | `/migrate-db` | Run DB migrations (idempotent, auto-runs on startup) |
| GET | `/docs` | Swagger UI — interactive API docs |
| GET | `/openapi.json` | OpenAPI schema |
