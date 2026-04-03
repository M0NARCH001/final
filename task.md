4. Store `grams_logged` and `serving_unit_used` (use `serving_unit` if
provided, else `food.serving_unit`) in the `FoodLog` record.
5. In the daily summary calculation, use `grams_logged / 100.0` as the
multiplier for all nutrient values instead of the hardcoded `1.0`
(100g-based) multiplier.

### Task 3.4 — Serving Size Modal in FoodLogScreen
**File:** `app/(tabs)/FoodLogScreen.js`

After a user selects a food from search results, open a bottom-sheet modal
that contains:

| UI Element          | Behaviour                                                                               |
|---------------------|-----------------------------------------------------------------------------------------|
| Food name           | Display `food.name`                                                                     |
| Serving unit label  | Display `food.serving_unit` (e.g. `"1 piece"`, `"1 cup"`)                              |
| Quantity stepper    | `−` and `+` buttons, integer or 0.5 steps, minimum `0.5`, default `1`                  |
| "Enter exact grams" | Toggle switch; when ON, replaces stepper with a numeric `TextInput`                     |
| Nutrient preview    | Single line updated live: `Calories: X kcal · Protein: Yg · Carbs: Zg · Fat: Wg`      |
|                     | Computed client-side: `(food.calories * quantity * food.serving_weight_g) / 100`        |
| "Add to Log" button | Calls `POST /food-logs` with `{ food_id, quantity, serving_unit }` or `{ food_id, custom_grams }` |

- Do not close the modal on quantity change; only close on "Add to Log" or
explicit dismiss.
- Show a success toast after the log is added.

### Task 3.5 — Region Selection in Onboarding
**File:** `app/setup.js`

1. Add a new screen step after the **health conditions** screen.
2. Display a picker or scrollable list with options:
- `Tamil Nadu`, `Kerala`, `Karnataka`, `Maharashtra`, `Punjab`, `All India`
3. On selection:
- Save to `AsyncStorage` under key `"region"`.
- Include `region` in the user registration API call body.
4. Default selection: `"All India"` (pre-selected).
5. The step must be skippable (show a "Skip" link that defaults to
`"All India"`).

### Task 3.6 — Cuisine Badge in RecommendScreen
**File:** `app/(tabs)/RecommendScreen.js`

- On each food recommendation card, render a small badge showing
`item.cuisine_type`.
- Badge styling: pill shape, background `#E8F5E9`, text colour `#2E7D32`,
font size `11`, positioned bottom-right of the card.
- If `cuisine_type` is `null` or `"Generic"`, do not render the badge.

---

## Verification Checklist

Run these checks after all tasks are complete:

- [ ] `POST /users` — accepts `region`, stores it, returns user object with
   `region`
- [ ] `GET /foods?query=idli` — returns results with `region`, `cuisine_type`,
   `serving_unit`, `serving_weight_g` fields
- [ ] `POST /food-logs` — correctly computes `grams_logged` for both
   quantity-based and `custom_grams` paths
- [ ] `GET /food-logs/daily-summary` — nutrient totals scale with
   `grams_logged`
- [ ] `GET /recommendations` — regional foods rank higher for matching user
   region
- [ ] ML retraining completes without error with 12-feature vector
- [ ] Seeding script inserts 200+ Indian food items without duplicates
- [ ] Classification script updates `region`/`cuisine_type` on existing rows
- [ ] Expo app: serving size modal opens after food selection
- [ ] Expo app: region step appears in onboarding after health conditions
- [ ] Expo app: cuisine badge renders on recommendation cards

---

## Execution Order (Dependency Graph)
