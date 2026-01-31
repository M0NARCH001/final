import React, { useState } from "react";
import {
    View,
    Text,
    TextInput,
    StyleSheet,
    TouchableOpacity,
    Keyboard,
    TouchableWithoutFeedback,
    ScrollView,
} from "react-native";
import Slider from "@react-native-community/slider";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import API from "../src/api";

export default function SetupScreen() {
    const router = useRouter();

    const [name, setName] = useState("");
    const [age, setAge] = useState("");
    const [gender, setGender] = useState("Male");

    const [height, setHeight] = useState("");
    const [weight, setWeight] = useState("");

    const [activity, setActivity] = useState("Moderate");
    const [goal, setGoal] = useState("Maintain");

    const [targetWeight, setTargetWeight] = useState("");
    const [days, setDays] = useState(60);

    // Health conditions
    const [hasDiabetes, setHasDiabetes] = useState(false);
    const [hasHypertension, setHasHypertension] = useState(false);
    const [hasPcos, setHasPcos] = useState(false);
    const [muscleGainFocus, setMuscleGainFocus] = useState(false);
    const [heartHealthFocus, setHeartHealthFocus] = useState(false);

    async function saveProfile() {
        try {
            if (!name || !age || !height || !weight) {
                alert("Fill all required fields");
                return;
            }

            const payload = {
                name,
                age: Number(age),
                gender,
                height_cm: Number(height),
                weight_kg: Number(weight),
                activity_level: activity,
                goal,
                target_weight: goal === "Maintain" ? null : Number(targetWeight),
                days,
                // Health conditions
                has_diabetes: hasDiabetes,
                has_hypertension: hasHypertension,
                has_pcos: hasPcos,
                muscle_gain_focus: muscleGainFocus,
                heart_health_focus: heartHealthFocus,
            };

            // 1. compute targets locally (via backend compute)
            const plan = await API.computeGoals(payload);

            // 2. register user in backend to get a unique user_id
            const userData = {
                name: payload.name,
                age: payload.age,
                gender: payload.gender,
                height_cm: payload.height_cm,
                weight_kg: payload.weight_kg,
                activity_level: payload.activity_level,
                goal: payload.goal,
            };

            let userResponse;
            try {
                // Check if we already have a user_id (editing mode)
                const existingId = await AsyncStorage.getItem("user_id");
                if (existingId) {
                    userResponse = await API.request(`/users/${existingId}`, {
                        method: "PUT",
                        body: userData
                    });
                } else {
                    userResponse = await API.request("/users", {
                        method: "POST",
                        body: userData
                    });
                }
            } catch (err) {
                console.warn("User registration failed, falling back to local only", err);
            }

            const activeUserId = userResponse?.user_id || 1;

            // 3. store profile, goals, AND the unique user_id
            await AsyncStorage.multiSet([
                ["user_id", activeUserId.toString()],
                ["nutrimate_profile", JSON.stringify(payload)],
                ["nutrimate_goals", JSON.stringify(plan)],
            ]);

            router.replace("/(tabs)");
        } catch (e) {
            alert(e.message || "Setup failed");
        }
    }

    return (
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <SafeAreaView style={{ flex: 1 }}>
                <ScrollView contentContainerStyle={styles.container}>

                    <Text style={styles.h1}>Setup Profile</Text>

                    <Text style={styles.label}>Name</Text>
                    <TextInput
                        placeholder="Name"
                        value={name}
                        onChangeText={setName}
                        style={styles.input}
                    />

                    <Text style={styles.label}>Age</Text>
                    <TextInput
                        placeholder="Age"
                        value={age}
                        onChangeText={setAge}
                        keyboardType="number-pad"
                        style={styles.input}
                    />

                    <Text style={styles.label}>Gender</Text>
                    <View style={styles.row}>
                        {["Male", "Female"].map((g) => (
                            <TouchableOpacity
                                key={g}
                                onPress={() => setGender(g)}
                                style={[styles.chip, gender === g && styles.chipActive]}
                            >
                                <Text style={gender === g ? styles.chipTextActive : styles.chipText}>
                                    {g}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    <Text style={styles.label}>Height (cm)</Text>
                    <TextInput
                        placeholder="Height (cm)"
                        value={height}
                        onChangeText={setHeight}
                        keyboardType="number-pad"
                        style={styles.input}
                    />

                    <Text style={styles.label}>Weight (kg)</Text>
                    <TextInput
                        placeholder="Weight (kg)"
                        value={weight}
                        onChangeText={setWeight}
                        keyboardType="number-pad"
                        style={styles.input}
                    />

                    <Text style={styles.label}>Activity Level</Text>
                    <View style={styles.row}>
                        {["Low", "Moderate", "High"].map((a) => (
                            <TouchableOpacity
                                key={a}
                                onPress={() => setActivity(a)}
                                style={[styles.chip, activity === a && styles.chipActive]}
                            >
                                <Text style={activity === a ? styles.chipTextActive : styles.chipText}>
                                    {a}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    <Text style={styles.label}>Goal</Text>
                    <View style={styles.row}>
                        {["Maintain", "Weight Loss", "Weight Gain"].map((g) => (
                            <TouchableOpacity
                                key={g}
                                onPress={() => setGoal(g)}
                                style={[styles.chip, goal === g && styles.chipActive]}
                            >
                                <Text style={goal === g ? styles.chipTextActive : styles.chipText}>
                                    {g}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    {goal !== "Maintain" && (
                        <>
                            <Text style={styles.label}>Target Weight (kg)</Text>
                            <TextInput
                                placeholder="Target Weight (kg)"
                                value={targetWeight}
                                onChangeText={setTargetWeight}
                                keyboardType="number-pad"
                                style={styles.input}
                            />

                            <Text style={styles.label}>Days: {days}</Text>
                            <Slider
                                minimumValue={14}
                                maximumValue={365}
                                step={1}
                                value={days}
                                onValueChange={setDays}
                            />
                        </>
                    )}

                    <Text style={styles.h2}>Health Conditions</Text>
                    <Text style={styles.hint}>Select any that apply for personalized recommendations</Text>

                    <TouchableOpacity
                        style={[styles.checkRow, hasDiabetes && styles.checkRowActive]}
                        onPress={() => setHasDiabetes(!hasDiabetes)}
                    >
                        <View style={[styles.checkbox, hasDiabetes && styles.checkboxActive]}>
                            {hasDiabetes && <Text style={styles.checkmark}>✓</Text>}
                        </View>
                        <Text style={styles.checkLabel}>Diabetes / Prediabetes</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.checkRow, hasHypertension && styles.checkRowActive]}
                        onPress={() => setHasHypertension(!hasHypertension)}
                    >
                        <View style={[styles.checkbox, hasHypertension && styles.checkboxActive]}>
                            {hasHypertension && <Text style={styles.checkmark}>✓</Text>}
                        </View>
                        <Text style={styles.checkLabel}>High Blood Pressure</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.checkRow, hasPcos && styles.checkRowActive]}
                        onPress={() => setHasPcos(!hasPcos)}
                    >
                        <View style={[styles.checkbox, hasPcos && styles.checkboxActive]}>
                            {hasPcos && <Text style={styles.checkmark}>✓</Text>}
                        </View>
                        <Text style={styles.checkLabel}>PCOS</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.checkRow, muscleGainFocus && styles.checkRowActive]}
                        onPress={() => setMuscleGainFocus(!muscleGainFocus)}
                    >
                        <View style={[styles.checkbox, muscleGainFocus && styles.checkboxActive]}>
                            {muscleGainFocus && <Text style={styles.checkmark}>✓</Text>}
                        </View>
                        <Text style={styles.checkLabel}>Muscle Gain Focus</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.checkRow, heartHealthFocus && styles.checkRowActive]}
                        onPress={() => setHeartHealthFocus(!heartHealthFocus)}
                    >
                        <View style={[styles.checkbox, heartHealthFocus && styles.checkboxActive]}>
                            {heartHealthFocus && <Text style={styles.checkmark}>✓</Text>}
                        </View>
                        <Text style={styles.checkLabel}>Heart Health Focus</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.btn} onPress={saveProfile}>
                        <Text style={styles.btnText}>Continue</Text>
                    </TouchableOpacity>

                </ScrollView>
            </SafeAreaView>
        </TouchableWithoutFeedback>
    );
}

