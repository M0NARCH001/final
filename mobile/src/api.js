// mobile/src/api.js
// NutriMate v2 unified API (no RDA, no life_stage)

import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";

const DEV_MACHINE_IP = "172.20.10.2"; // <-- your laptop IP
const PORT = 8000;

const ANDROID_EMULATOR_HOST = "10.0.2.2";
const OPENFOOD_BASE = "https://world.openfoodfacts.org/api/v0/product";

// Get API URL from expo-constants (works in EAS builds) or fall back to dev
const API_BASE = (() => {
  // Check expo-constants extra config first (for EAS builds)
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_API_URL;
  if (extraUrl) {
    console.log("[API] Using production URL from config:", extraUrl);
    return extraUrl;
  }
  // Fallback for local development
  if (Platform.OS === "android") {
    return `http://${ANDROID_EMULATOR_HOST}:${PORT}`;
  }
  return `http://${DEV_MACHINE_IP}:${PORT}`;
})();

// ---------------- CORE REQUEST ----------------
async function computeGoals(payload) {
  return request("/compute", {
    method: "POST",
    body: payload,
  });
}
async function request(path, opts = {}) {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  const cfg = {
    headers: { "Content-Type": "application/json" },
    ...opts,
  };

  if (cfg.body && typeof cfg.body !== "string") {
    cfg.body = JSON.stringify(cfg.body);
  }

  const res = await fetch(url, cfg);

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt}`);
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

// ---------------- SETUP / COMPUTE ----------------

async function computePlan(payload) {
  return request("/compute", {
    method: "POST",
    body: payload,
  });
}

// ---------------- FOODS ----------------

async function searchFoods(query, limit = 20) {
  if (!query) return [];
  return request(`/foods?query=${encodeURIComponent(query)}&limit=${limit}`);
}

// ---------------- LOGS ----------------

async function addFoodLog(payload) {
  return request("/food-logs", {
    method: "POST",
    body: payload,
  });
}

async function getTodayLogs(user_id = 1) {
  try {
    const res = await request(`/food-logs/today?user_id=${user_id}`, {
      method: "GET",
    });

    return Array.isArray(res) ? res : [];
  } catch (e) {
    const d = new Date().toISOString().slice(0, 10);
    const res = await request(`/food-logs?user_id=${user_id}&date=${d}`, {
      method: "GET",
    });

    return Array.isArray(res) ? res : [];
  }
}

async function deleteFoodLog(log_id) {
  return request(`/food-logs/${log_id}`, { method: "DELETE" });
}

// ---------------- HOME SUMMARY ----------------

async function getTodayReport(user_id = 1) {
  try {
    return await request(`/reports/today?user_id=${user_id}`);
  } catch {
    const logs = await getTodayLogs(user_id);

    const payload = {
      food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
        food_id: l.food_id,
        quantity: l.quantity || 1,
      })),
    };

    return request("/reports/daily", {
      method: "POST",
      body: payload,
    });
  }
}

// ---------------- DAILY SUMMARY WITH WARNINGS ----------------

async function getDailySummary(user_id, goals) {
  // goals should contain targets from computed goals
  const payload = {
    user_id,
    daily_calories: goals.daily_calories || 2000,
    protein_g: goals.protein_g || 100,
    fat_g: goals.fat_g || 60,
    carbs_g: goals.carbs_g || 250,
    fiber_g: goals.fiber_g || 25,
    sugar_limit_g: goals.sugar_limit_g || 50,
    sodium_limit_mg: goals.sodium_limit_mg || 2300,
    calcium_mg: goals.calcium_mg || 1000,
    iron_mg: goals.iron_mg || 18,
    vitaminC_mg: goals.vitaminC_mg || 90,
    folate_ug: goals.folate_ug || 400,
  };

  return request("/daily-summary", {
    method: "POST",
    body: payload,
  });
}

// ---------------- RECOMMENDATIONS ----------------

async function generateRecommendations(logs = []) {
  const planRaw = await AsyncStorage.getItem("nutrimate_goals");
  if (!planRaw) throw new Error("No goals stored - complete setup first");

  const plan = JSON.parse(planRaw);

  const payload = {
    food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
      food_id: l.food_id,
      quantity: l.quantity || 1,
    })),
    daily_calories: plan.daily_calories,
    protein_g: plan.protein_g,
    fat_g: plan.fat_g,
    carbs_g: plan.carbs_g,
  };

  return request("/recommendations/generate", {
    method: "POST",
    body: payload,
  });
}

// ---------------- BARCODE ----------------

async function fetchOpenFoodFacts(barcode) {
  const res = await fetch(`${OPENFOOD_BASE}/${barcode}.json`);
  if (!res.ok) throw new Error("OpenFoodFacts error");
  return res.json();
}

// ---------------- UTIL ----------------

function formatISODate(dt = new Date()) {
  return new Date(dt).toISOString();
}

// ---------------- EXPORTS ----------------

const API = {
  computePlan,

  searchFoods,

  computeGoals,

  addFoodLog,
  getTodayLogs,
  deleteFoodLog,

  getTodayReport,
  getDailySummary,

  generateRecommendations,

  fetchOpenFoodFacts,

  formatISODate,
};

export default API;

export {
  request,
  computePlan,
  searchFoods,
  addFoodLog,
  getTodayLogs,
  deleteFoodLog,
  getTodayReport,
  getDailySummary,
  generateRecommendations,
  fetchOpenFoodFacts,
  formatISODate,
  computeGoals,
};