// mobile/src/api.js
// NutriMate v2 unified API (no RDA, no life_stage)

import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

const DEV_MACHINE_IP = "192.168.29.117"; // <-- your laptop IP
const PORT = 8000;

const ANDROID_EMULATOR_HOST = "10.0.2.2";
const OPENFOOD_BASE = "https://world.openfoodfacts.org/api/v0/product";

const API_BASE = (() => {
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

// ---------------- RECOMMENDATIONS ----------------

async function generateRecommendations(logs = []) {
  const planRaw = await AsyncStorage.getItem("nutrimate_plan");
  if (!planRaw) throw new Error("No plan stored");

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
  generateRecommendations,
  fetchOpenFoodFacts,
  formatISODate,
  computeGoals,
};