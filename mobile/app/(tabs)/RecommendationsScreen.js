import React, { useState } from "react";
import {
    View,
    Text,
    StyleSheet,
    FlatList,
    ActivityIndicator,
    TouchableOpacity,
    Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import API from "../../src/api";
import { useFocusEffect } from "@react-navigation/native";

/* ---------- Nutrient Badge ---------- */
function NutrientBadge({ label, value, unit, color }) {
    return (
        <View style={[styles.badge, { backgroundColor: color + "20", borderColor: color }]}>
            <Text style={[styles.badgeText, { color: color }]}>
                {label}: {Math.round(value)}{unit}
            </Text>
        </View>
    );
}

export default function RecommendationsScreen() {
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [items, setItems] = useState([]);

    useFocusEffect(
        React.useCallback(() => {
            load();
        }, [])
    );

    async function load() {
        try {
            const profile = await AsyncStorage.getItem("nutrimate_profile");
            const goals = await AsyncStorage.getItem("nutrimate_goals");

            if (!profile || !goals) {
                Alert.alert("Setup missing", "Please complete setup first.");
                router.replace("/setup");
                return;
            }

            const plan = JSON.parse(goals);
            const profileData = JSON.parse(profile);
            const uidStr = await AsyncStorage.getItem("user_id");
            const uid = uidStr ? parseInt(uidStr) : 1;

            const logs = await API.getTodayLogs(uid) || [];

            const payload = {
                food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
                    food_id: l.food_id,
                    quantity: l.quantity || 1,
                })),
                daily_calories: plan.daily_calories,
                protein_g: plan.protein_g,
                fat_g: plan.fat_g,
                carbs_g: plan.carbs_g,
                // Micronutrient targets
                fiber_g: plan.fiber_g || 25,
                sugar_limit_g: plan.sugar_limit_g || 50,
                sodium_limit_mg: plan.sodium_limit_mg || 2300,
                calcium_mg: plan.calcium_mg || 1000,
                iron_mg: plan.iron_mg || 18,
                vitaminC_mg: plan.vitaminC_mg || 90,
                folate_ug: plan.folate_ug || 400,
                // Health conditions
                has_diabetes: profileData.has_diabetes || false,
                has_hypertension: profileData.has_hypertension || false,
                has_pcos: profileData.has_pcos || false,
                muscle_gain_focus: profileData.muscle_gain_focus || false,
                heart_health_focus: profileData.heart_health_focus || false,
            };

            const recs = await API.generateRecommendations(payload);
            setItems(Array.isArray(recs?.recommendations) ? recs.recommendations : []);
        } catch (e) {
            console.warn(e);
            Alert.alert("Error", "Failed to load recommendations");
        } finally {
            setLoading(false);
        }
    }

    async function addFood(food) {
        const uidStr = await AsyncStorage.getItem("user_id");
        const uid = uidStr ? parseInt(uidStr) : 1;

        await API.addFoodLog({
            user_id: uid,
            food_id: food.food_id,
            quantity: 1,
            unit: "serving",
        });
        await load();
        Alert.alert("Added", food.food_name);
    }

    if (loading)
        return <ActivityIndicator style={{ flex: 1 }} size="large" />;

    return (
        <SafeAreaView style={styles.container}>
            <Text style={styles.h1}>Recommended Foods</Text>

            <FlatList
                data={items}
                keyExtractor={(i, idx) => idx.toString()}
                ListEmptyComponent={() => (
                    <Text style={{ padding: 20, color: "#666" }}>No recommendations yet.</Text>
                )}
                renderItem={({ item }) => (
                    <View style={styles.card}>
                        <View style={styles.cardHeader}>
                            <Text style={styles.name}>{item.food_name}</Text>
                            {item.suggested_portion_g && (
                                <Text style={styles.portion}>
                                    ~{item.suggested_portion_g}g
                                </Text>
                            )}
                        </View>

                        {/* Reason for recommendation */}
                        {item.reason && (
                            <Text style={styles.reason}>✨ {item.reason}</Text>
                        )}

                        {/* Nutrient badges */}
                        {item.nutrients && (
                            <View style={styles.badgeRow}>
                                {item.nutrients.Protein_g > 10 && (
                                    <NutrientBadge
                                        label="Protein"
                                        value={item.nutrients.Protein_g}
                                        unit="g"
                                        color="#22c55e"
                                    />
                                )}
                                {item.nutrients.Fibre_g > 3 && (
                                    <NutrientBadge
                                        label="Fiber"
                                        value={item.nutrients.Fibre_g}
                                        unit="g"
                                        color="#10b981"
                                    />
                                )}
                                {item.nutrients.FreeSugar_g < 5 && (
                                    <NutrientBadge
                                        label="Low Sugar"
                                        value={item.nutrients.FreeSugar_g}
                                        unit="g"
                                        color="#06b6d4"
                                    />
                                )}
                            </View>
                        )}

                        <View style={styles.cardFooter}>
                            <Text style={styles.calories}>
                                {Math.round(item.nutrients?.Calories_kcal || 0)} kcal
                            </Text>
                            <TouchableOpacity
                                style={styles.btn}
                                onPress={() => addFood(item)}
                            >
                                <Text style={{ color: "#fff", fontWeight: "600" }}>+ Add</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                )}
            />

            <TouchableOpacity style={styles.refresh} onPress={load}>
                <Text style={{ color: "#fff", fontWeight: "600" }}>Refresh</Text>
            </TouchableOpacity>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 16, backgroundColor: "#fff" },
    h1: { fontSize: 22, fontWeight: "700", marginBottom: 12 },
    card: {
        backgroundColor: "#f6f7fb",
        padding: 14,
        borderRadius: 12,
        marginBottom: 12,
    },
    cardHeader: {
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 6,
    },
    name: { fontSize: 16, fontWeight: "600", flex: 1 },
    portion: {
        fontSize: 13,
        color: "#666",
        backgroundColor: "#e8e8e8",
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 10
    },
    reason: {
        fontSize: 13,
        color: "#666",
        marginBottom: 8,
        fontStyle: "italic",
    },
    badgeRow: {
        flexDirection: "row",
        flexWrap: "wrap",
        marginBottom: 8,
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
        borderWidth: 1,
        marginRight: 6,
        marginBottom: 4,
    },
    badgeText: {
        fontSize: 11,
        fontWeight: "600",
    },
    cardFooter: {
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        marginTop: 4,
    },
    calories: {
        fontSize: 14,
        color: "#333",
        fontWeight: "500",
    },
    btn: {
        backgroundColor: "#3478f6",
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 8,
    },
    refresh: {
        backgroundColor: "#3478f6",
        padding: 14,
        borderRadius: 12,
        alignItems: "center",
        marginTop: 8,
    },
});