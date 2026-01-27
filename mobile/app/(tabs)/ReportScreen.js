import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import API from "../../src/api";

export default function ReportScreen() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);

  const [recs, setRecs] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);

  // backend still uses static user 1
  const userId = 1;

  // -------- Fetch daily report --------
  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const rep = await API.getTodayReport(userId, "Adult Male");

      const rows = Object.entries(rep?.rda_comparison || {}).map(([k, v]) => ({
        key: k,
        intake: Number(v?.intake || 0).toFixed(2),
        rda: Number(v?.rda || 0).toFixed(2),
        percent: Math.round(v?.percent || 0),
      }));

      setItems(rows);

      // clear old recs when report refreshes
      setRecs([]);
    } catch (e) {
      console.warn("[Report] fetch error", e);
      Alert.alert("Report failed", String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, []);

  // refresh when tab gains focus
  useFocusEffect(
    useCallback(() => {
      fetchReport();
    }, [fetchReport])
  );

  // -------- Generate recommendations --------
  const fetchRecommendations = async () => {
    setRecsLoading(true);
    try {
      const logs = await API.getTodayLogs(userId);

      const payload = {
        food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
          food_id: l.food_id,
          quantity: l.quantity || 1,
        })),
        life_stage: "Adult Male",
      };

      const data = await API.generateRecommendations(payload);
      setRecs(data?.recommendations || []);
    } catch (e) {
      console.warn("[Report] recommendations error", e);
      Alert.alert("Recommendations failed", String(e?.message || e));
    } finally {
      setRecsLoading(false);
    }
  };

  // -------- Add recommended food to log --------
  const addRecommendedToLog = async (food) => {
    try {
      await API.addFoodLog({
        user_id: userId,
        food_id: food.food_id,
        quantity: 1,
        unit: "serving",
      });

      Alert.alert("Added", `${food.food_name || "Food"} added to log`);

      // refresh report after adding
      await fetchReport();
    } catch (e) {
      console.warn("add rec error", e);
      Alert.alert("Add failed", String(e?.message || e));
    }
  };

  if (loading) {
    return <ActivityIndicator style={{ flex: 1 }} size="large" />;
  }

  return (
    <SafeAreaView style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 22, fontWeight: "800", marginBottom: 10 }}>
        Daily Report
      </Text>

      <FlatList
        data={items}
        keyExtractor={(i) => i.key}
        renderItem={({ item }) => (
          <View
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
              paddingVertical: 8,
              borderBottomWidth: 0.5,
            }}
          >
            <Text style={{ fontWeight: "600" }}>
              {item.key.replace("_", " ")}
            </Text>
            <Text>
              {item.intake} / {item.rda} ({item.percent}%)
            </Text>
          </View>
        )}
        ListFooterComponent={
          <View style={{ marginTop: 20 }}>
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

            {recs.length > 0 && (
              <View style={{ marginTop: 18 }}>
                <Text
                  style={{
                    fontSize: 18,
                    fontWeight: "800",
                    marginBottom: 10,
                  }}
                >
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

                    <TouchableOpacity
                      onPress={() => addRecommendedToLog(r)}
                      style={{
                        marginTop: 10,
                        paddingVertical: 10,
                        borderRadius: 10,
                        backgroundColor: "#34A853",
                      }}
                    >
                      <Text
                        style={{
                          color: "white",
                          textAlign: "center",
                          fontWeight: "700",
                        }}
                      >
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
    </SafeAreaView>
  );
}
