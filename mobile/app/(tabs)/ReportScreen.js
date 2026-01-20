// mobile/app/ReportScreen.js
import React, { useState, useCallback } from "react";
import { View, Text, Button, StyleSheet, ActivityIndicator, FlatList, TouchableOpacity } from "react-native";
import { useFocusEffect } from "expo-router";
import { Alert } from "react-native";
import API from "../../src/api";

export default function ReportScreen() {
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);
  const [recs, setRecs] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const userId = 1;

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const rep = await API.getTodayReport(userId);
      console.log("[Report] rep:", rep);
      setReport(rep);
      setRecs([]);
    } catch (e) {
      console.warn("[Report] fetch error", e);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useFocusEffect(
    useCallback(() => {
      fetchReport();
    }, [fetchReport])
  );

  const fetchRecommendations = async () => {
    setRecsLoading(true);
    try {
      const logs = await API.getTodayLogs(userId);

      const payload = {
        food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
          food_id: l.food_id,
          quantity: l.quantity || 1,
        })),
        life_stage: lifeStage || "Adult Male",
      };

      const data = await API.generateRecommendations(payload);
      console.log("[Report] recommendations:", data);

      setRecs(data?.recommendations || []);
    } catch (e) {
      console.warn("[Report] recommendations error", e);
      Alert.alert("Recommendations failed", String(e?.message || e));
    } finally {
      setRecsLoading(false);
    }
  };

  const addRecommendedToLog = async (food) => {
    try {
      await API.addFoodLog({
        user_id: userId,
        food_id: food.food_id,
        quantity: 1,
        unit: "serving",
      });
      Alert.alert("Added", `${food.food_name || "Food"} added to log`);
      await fetchReport();
    } catch (e) {
      console.warn("add rec error", e);
      Alert.alert("Add failed", String(e?.message || e));
      await fetchReport();
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchRecs();
    }, [fetchRecs])
  );

  if (loading) return <ActivityIndicator style={{ flex: 1 }} size="large" />;

  const comparison = report?.rda_comparison || {};

  const items = Object.keys(comparison).map((k) => ({
    key: k,
    ...comparison[k]
  }));

  return (
    <View style={styles.container}>
      <Text style={styles.h1}>Daily Report</Text>

      <FlatList
        data={items}
        keyExtractor={(i) => i.key}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text style={styles.label}>{item.key.replace("_", " ")}</Text>
            <Text style={styles.value}>
              {item.intake} / {item.rda} ({item.percent ?? 0}%)
            </Text>
          </View>
        )}
        ListFooterComponent={
          <View style={{ marginTop: 20 }}>
            {/* ---------- Recommendations Button ---------- */}
            <TouchableOpacity
              onPress={fetchRecommendations}
              disabled={recsLoading}
              style={{
                padding: 14,
                borderRadius: 10,
                backgroundColor: recsLoading ? "#999" : "#1A73E8",
              }}
            >
              <Text
                style={{
                  color: "white",
                  textAlign: "center",
                  fontWeight: "700",
                }}
              >
                {recsLoading ? "Generating..." : "Get Recommendations"}
              </Text>
            </TouchableOpacity>

            {/* ---------- Recommendations List ---------- */}
            {recs.length > 0 && (
              <View style={{ marginTop: 18 }}>
                <Text style={{ fontSize: 18, fontWeight: "800", marginBottom: 10 }}>
                  Recommended Foods
                </Text>

                {recs.map((r, idx) => (
                  <View
                    key={`${r.food_id}-${idx}`}
                    style={{
                      padding: 12,
                      borderRadius: 12,
                      borderWidth: 1,
                      marginBottom: 10,
                    }}
                  >
                    <Text style={{ fontSize: 16, fontWeight: "700" }}>
                      {r.food_name || r.main_name || "Food"}
                    </Text>

                    {"score" in r && (
                      <Text style={{ marginTop: 4 }}>
                        Score: {Number(r.score || 0).toFixed(2)}
                      </Text>
                    )}

                    {/* ✅ Step 4.2: Add to Log button */}
                    <TouchableOpacity
                      onPress={() => addRecommendedToLog(r)}
                      style={{
                        marginTop: 10,
                        paddingVertical: 10,
                        borderRadius: 10,
                        backgroundColor: "#34A853",
                      }}
                    >
                      <Text style={{ color: "white", textAlign: "center", fontWeight: "700" }}>
                        Add to Log
                      </Text>
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            )}
          </View>
        }
      />
    </View>
  );

}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#fff" },
  h1: { fontSize: 20, fontWeight: "700", marginBottom: 12 },
  row: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#eee" },
  label: { fontSize: 16 },
  value: { fontWeight: "700" }
});