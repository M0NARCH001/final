// mobile/src/openfood.js
const OF_API = "https://world.openfoodfacts.org/api/v0/product/";
const API_BASE = "http://10.218.59.24:8000"; // <-- REPLACE with your laptop IP

function safeNum(v) {
  if (v === undefined || v === null || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function mapNutriments(n) {
  // Common OF keys (per 100g)
  // energy-kcal_100g, proteins_100g, carbohydrates_100g, fat_100g,
  // sugars_100g, fiber_100g, sodium_100g (g), calcium_100g (mg?), iron_100g, vitamin-c_100g, folate_100g
  const out = {
    Calories_kcal: safeNum(n["energy-kcal_100g"] ?? n["energy_100g"]) ?? null,
    Protein_g: safeNum(n["proteins_100g"]) ?? null,
    Carbohydrates_g: safeNum(n["carbohydrates_100g"]) ?? null,
    Fats_g: safeNum(n["fat_100g"]) ?? null,
    FreeSugar_g: safeNum(n["sugars_100g"]) ?? null,
    Fibre_g: safeNum(n["fiber_100g"]) ?? null,
    Sodium_mg: (() => {
      const s = safeNum(n["sodium_100g"]);
      if (s === null) return null;
      // OF sodium often in g per 100g; convert to mg
      return s > 10 ? s : Math.round(s * 1000); // heuristic: if >10 assume mg already
    })(),
    Calcium_mg: (() => { const v = safeNum(n["calcium_100g"]); return v === null ? null : v; })(),
    Iron_mg: safeNum(n["iron_100g"]) ?? null,
    VitaminC_mg: safeNum(n["vitamin-c_100g"]) ?? null,
    Folate_ug: safeNum(n["folate_100g"]) ?? null
  };
  return out;
}

export async function getProductFromOpenFoodFacts(barcode) {
  const url = `${OF_API}${barcode}.json`;
  const r = await fetch(url);
  if (!r.ok) throw new Error("OpenFoodFacts lookup failed: " + r.status);
  const j = await r.json();
  if (j.status !== 1) return null;
  const p = j.product || {};
  const nutriments = p.nutriments || {};
  const per100 = mapNutriments(nutriments);

  // If serving size given, try to estimate per-serving
  let perServing = null;
  if (p.serving_size) {
    // serving_size strings vary ("30 g", "1 slice (25 g)"); extract number in grams if possible
    const m = p.serving_size.match(/([\d\.]+)\s*g/i);
    if (m) {
      const grams = Number(m[1]);
      perServing = {};
      Object.entries(per100).forEach(([k, v]) => {
        perServing[k] = v === null ? null : Number((v * grams) / 100.0);
      });
    }
  }

  return {
    barcode,
    product_name: p.product_name || p.generic_name || null,
    brands: p.brands || null,
    serving_size: p.serving_size || null,
    nutriments_raw: nutriments,
    nutrients_per_100g: per100,
    nutrients_per_serving: perServing
  };
}

// Query your backend for similar foods
export async function findLocalFoods(query, limit = 10) {
  const url = `${API_BASE}/foods?query=${encodeURIComponent(query)}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error("Local search failed: " + r.status);
  const j = await r.json();
  // backend returns array or {message:...}
  if (Array.isArray(j)) return j;
  if (j && j.message) return [];
  return j;
}

// Add to backend food logs
export async function addFoodLog({ food_id, quantity = 1, unit = "serving", user_id = null }) {
  const url = `${API_BASE}/food-logs`;
  const body = { user_id, food_id, quantity, unit };
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error("Add log failed: " + r.status + " " + txt);
  }
  return r.json();
}