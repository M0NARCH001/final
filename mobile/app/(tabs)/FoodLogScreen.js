// mobile/app/FoodLogScreen.js
import React, { useState, useEffect, useCallback } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Keyboard,
} from "react-native";
import { useRouter, useSearchParams, useFocusEffect } from "expo-router";
import API from "../../src/api"; // <- make sure this file exists at mobile/app/src/api.js

export default function FoodLogScreen() {
  const router = useRouter();
  // if you navigate here with params, you can read them:
  // const params = useSearchParams(); // not required, only if you pass food_id directly
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [addingId, setAddingId] = useState(null);
  const [quantityMap, setQuantityMap] = useState({}); // per-food quantity if user wants >1

  const USER_ID = 1; // replace with real logged-in user id later

  // Fetch today's logs from backend
  const fetchTodayLogs = useCallback(async () => {
    console.log("[FoodLog] fetchTodayLogs start");
    setLoadingLogs(true);
    try {
      const res = await API.getTodayLogs(USER_ID);
      console.log("[FoodLog] today logs:", res);
      // backend returns list of FoodLogOut; add food_name if not present
      setLogs(Array.isArray(res) ? res : []);
    } catch (e) {
      console.warn("[FoodLog] fetchTodayLogs error", e);
      setLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  async function fetchLogs(setLogs, setLoading, setError) {
    try {
      setLoading(true);
      setError("");
      const data = await apiGet(`/food-logs?user_id=1`);
      setLogs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }
  // refresh logs when the screen gains focus
  useFocusEffect(
    React.useCallback(() => {
      fetchTodayLogs();
    }, [])
  );

  // Search foods
  async function doSearch() {
    if (!query || query.trim().length < 1) {
      setResults([]);
      return;
    }
    setLoadingSearch(true);
    try {
      Keyboard.dismiss();
      console.log("[FoodLog] search:", query);
      const data = await API.searchFoods(query, 30);
      const arr = Array.isArray(data) ? data : [];
      // default quantity 1
      setResults(arr);
      // initialize quantityMap for new results
      const qm = {};
      arr.forEach((it) => {
        qm[it.food_id] = 1;
      });
      setQuantityMap(qm);
      console.log("[FoodLog] search results:", arr.length);
    } catch (err) {
      console.error("[FoodLog] search error", err);
      Alert.alert("Search failed", String(err?.message || err));
    } finally {
      setLoadingSearch(false);
    }
  }

  // Add selected food to log
  async function addToLog(food) {
    const qty = Number(quantityMap[food.food_id] || 1);
    setAddingId(food.food_id);
    try {
      const payload = {
        user_id: USER_ID,           // IMPORTANT: include user_id so backend doesn't save NULL
        food_id: food.food_id,
        quantity: qty,
        unit: "serving"
      };
      console.log("[FoodLog] addToLog payload:", payload);
      const resp = await API.addFoodLog(payload);
      console.log("[FoodLog] add response:", resp);
      // optimistic update of local logs (backend has the authoritative copy)
      Alert.alert("Added", `${food.food_name} added to your log.`);
      // re-fetch today's logs from server to ensure data consistent
      await fetchTodayLogs();
      // navigate back so Home/Report screen regains focus and fetches
      // If you want to remain in the FoodLog screen, comment the next line
      router.back();
    } catch (err) {
      console.error("[FoodLog] addToLog error", err);
      Alert.alert("Add failed", String(err?.message || err));
    } finally {
      setAddingId(null);
    }
  }

  // Delete a log (optional convenience)
  async function deleteLog(log) {
    Alert.alert("Delete log", `Remove ${log.food_name}?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await API.deleteFoodLog(log.log_id);
            // optimistically remove from UI
            setLogs((s) => s.filter((x) => x.log_id !== log.log_id));
            await fetchTodayLogs();
          } catch (e) {
            console.warn("delete error", e);
            Alert.alert("Delete failed", String(e?.message || e));
          }
        }
      }
    ]);
  }

  // simple quantity + / - helpers
  function incQty(id) {
    setQuantityMap((m) => ({ ...m, [id]: Math.max(1, (m[id] || 1) + 1) }));
  }
  function decQty(id) {
    setQuantityMap((m) => ({ ...m, [id]: Math.max(1, (m[id] || 1) - 1) }));
  }
  function setQty(id, v) {
    const n = Math.max(1, Number(v) || 1);
    setQuantityMap((m) => ({ ...m, [id]: n }));
  }

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Add Food Log</Text>

      <View style={styles.searchRow}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search food (e.g., apple)"
          style={styles.input}
          onSubmitEditing={doSearch}
          returnKeyType="search"
        />
        <TouchableOpacity style={styles.searchBtn} onPress={doSearch} disabled={loadingSearch}>
          {loadingSearch ? <ActivityIndicator color="#fff" /> : <Text style={styles.searchBtnText}>Search</Text>}
        </TouchableOpacity>
      </View>

      <Text style={styles.sectionTitle}>Results</Text>
      {loadingSearch && <ActivityIndicator style={{ marginVertical: 8 }} />}
      <FlatList
        data={results}
        keyboardShouldPersistTaps="handled"
        keyExtractor={(it) => String(it.food_id)}
        ListEmptyComponent={() => <Text style={styles.placeholder}>No results. Try searching for "apple" or "tea".</Text>}
        renderItem={({ item }) => (
          <View style={styles.resultRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.resultName}>{item.food_name}</Text>
              <Text style={styles.resultMeta}>{Math.round(item.Calories_kcal || 0)} kcal • {item.Protein_g || 0}g protein</Text>
              <View style={styles.qtyRow}>
                <TouchableOpacity style={styles.qtyBtn} onPress={() => decQty(item.food_id)}><Text>-</Text></TouchableOpacity>
                <TextInput
                  style={styles.qtyInput}
                  keyboardType="numeric"
                  value={String(quantityMap[item.food_id] || 1)}
                  onChangeText={(t) => setQty(item.food_id, t)}
                />
                <TouchableOpacity style={styles.qtyBtn} onPress={() => incQty(item.food_id)}><Text>+</Text></TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.addBtn, addingId === item.food_id ? { opacity: 0.7 } : null]}
              onPress={() => addToLog(item)}
              disabled={addingId === item.food_id}
            >
              <Text style={styles.addBtnText}>{addingId === item.food_id ? "Adding..." : "Add"}</Text>
            </TouchableOpacity>
          </View>
        )}
      />

      <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Today's Logs</Text>
      {loadingLogs ? (
        <ActivityIndicator style={{ marginVertical: 12 }} />
      ) : (
        <FlatList
          data={logs}
          keyExtractor={(it) => String(it.log_id)}
          ListEmptyComponent={() => <Text style={styles.placeholder}>No logs for today.</Text>}
          renderItem={({ item }) => (
            <View style={styles.logRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.logName}>{item.food_name || `Food #${item.food_id}`}</Text>
                <Text style={styles.logMeta}>Qty: {item.quantity} {item.unit} • {item.logged_at ? new Date(item.logged_at).toLocaleTimeString() : ""}</Text>
              </View>
              <TouchableOpacity style={styles.deleteBtn} onPress={() => deleteLog(item)}>
                <Text style={{ color: "#fff" }}>Delete</Text>
              </TouchableOpacity>
            </View>
          )}
        />
      )}

      <TouchableOpacity
        style={styles.generateBtn}
        onPress={async () => {
          if (!logs.length) {
            Alert.alert("No logs", "Add at least one food to generate report");
            return;
          }
          try {
            const payload = { food_logs: logs.map(l => ({ food_id: l.food_id, quantity: l.quantity })), life_stage: "Adult Male" };
            const rep = await API.dailyReport(payload);
            console.log("[FoodLog] generated report:", rep);
            Alert.alert("Report created", "Open Reports tab to view details.");
            // optionally navigate to report screen:
            // router.push("/ReportScreen");
          } catch (e) {
            console.warn("[FoodLog] daily report error", e);
            Alert.alert("Report failed", String(e?.message || e));
          }
        }}
      >
        <Text style={styles.generateBtnText}>Generate Report</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 12, backgroundColor: "#fff" },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 8 },
  searchRow: { flexDirection: "row", marginBottom: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: "#ddd", padding: 8, borderRadius: 8, marginRight: 8 },
  searchBtn: { backgroundColor: "#1976D2", padding: 10, borderRadius: 8, justifyContent: "center", alignItems: "center" },
  searchBtnText: { color: "#fff", fontWeight: "700" },
  sectionTitle: { fontWeight: "700", marginTop: 6, marginBottom: 6 },
  placeholder: { color: "#666", paddingVertical: 8 },
  resultRow: { flexDirection: "row", padding: 10, borderBottomWidth: 1, borderColor: "#eee", alignItems: "center" },
  resultName: { fontWeight: "700", fontSize: 15 },
  resultMeta: { color: "#666", marginTop: 4 },
  addBtn: { backgroundColor: "#4CAF50", paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8, marginLeft: 12 },
  addBtnText: { color: "#fff", fontWeight: "700" },
  qtyRow: { flexDirection: "row", alignItems: "center", marginTop: 8 },
  qtyBtn: { width: 28, height: 28, borderRadius: 4, borderWidth: 1, borderColor: "#ddd", alignItems: "center", justifyContent: "center" },
  qtyInput: { width: 48, height: 32, borderWidth: 1, borderColor: "#ddd", marginHorizontal: 8, textAlign: "center", borderRadius: 6, padding: 4 },
  logRow: { flexDirection: "row", padding: 10, borderBottomWidth: 1, borderColor: "#eee", alignItems: "center" },
  logName: { fontWeight: "700" },
  logMeta: { color: "#666", marginTop: 4 },
  deleteBtn: { backgroundColor: "#E53935", padding: 8, borderRadius: 8 },
  generateBtn: { marginTop: 12, backgroundColor: "#1976D2", padding: 12, alignItems: "center", borderRadius: 8 },
  generateBtnText: { color: "#fff", fontWeight: "700" }
});