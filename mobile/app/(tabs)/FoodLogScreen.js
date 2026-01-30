import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useFocusEffect } from "@react-navigation/native";
import API from "../../src/api";

export default function FoodLogScreen() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const USER_ID = 1;

  async function fetchLogs() {
    const l = await API.getTodayLogs(USER_ID);
    setLogs(Array.isArray(l) ? l : []);
  }

  useFocusEffect(
    useCallback(() => {
      fetchLogs();
    }, [])
  );

  async function search() {
    if (!query) return;
    setLoading(true);
    const r = await API.searchFoods(query);
    setResults(r || []);
    setLoading(false);
  }

  async function add(food) {
    await API.addFoodLog({
      user_id: USER_ID,
      food_id: food.food_id,
      quantity: 1,
      unit: "serving",
    });

    setQuery("");
    setResults([]);
    fetchLogs();
  }

  async function remove(log) {
    await API.deleteFoodLog(log.log_id);
    fetchLogs();
  }

  const totalCalories = logs.reduce(
    (s, l) => s + (l.Calories_kcal || l.calories || 0),
    0
  );

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.h1}>Log Food</Text>

      <TextInput
        placeholder="Search food"
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={search}
        style={styles.input}
      />

      {loading && <ActivityIndicator />}

      <FlatList
        data={results}
        keyExtractor={(i) => i.food_id.toString()}
        renderItem={({ item }) => (
          <View style={styles.result}>
            <View style={styles.textWrap}>
              <Text style={styles.name}>{item.food_name}</Text>
              <Text style={styles.meta}>
                {Math.round(item.Calories_kcal || 0)} kcal • P{" "}
                {item.Protein_g || 0}g
              </Text>
            </View>

            <TouchableOpacity onPress={() => add(item)}>
              <Text style={styles.add}>Add</Text>
            </TouchableOpacity>
          </View>
        )}
      />

      <Text style={styles.h2}>Today</Text>

      <FlatList
        data={logs}
        keyExtractor={(i) => i.log_id.toString()}
        renderItem={({ item }) => (
          <View style={styles.log}>
            <View style={styles.textWrap}>
              <Text>{item.food_name}</Text>
              <Text>{Math.round(item.Calories_kcal || 0)} kcal</Text>
            </View>

            <TouchableOpacity onPress={() => remove(item)}>
              <Text style={styles.delete}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
      />

      <Text style={styles.total}>Total Today: {Math.round(totalCalories)} kcal</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  h1: { fontSize: 22, fontWeight: "700" },
  h2: { fontSize: 18, fontWeight: "600", marginTop: 16 },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    padding: 12,
    marginVertical: 10,
  },
  result: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderColor: "#eee",
  },
  log: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderColor: "#eee",
  },
  textWrap: { flex: 1, paddingRight: 10 },
  name: { fontWeight: "600" },
  meta: { color: "#666" },
  add: { color: "#1e6cf0", fontWeight: "600" },
  delete: { color: "red" },
  total: { marginTop: 12, fontWeight: "700" },
});