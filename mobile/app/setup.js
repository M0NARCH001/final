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
            };

            // compute plan FIRST
            const plan = await API.computeGoals(payload);

            // store BOTH
            await AsyncStorage.multiSet([
                ["nutrimate_profile", JSON.stringify(payload)],
                ["nutrimate_goals", JSON.stringify(plan)],
            ]);

            // verify
            const check = await AsyncStorage.getItem("nutrimate_goals");
            if (!check) throw new Error("Goals not saved");

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
});