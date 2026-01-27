// mobile/app/index.js
import React, { useState, useCallback } from "react";
import { View, Text, StyleSheet, FlatList, ActivityIndicator } from "react-native";
import { useFocusEffect } from "@react-navigation/native"; // this works with expo-router's underlying nav
import { useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import API from "../../src/api"; // adjust if your api path is different

function ProgressBar({ label, value, target }) {
  const pct = target && target > 0 ? Math.min(100, Math.round((value / target) * 100)) : 0;
  return (
    <View style={{ marginVertical: 8 }}>
      <View style={styles.row}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>{Math.round(value)} / {Math.round(target || 0)} ({pct}%)</Text>
      </View>
      <View style={styles.barBg}>
        <View style={[styles.barFill, { width: `${pct}%` }]} />
      </View>
    </View>
  );
}

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);
  const [logs, setLogs] = useState([]);

  const uid = 1; // replace with actual logged-in user's id when available

  const fetchData = async () => {
    console.log("[Home] fetchData start", new Date().toISOString());
    setLoading(true);
    try {
      const rep = await API.getTodayReport(uid);
      console.log("[Home] report:", rep);
      const l = await API.getTodayLogs(uid);
      console.log("[Home] logs:", l);
      setReport(rep);
      setLogs(l);
    } catch (e) {
      console.warn("[Home] fetch error", e);
    } finally {
      setLoading(false);
    }
  };

  // runs when screen comes into focus (tab switch / back)
  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [])
  );

  if (loading) return <ActivityIndicator style={{ flex: 1 }} size="large" />;

  const totals = report?.totals || {};
  const comp = report?.rda_comparison || {};

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.h1}>Today's Summary</Text>
      <View style={styles.card}>
        <Text style={styles.big}>{Math.round(totals.Calories_kcal || 0)} kcal</Text>
        <ProgressBar label="Protein (g)" value={totals.Protein_g || 0} target={comp?.Protein_g?.rda || 0} />
        <ProgressBar label="Carbs (g)" value={totals.Carbohydrates_g || 0} target={comp?.Carbohydrates_g?.rda || 0} />
        <ProgressBar label="Fats (g)" value={totals.Fats_g || 0} target={comp?.Fats_g?.rda || 0} />
      </View>

      <Text style={[styles.h2, { marginTop: 12 }]}>Today's Logs</Text>
      <FlatList
        data={logs}
        keyExtractor={(item) => item.log_id?.toString() || Math.random().toString()}
        renderItem={({ item }) => (
          <View style={styles.logRow}>
            <View>
              <Text style={styles.logName}>{item.food_name || "Unknown"}</Text>
              <Text style={styles.logMeta}>{item.quantity} {item.unit || "serving"} • {item.Calories_kcal || item.calories || 0} kcal</Text>
            </View>
          </View>
        )}
        ListEmptyComponent={() => <Text style={{ padding: 16 }}>No logs for today.</Text>}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#fff" },
  h1: { fontSize: 20, fontWeight: "700", marginBottom: 12 },
  card: { backgroundColor: "#f6f7fb", padding: 12, borderRadius: 12 },
  big: { fontSize: 28, fontWeight: "700", marginBottom: 8 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  label: { fontSize: 14 },
  value: { fontSize: 14, fontWeight: "600" },
  barBg: { height: 10, backgroundColor: "#e6e6e6", borderRadius: 6, marginTop: 6, overflow: "hidden" },
  barFill: { height: "100%", backgroundColor: "#34b889" },
  h2: { fontSize: 18, fontWeight: "600" },
  logRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: "#f0f0f0" },
  logName: { fontSize: 16, fontWeight: "600" },
  logMeta: { color: "#666", fontSize: 13 }
});