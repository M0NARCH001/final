import React, { useEffect, useState, useCallback } from "react";
import {
    View,
    Text,
    StyleSheet,
    FlatList,
    ActivityIndicator,
    ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import API from "../../src/api";
import CalorieProgressCircle from "../../components/CalorieProgressCircle";

/* ---------- Progress Bar ---------- */
function ProgressBar({ label, value = 0, target = 0, color = "#3478f6" }) {
    const pct =
        target && target > 0 ? Math.min(100, Math.round((value / target) * 100)) : 0;

    return (
        <View style={{ marginVertical: 6 }}>
            <View style={styles.row}>
                <Text style={styles.barLabel}>{label}</Text>
                <Text style={styles.barValue}>
                    {Math.round(value)} / {Math.round(target)} ({pct}%)
                </Text>
            </View>
            <View style={styles.barBg}>
                <View style={[styles.barFill, { width: `${pct}%`, backgroundColor: color }]} />
            </View>
        </View>
    );
}

/* ---------- Warning Badge ---------- */
function WarningBadge({ warning }) {
    const bgColor = warning.severity === "warning" ? "#fff3cd" : "#d1ecf1";
    const textColor = warning.severity === "warning" ? "#856404" : "#0c5460";
    const icon = warning.severity === "warning" ? "⚠️" : "ℹ️";

    return (
        <View style={[styles.warningBadge, { backgroundColor: bgColor }]}>
            <Text style={[styles.warningText, { color: textColor }]}>
                {icon} {warning.message}
            </Text>
        </View>
    );
}

/* ---------- Home ---------- */
export default function Home() {
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [goals, setGoals] = useState(null);
    const [logs, setLogs] = useState([]);
    const [warnings, setWarnings] = useState([]);

    /* initial bootstrap */
    useEffect(() => {
        bootstrap();
    }, []);

    async function bootstrap() {
        const g = await AsyncStorage.getItem("nutrimate_goals");
        const uid = await AsyncStorage.getItem("user_id");

        // Redirect to setup if either goals OR user_id is missing
        // This prevents falling back to user_id: 1 and seeing old logs
        if (!g || !uid) {
            router.replace("/setup");
            return;
        }

        setGoals(JSON.parse(g));
        await fetchData(JSON.parse(g));
        setLoading(false);
    }

    /* refresh when tab focused */
    useFocusEffect(
        useCallback(() => {
            if (goals) fetchData(goals);
        }, [goals])
    );

    async function fetchData(currentGoals) {
        try {
            const uidStr = await AsyncStorage.getItem("user_id");
            const uid = uidStr ? parseInt(uidStr) : 1;

            const l = await API.getTodayLogs(uid);
            setLogs(Array.isArray(l) ? l : []);

            // Fetch daily summary with warnings
            try {
                const summary = await API.getDailySummary(uid, currentGoals);
                if (summary.warnings) {
                    setWarnings(summary.warnings);
                }
            } catch (e) {
                console.warn("summary fetch error", e);
            }
        } catch (e) {
            console.warn("home logs error", e);
        }
    }

    if (loading || !goals)
        return <ActivityIndicator style={{ flex: 1 }} size="large" />;

    /* totals from logs - including micronutrients */
    const totals = logs.reduce(
        (a, b) => {
            a.Calories_kcal += b.Calories_kcal || 0;
            a.Protein_g += b.Protein_g || 0;
            a.Carbohydrates_g += b.Carbohydrates_g || 0;
            a.Fats_g += b.Fats_g || 0;
            a.Fibre_g += b.Fibre_g || 0;
            a.Sodium_mg += b.Sodium_mg || 0;
            a.Iron_mg += b.Iron_mg || 0;
            a.Calcium_mg += b.Calcium_mg || 0;
            a.VitaminC_mg += b.VitaminC_mg || 0;
            return a;
        },
        {
            Calories_kcal: 0,
            Protein_g: 0,
            Carbohydrates_g: 0,
            Fats_g: 0,
            Fibre_g: 0,
            Sodium_mg: 0,
            Iron_mg: 0,
            Calcium_mg: 0,
            VitaminC_mg: 0,
        }
    );

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView showsVerticalScrollIndicator={false}>
                <Text style={styles.h1}>Today</Text>

                {/* Warnings Section */}
                {warnings.length > 0 && (
                    <View style={styles.warningsContainer}>
                        {warnings.slice(0, 3).map((w, idx) => (
                            <WarningBadge key={idx} warning={w} />
                        ))}
                    </View>
                )}

                <View style={{ alignItems: "center", marginVertical: 16 }}>
                    <CalorieProgressCircle
                        progress={totals.Calories_kcal || 0}
                        goal={goals.daily_calories || goals.Calories_kcal || 2000}
                    />

                    <Text style={{ marginTop: 6, color: "#666" }}>
                        {Math.round(totals.Calories_kcal || 0)} / {Math.round(goals.daily_calories || goals.Calories_kcal || 2000)} kcal
                    </Text>
                </View>

                {/* Macros Card */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Macronutrients</Text>

                    <ProgressBar
                        label="Protein (g)"
                        value={totals.Protein_g}
                        target={goals.protein_g}
                        color="#22c55e"
                    />

                    <ProgressBar
                        label="Carbs (g)"
                        value={totals.Carbohydrates_g}
                        target={goals.carbs_g}
                        color="#3b82f6"
                    />

                    <ProgressBar
                        label="Fat (g)"
                        value={totals.Fats_g}
                        target={goals.fat_g}
                        color="#f59e0b"
                    />
                </View>

                {/* Micronutrients Card */}
                <View style={[styles.card, { marginTop: 12 }]}>
                    <Text style={styles.cardTitle}>Micronutrients</Text>

                    <ProgressBar
                        label="Fiber (g)"
                        value={totals.Fibre_g}
                        target={goals.fiber_g || 25}
                        color="#10b981"
                    />

                    <ProgressBar
                        label="Sodium (mg)"
                        value={totals.Sodium_mg}
                        target={goals.sodium_limit_mg || 2300}
                        color="#ef4444"
                    />

                    <ProgressBar
                        label="Iron (mg)"
                        value={totals.Iron_mg}
                        target={goals.iron_mg || 18}
                        color="#8b5cf6"
                    />

                    <ProgressBar
                        label="Calcium (mg)"
                        value={totals.Calcium_mg}
                        target={goals.calcium_mg || 1000}
                        color="#06b6d4"
                    />

                    <ProgressBar
                        label="Vitamin C (mg)"
                        value={totals.VitaminC_mg}
                        target={goals.vitaminC_mg || 90}
                        color="#f97316"
                    />
                </View>

                <Text style={styles.h2}>Today's Logs</Text>

                {logs.length === 0 ? (
                    <Text style={{ padding: 16, color: "#666" }}>No logs yet.</Text>
                ) : (
                    logs.map((item, idx) => (
                        <View key={idx} style={styles.logRow}>
                            <Text style={styles.logName}>{item.food_name}</Text>
                            <Text style={styles.logMeta}>
                                {Math.round(item.Calories_kcal || 0)} kcal
                            </Text>
                        </View>
                    ))
                )}
            </ScrollView>
        </SafeAreaView>
    );
}

/* ---------- Styles ---------- */
const styles = StyleSheet.create({
    container: { flex: 1, padding: 16, backgroundColor: "#fff" },
    h1: { fontSize: 22, fontWeight: "700", marginBottom: 8 },
    h2: { fontSize: 18, fontWeight: "600", marginTop: 16, marginBottom: 8 },
    card: { backgroundColor: "#f6f7fb", padding: 14, borderRadius: 12 },
    cardTitle: { fontSize: 14, fontWeight: "600", color: "#666", marginBottom: 8 },
    row: { flexDirection: "row", justifyContent: "space-between" },
    barLabel: { fontSize: 13, color: "#333" },
    barValue: { fontSize: 12, color: "#666" },
    barBg: {
        height: 8,
        backgroundColor: "#e6e6e6",
        borderRadius: 4,
        marginTop: 4,
        overflow: "hidden",
    },
    barFill: { height: "100%", backgroundColor: "#3478f6", borderRadius: 4 },
    logRow: {
        paddingVertical: 10,
        borderBottomWidth: 1,
        borderBottomColor: "#eee",
    },
    logName: { fontSize: 15, fontWeight: "600" },
    logMeta: { color: "#666" },
    warningsContainer: {
        marginBottom: 12,
    },
    warningBadge: {
        padding: 10,
        borderRadius: 8,
        marginBottom: 6,
    },
    warningText: {
        fontSize: 13,
        fontWeight: "500",
    },
});