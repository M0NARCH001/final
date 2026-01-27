// mobile/src/api.js
// Unified API wrapper for NutriMate backend + OpenFoodFacts (barcode fallback)
// Works for Android emulator, physical phone, and iOS simulator.

import { Platform } from "react-native";

const DEV_MACHINE_IP = "192.168.29.117";
const PORT = 8000;

// Android emulator must use 10.0.2.2 to reach host machine
const ANDROID_EMULATOR_HOST = "10.0.2.2";
const OPENFOOD_BASE = "https://world.openfoodfacts.org/api/v0/product";

const API_BASE = (() => {
  // ✅ Android emulator
  if (Platform.OS === "android") {
    // In most cases Expo on Android emulator uses this.
    return `http://${ANDROID_EMULATOR_HOST}:${PORT}`;
  }
  // ✅ iOS simulator / physical iPhone on LAN
  return `http://${DEV_MACHINE_IP}:${PORT}`;
})();

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
    throw new Error(`HTTP ${res.status} ${res.statusText} - ${txt}`);
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

// ------------------ API METHODS ------------------
async function searchFoods(query, limit = 20) {
  if (!query) return [];
  const q = encodeURIComponent(query);
  const url = `/foods?query=${q}&limit=${limit}`;
  const data = await request(url, { method: "GET" });
  return Array.isArray(data) ? data : [];
}

async function addFoodLog(payload = { user_id: null, food_id: 0, quantity: 1, unit: "serving" }) {
  return request(`/food-logs`, { method: "POST", body: payload });
}

async function getTodayLogs(user_id = 1) {
  // try /food-logs/today first
  try {
    return await request(`/food-logs/today?user_id=${user_id}`, { method: "GET" });
  } catch (e) {
    // fallback: query by date (YYYY-MM-DD)
    const d = new Date().toISOString().slice(0, 10);
    return request(`/food-logs?user_id=${user_id}&date=${d}`, { method: "GET" });
  }
}

async function deleteFoodLog(log_id) {
  return request(`/food-logs/${log_id}`, { method: "DELETE" });
}

async function dailyReport(payload = { food_logs: [], life_stage: "Adult Male" }) {
  return request(`/reports/daily`, { method: "POST", body: payload });
}

async function getTodayReport(user_id = 1, life_stage = "Adult Male") {
  try {
    // If backend has a direct endpoint
    return await request(`/reports/today?user_id=${user_id}`, { method: "GET" });
  } catch (e) {
    // fallback: fetch today's logs then compute via /reports/daily
    const logs = await getTodayLogs(user_id);
    const payload = {
      food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
        food_id: l.food_id,
        quantity: l.quantity || 1,
      })),
      life_stage,
    };
    return dailyReport(payload);
  }
}

async function generateRecommendations(payload = { food_logs: [], life_stage: "Adult Male" }) {
  return request(`/recommendations/generate`, { method: "POST", body: payload });
}

// ------------------ Scanner / OpenFoodFacts ------------------
async function fetchOpenFoodFacts(barcode) {
  const url = `${OPENFOOD_BASE}/${encodeURIComponent(barcode)}.json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`OpenFoodFacts error ${res.status}`);
  return res.json();
}

// ------------------ Utility ------------------
function formatISODate(dt = new Date()) {
  return new Date(dt).toISOString();
}

// ------------------ Exports ------------------
const API = {
  // foods
  searchFoods,

  // logs
  addFoodLog,
  getTodayLogs,
  deleteFoodLog,

  // reports
  dailyReport,
  getTodayReport,

  // recommendations
  generateRecommendations,

  // scanner
  fetchOpenFoodFacts,

  // utils
  formatISODate,
};

export default API;
export {
  request,
  searchFoods,
  addFoodLog,
  getTodayLogs,
  deleteFoodLog,
  dailyReport,
  getTodayReport,
  generateRecommendations,
  fetchOpenFoodFacts,
  formatISODate,
};
