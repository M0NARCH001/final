import React, { useEffect, useState, useCallback } from "react";
import {
    View,
    Text,
    StyleSheet,
    FlatList,
    ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import API from "../../src/api";

/* ---------- Progress Bar ---------- */
function ProgressBar({ label, value = 0, target = 0 }) {
    const pct =
        target && target > 0 ? Math.min(100, Math.round((value / target) * 100)) : 0;

    return (
        <View style={{ marginVertical: 8 }}>
            <View style={styles.row}>
                <Text>{label}</Text>
                <Text>
                    {Math.round(value)} / {Math.round(target)} ({pct}%)
                </Text>
            </View>
            <View style={styles.barBg}>
                <View style={[styles.barFill, { width: `${pct}%` }]} />
            </View>
        </View>
    );
}

/* ---------- Home ---------- */
export default function Home() {
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [goals, setGoals] = useState(null);
    const [logs, setLogs] = useState([]);

    /* initial bootstrap */
    useEffect(() => {
        bootstrap();
    }, []);

    async function bootstrap() {
        const g = await AsyncStorage.getItem("nutrimate_goals");

        if (!g) {
            router.replace("/setup");
            return;
        }

        setGoals(JSON.parse(g));
        await fetchLogs();
        setLoading(false);
    }

    /* refresh when tab focused */
    useFocusEffect(
        useCallback(() => {
            fetchLogs();
        }, [])
    );

    async function fetchLogs() {
        try {
            const l = await API.getTodayLogs(1);
            setLogs(Array.isArray(l) ? l : []);
        } catch (e) {
            console.warn("home logs error", e);
        }
    }

    if (loading || !goals)
        return <ActivityIndicator style={{ flex: 1 }} size="large" />;

    /* totals from logs */
    const totals = logs.reduce(
        (a, b) => {
            a.Calories_kcal += b.Calories_kcal || 0;
            a.Protein_g += b.Protein_g || 0;
            a.Carbohydrates_g += b.Carbohydrates_g || 0;
            a.Fats_g += b.Fats_g || 0;
            return a;
        },
        {
            Calories_kcal: 0,
            Protein_g: 0,
            Carbohydrates_g: 0,
            Fats_g: 0,
        }
    );

    return (
        <SafeAreaView style={styles.container}>
            <Text style={styles.h1}>Today</Text>

            <View style={styles.card}>
                <Text style={styles.big}>{Math.round(totals.Calories_kcal)} kcal</Text>

                <ProgressBar
                    label="Protein (g)"
                    value={totals.Protein_g}
                    target={goals.protein_g}
                />

                <ProgressBar
                    label="Carbs (g)"
                    value={totals.Carbohydrates_g}
                    target={goals.carbs_g}
                />

                <ProgressBar
                    label="Fat (g)"
                    value={totals.Fats_g}
                    target={goals.fat_g}
                />
            </View>

            <Text style={styles.h2}>Today’s Logs</Text>

            <FlatList
                data={logs}
                keyExtractor={(i, idx) => idx.toString()}
                ListEmptyComponent={() => (
                    <Text style={{ padding: 16 }}>No logs yet.</Text>
                )}
                renderItem={({ item }) => (
                    <View style={styles.logRow}>
                        <Text style={styles.logName}>{item.food_name}</Text>
                        <Text style={styles.logMeta}>
                            {Math.round(item.Calories_kcal || 0)} kcal
                        </Text>
                    </View>
                )}
            />
        </SafeAreaView>
    );
}

/* ---------- Styles ---------- */
const styles = StyleSheet.create({
    container: { flex: 1, padding: 16, backgroundColor: "#fff" },
    h1: { fontSize: 22, fontWeight: "700", marginBottom: 12 },
    h2: { fontSize: 18, fontWeight: "600", marginTop: 12 },
    card: { backgroundColor: "#f6f7fb", padding: 12, borderRadius: 12 },
    big: { fontSize: 28, fontWeight: "700", marginBottom: 8 },
    row: { flexDirection: "row", justifyContent: "space-between" },
    barBg: {
        height: 10,
        backgroundColor: "#e6e6e6",
        borderRadius: 6,
        marginTop: 6,
        overflow: "hidden",
    },
    barFill: { height: "100%", backgroundColor: "#3478f6" },
    logRow: {
        paddingVertical: 10,
        borderBottomWidth: 1,
        borderBottomColor: "#eee",
    },
    logName: { fontSize: 15, fontWeight: "600" },
    logMeta: { color: "#666" },
});