const styles = StyleSheet.create({
    container: {
        padding: 16,
    },
    h1: {
        fontSize: 22,
        fontWeight: "700",
        marginBottom: 12,
    },
    input: {
        borderWidth: 1,
        borderColor: "#ddd",
        padding: 10,
        borderRadius: 8,
        marginBottom: 10,
    },
    label: {
        marginTop: 10,
        marginBottom: 6,
        fontWeight: "600",
    },
    row: {
        flexDirection: "row",
        marginBottom: 6,
    },
    chip: {
        borderWidth: 1,
        borderColor: "#ccc",
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 16,
        marginRight: 8,
    },
    chipActive: {
        backgroundColor: "#1A73E8",
        borderColor: "#1A73E8",
    },
    chipText: {
        color: "#333",
    },
    chipTextActive: {
        color: "white",
    },
    btn: {
        marginTop: 20,
        backgroundColor: "#1A73E8",
        padding: 14,
        borderRadius: 10,
        alignItems: "center",
    },
    btnText: {
        color: "white",
        fontWeight: "700",
    },
    h2: {
        fontSize: 18,
        fontWeight: "600",
        marginTop: 24,
        marginBottom: 4,
    },
    hint: {
        fontSize: 13,
        color: "#666",
        marginBottom: 12,
    },
    checkRow: {
        flexDirection: "row",
        alignItems: "center",
        paddingVertical: 12,
        paddingHorizontal: 12,
        marginBottom: 8,
        borderRadius: 10,
        backgroundColor: "#f8f8f8",
        borderWidth: 1,
        borderColor: "#eee",
    },
    checkRowActive: {
        backgroundColor: "#e8f0fe",
        borderColor: "#1A73E8",
    },
    checkbox: {
        width: 22,
        height: 22,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: "#ccc",
        marginRight: 12,
        justifyContent: "center",
        alignItems: "center",
    },
    checkboxActive: {
        backgroundColor: "#1A73E8",
        borderColor: "#1A73E8",
    },
    checkmark: {
        color: "white",
        fontWeight: "700",
        fontSize: 14,
    },
    checkLabel: {
        fontSize: 15,
        color: "#333",
    },
});