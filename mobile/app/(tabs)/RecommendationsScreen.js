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

            const logs = await API.getTodayLogs(1) || [];

            const payload = {
                food_logs: (Array.isArray(logs) ? logs : []).map((l) => ({
                    food_id: l.food_id,
                    quantity: l.quantity || 1,
                })),
                targets: {
                    Calories_kcal: plan.daily_calories,
                    Protein_g: plan.protein_g,
                    Fats_g: plan.fat_g,
                    Carbohydrates_g: plan.carbs_g,
                },
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
        await API.addFoodLog({
            user_id: 1,
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
                    <Text style={{ padding: 20 }}>No recommendations yet.</Text>
                )}
                renderItem={({ item }) => (
                    <View style={styles.card}>
                        <Text style={styles.name}>{item.food_name}</Text>
                        <Text>Score: {Math.round(item.score)}</Text>

                        <TouchableOpacity
                            style={styles.btn}
                            onPress={() => addFood(item)}
                        >
                            <Text style={{ color: "#fff" }}>Add to Log</Text>
                        </TouchableOpacity>
                    </View>
                )}
            />

            <TouchableOpacity style={styles.refresh} onPress={load}>
                <Text style={{ color: "#fff" }}>Refresh</Text>
            </TouchableOpacity>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 16 },
    h1: { fontSize: 22, fontWeight: "700", marginBottom: 12 },
    card: {
        backgroundColor: "#f6f7fb",
        padding: 12,
        borderRadius: 12,
        marginBottom: 12,
    },
    name: { fontSize: 16, fontWeight: "600" },
    btn: {
        backgroundColor: "#3478f6",
        padding: 10,
        borderRadius: 8,
        marginTop: 8,
        alignItems: "center",
    },
    refresh: {
        backgroundColor: "#3478f6",
        padding: 14,
        borderRadius: 12,
        alignItems: "center",
        marginTop: 8,
    },
});