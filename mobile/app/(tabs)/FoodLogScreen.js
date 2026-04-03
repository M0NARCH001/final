import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Switch,
  Keyboard,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useFocusEffect } from "@react-navigation/native";
import { useLocalSearchParams } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import API from "../../src/api";

export default function FoodLogScreen() {
  const { searchQuery } = useLocalSearchParams();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modal states
  const [selectedFood, setSelectedFood] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [exactGrams, setExactGrams] = useState(false);
  const [customGrams, setCustomGrams] = useState("");

  // Auto-fill and search when navigating from ScannerScreen
  useEffect(() => {
    if (searchQuery) {
      setQuery(searchQuery);
      // Trigger search after setting query
      searchWithQuery(searchQuery);
    }
  }, [searchQuery]);

  async function getUserId() {
    const uid = await AsyncStorage.getItem("user_id");
    if (!uid) {
      throw new Error("user_id not found - setup incomplete");
    }
    return parseInt(uid);
  }

  async function fetchLogs() {
    const uid = await getUserId();
    // eslint-disable-next-line import/no-named-as-default-member
    const l = await API.getTodayLogs(uid);
    setLogs(Array.isArray(l) ? l : []);
  }

  useFocusEffect(
    useCallback(() => {
      fetchLogs();
    }, [])
  );

  async function search() {
    if (!query) return;
    searchWithQuery(query);
  }

  async function searchWithQuery(q) {
    if (!q) return;
    setLoading(true);
    // eslint-disable-next-line import/no-named-as-default-member
    const r = await API.searchFoods(q);
    setResults(r || []);
    setLoading(false);
  }

  function openModal(food) {
    setSelectedFood(food);
    setQuantity(1);
    setExactGrams(false);
    setCustomGrams("");
    Keyboard.dismiss();
  }

  function closeModal() {
    setSelectedFood(null);
  }

  async function add() {
    if (!selectedFood) return;

    const uid = await getUserId();
    const payload = {
      user_id: uid,
      food_id: selectedFood.food_id,
      serving_unit: selectedFood.serving_unit || "serving"
    };

    if (exactGrams) {
      if (!customGrams || isNaN(customGrams)) {
        alert("Please enter a valid gram amount");
        return;
      }
      payload.custom_grams = parseFloat(customGrams);
      payload.quantity = 1; // Backend requires quantity, though we use custom_grams
    } else {
      payload.quantity = quantity;
    }

    try {
      // eslint-disable-next-line import/no-named-as-default-member
      await API.addFoodLog(payload);
      closeModal();
      setQuery("");
      setResults([]);
      fetchLogs();
      alert("Added to log!");
    } catch (e) {
      console.warn("Error adding food", e);
      alert("Failed to add food");
    }
  }

  async function remove(log) {
    // eslint-disable-next-line import/no-named-as-default-member
    await API.deleteFoodLog(log.log_id);
    fetchLogs();
  }

  const totalCalories = logs.reduce(
    (s, l) => s + (l.Calories_kcal || l.calories || 0),
    0
  );
  // Live search as user types
  React.useEffect(() => {
    if (query.length >= 2) {
      const timer = setTimeout(() => searchWithQuery(query), 400);
      return () => clearTimeout(timer);
    } else {
      setResults([]);
    }
  }, [query]);

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.h1}>Log Food</Text>

      <TextInput
        placeholder="Search food (e.g. idli, rice, chicken)"
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={search}
        style={styles.input}
        returnKeyType="search"
      />

      {loading && <ActivityIndicator style={{marginVertical: 8}} />}

      {/* Search Results */}
      {results.length > 0 && (
        <View style={styles.searchResultsContainer}>
          <Text style={styles.sectionLabel}>Search Results ({results.length})</Text>
          {results.map((item) => (
            <View key={item.food_id} style={styles.result}>
              <View style={styles.textWrap}>
                <Text style={styles.name}>{item.food_name}</Text>
                <Text style={styles.meta}>
                  {Math.round(item.Calories_kcal || 0)} kcal • P{" "}
                  {item.Protein_g || 0}g
                  {item.region && item.region !== "All India" ? ` • ${item.region}` : ""}
                </Text>
              </View>
              <TouchableOpacity onPress={() => openModal(item)}>
                <Text style={styles.add}>+ Add</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}

      {results.length === 0 && query.length >= 2 && !loading && (
        <Text style={styles.noResults}>No foods found for &quot;{query}&quot;</Text>
      )}

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

      {/* Serving Size Modal */}
      <Modal
        visible={!!selectedFood}
        transparent={true}
        animationType="slide"
        onRequestClose={closeModal}
      >
        {selectedFood && (() => {
          const weight = selectedFood.serving_weight_g || 100;
          const currentGrams = exactGrams ? parseFloat(customGrams || 0) : quantity * weight;
          const ratio = currentGrams / 100;
          
          const cal = (selectedFood.Calories_kcal || 0) * ratio;
          const pro = (selectedFood.Protein_g || 0) * ratio;
          const car = (selectedFood.Carbohydrates_g || 0) * ratio;
          const fat = (selectedFood.Fats_g || 0) * ratio;

          return (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>{selectedFood.food_name}</Text>
                  <TouchableOpacity onPress={closeModal}>
                    <Text style={styles.closeBtn}>✕</Text>
                  </TouchableOpacity>
                </View>

                {!exactGrams ? (
                  <View style={styles.stepperContainer}>
                    <Text style={styles.label}>
                      Quantity ({selectedFood.serving_unit || selectedFood.serving_size || "serving"})
                    </Text>
                    <View style={styles.stepperRow}>
                      <TouchableOpacity 
                        style={styles.stepperBtn} 
                        onPress={() => setQuantity(Math.max(0.5, quantity - 0.5))}
                      >
                        <Text style={styles.stepperBtnText}>−</Text>
                      </TouchableOpacity>
                      <Text style={styles.quantityText}>{quantity}</Text>
                      <TouchableOpacity 
                        style={styles.stepperBtn} 
                        onPress={() => setQuantity(quantity + 0.5)}
                      >
                        <Text style={styles.stepperBtnText}>+</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ) : (
                  <View style={styles.customGramsContainer}>
                    <Text style={styles.label}>Enter exact grams:</Text>
                    <TextInput
                      style={styles.gramInput}
                      keyboardType="numeric"
                      value={customGrams}
                      onChangeText={setCustomGrams}
                      placeholder="e.g. 150"
                      autoFocus
                    />
                  </View>
                )}

                <View style={styles.toggleRow}>
                  <Text style={{fontWeight: "500"}}>Enter exact grams?</Text>
                  <Switch
                    value={exactGrams}
                    onValueChange={(val) => {
                      setExactGrams(val);
                      if (val) setCustomGrams(Math.round(quantity * weight).toString());
                    }}
                  />
                </View>

                <View style={styles.previewBox}>
                  <Text style={styles.previewText}>
                    Calories: {Math.round(cal)} kcal • Protein: {Math.round(pro)}g • Carbs: {Math.round(car)}g • Fat: {Math.round(fat)}g
                  </Text>
                </View>

                <TouchableOpacity style={styles.submitBtn} onPress={add}>
                  <Text style={styles.submitBtnText}>Add to Log</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })()}
      </Modal>

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
  add: { color: "#1e6cf0", fontWeight: "600", fontSize: 15 },
  delete: { color: "red" },
  total: { marginTop: 12, fontWeight: "700" },
  searchResultsContainer: {
    maxHeight: 300,
    backgroundColor: "#fafafa",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#eee",
    paddingHorizontal: 12,
    marginBottom: 8,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#888",
    paddingTop: 8,
    paddingBottom: 4,
  },
  noResults: {
    textAlign: "center",
    color: "#999",
    paddingVertical: 12,
    fontStyle: "italic",
  },

  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  modalContent: {
    backgroundColor: "#fff",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    minHeight: 350,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  modalTitle: { fontSize: 20, fontWeight: "700" },
  closeBtn: { fontSize: 24, color: "#666", fontWeight: "300" },
  label: { fontSize: 16, fontWeight: "600", marginBottom: 12, color: "#333" },
  stepperContainer: { alignItems: "center", marginBottom: 20 },
  stepperRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  stepperBtn: {
    backgroundColor: "#f0f0f0",
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  stepperBtnText: { fontSize: 24, color: "#333", fontWeight: "500", marginTop: -2 },
  quantityText: { fontSize: 24, fontWeight: "700", width: 60, textAlign: "center" },
  customGramsContainer: { marginBottom: 20 },
  gramInput: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 12,
    fontSize: 18,
    textAlign: "center",
  },
  toggleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: "#eee",
  },
  previewBox: {
    backgroundColor: "#f8f9fa",
    padding: 12,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 20,
  },
  previewText: { fontSize: 14, color: "#555", fontWeight: "500" },
  submitBtn: {
    backgroundColor: "#1e6cf0",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
  },
  submitBtnText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});