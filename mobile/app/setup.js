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

    const [username, setUsername] = useState("");
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

    // Phase 5: Region Selection
    const [region, setRegion] = useState("All India");

    // Dietary preference
    const [dietaryPref, setDietaryPref] = useState("any");

    // Auth
    const [password, setPassword] = useState("");
    const [isLoginMode, setIsLoginMode] = useState(false);

    // ── LOGIN FLOW ────────────────────────────────────────────────────────────
    async function handleLogin() {
        const usernameClean = username.trim().toLowerCase();
        if (!usernameClean || !password) {
            alert("Enter your username and password.");
            return;
        }
        try {
            const userData = await API.request("/auth/login", {
                method: "POST",
                body: { username: usernameClean, password },
            });

            // Recompute daily goals from the stored profile
            const profilePayload = {
                age: userData.age || 25,
                gender: userData.gender || "Male",
                height_cm: userData.height_cm || 170,
                weight_kg: userData.weight_kg || 70,
                activity_level: userData.activity_level || "Moderate",
                goal: userData.goal || "Maintain",
                target_weight: userData.target_weight_kg || null,
                days: 90,
                has_diabetes: userData.has_diabetes,
                has_hypertension: userData.has_hypertension,
                has_pcos: userData.has_pcos,
                muscle_gain_focus: userData.muscle_gain_focus,
                heart_health_focus: userData.heart_health_focus,
                region: userData.region || "All India",
            };
            const plan = await API.computeGoals(profilePayload);
            const dp = userData.dietary_preference || "any";

            await AsyncStorage.multiSet([
                ["user_id", userData.user_id.toString()],
                ["username", userData.username],
                ["region", userData.region || "All India"],
                ["dietary_preference", dp],
                ["nutrimate_profile", JSON.stringify({ ...profilePayload, dietary_preference: dp })],
                ["nutrimate_goals", JSON.stringify(plan)],
            ]);

            router.replace("/(tabs)");
        } catch (err) {
            const msg = err?.message || String(err);
            if (msg.includes("401")) {
                alert("Incorrect username or password.");
            } else {
                alert("Login failed: " + msg);
            }
        }
    }

    // ── REGISTER / PROFILE-UPDATE FLOW ───────────────────────────────────────
    async function saveProfile() {
        try {
            if (!username || !name || !age || !height || !weight) {
                alert("Fill all required fields.");
                return;
            }

            const usernameClean = username.trim().toLowerCase();
            if (!/^[a-z0-9_]{3,20}$/.test(usernameClean)) {
                alert("Username: 3-20 characters, letters/numbers/underscore only.");
                return;
            }

            const existingStoredId = await AsyncStorage.getItem("user_id");
            const storedUsername = await AsyncStorage.getItem("username");
            const isEditing = existingStoredId && storedUsername === usernameClean;

            // Password required for new registrations only
            if (!isEditing) {
                if (!password) { alert("Choose a password."); return; }
                if (password.length < 6) { alert("Password must be at least 6 characters."); return; }
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
                has_diabetes: hasDiabetes,
                has_hypertension: hasHypertension,
                has_pcos: hasPcos,
                muscle_gain_focus: muscleGainFocus,
                heart_health_focus: heartHealthFocus,
                region,
            };

            const plan = await API.computeGoals(payload);

            let activeUserId;

            if (isEditing) {
                // Updating existing profile
                activeUserId = existingStoredId;
                try {
                    await API.request(`/users/${existingStoredId}`, {
                        method: "PUT",
                        body: {
                            name: payload.name, age: payload.age, gender: payload.gender,
                            height_cm: payload.height_cm, weight_kg: payload.weight_kg,
                            activity_level: payload.activity_level, region: payload.region,
                        },
                    });
                } catch (err) {
                    console.warn("Profile update failed (non-fatal):", err);
                }
            } else {
                // New registration via /auth/signup
                const result = await API.request("/auth/signup", {
                    method: "POST",
                    body: {
                        username: usernameClean,
                        password,
                        ...payload,
                        dietary_preference: dietaryPref,
                    },
                });
                activeUserId = result.user_id.toString();
            }

            await AsyncStorage.multiSet([
                ["user_id", activeUserId.toString()],
                ["username", usernameClean],
                ["region", region],
                ["dietary_preference", dietaryPref],
                ["nutrimate_profile", JSON.stringify({ ...payload, dietary_preference: dietaryPref })],
                ["nutrimate_goals", JSON.stringify(plan)],
            ]);

            router.replace("/(tabs)");
        } catch (e) {
            const msg = e?.message || String(e);
            if (msg.includes("409")) {
                alert("Username already taken. Pick a different one or login instead.");
            } else {
                alert(msg || "Setup failed");
            }
        }
    }

    return (
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <SafeAreaView style={{ flex: 1 }}>
                <ScrollView contentContainerStyle={styles.container}>

                    <Text style={styles.h1}>
                        {isLoginMode ? "Welcome Back" : "Create Account"}
                    </Text>

                    {/* ── Mode toggle ── */}
                    <View style={styles.modeRow}>
                        <TouchableOpacity
                            style={[styles.modeBtn, !isLoginMode && styles.modeBtnActive]}
                            onPress={() => setIsLoginMode(false)}
                        >
                            <Text style={[styles.modeBtnText, !isLoginMode && styles.modeBtnTextActive]}>
                                Register
                            </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={[styles.modeBtn, isLoginMode && styles.modeBtnActive]}
                            onPress={() => setIsLoginMode(true)}
                        >
                            <Text style={[styles.modeBtnText, isLoginMode && styles.modeBtnTextActive]}>
                                Login
                            </Text>
                        </TouchableOpacity>
                    </View>

                    {/* ── Username ── */}
                    <Text style={styles.label}>Username *</Text>
                    <TextInput
                        placeholder="Your username"
                        value={username}
                        onChangeText={setUsername}
                        autoCapitalize="none"
                        autoCorrect={false}
                        style={styles.input}
                    />
                    {!isLoginMode && (
                        <Text style={styles.hint}>3-20 characters, letters/numbers/underscore only</Text>
                    )}

                    {/* ── Password ── */}
                    <Text style={styles.label}>Password *</Text>
                    <TextInput
                        placeholder={isLoginMode ? "Your password" : "Choose a password (min 6 chars)"}
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                        autoCapitalize="none"
                        style={styles.input}
                    />

                    {/* ── LOGIN button — only shown in login mode ── */}
                    {isLoginMode && (
                        <TouchableOpacity style={styles.btn} onPress={handleLogin}>
                            <Text style={styles.btnText}>Login</Text>
                        </TouchableOpacity>
                    )}

                    {/* ── Everything below is REGISTER mode only ── */}
                    {!isLoginMode && (
                    <>

                    <Text style={styles.label}>Name *</Text>
                    <TextInput
                        placeholder="Your name"
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

                    <Text style={styles.h2}>Dietary Preference</Text>
                    <Text style={styles.hint}>We'll filter recommendations to match your diet</Text>
                    <View style={styles.row}>
                        {[
                            { key: "any",             label: "Any" },
                            { key: "vegetarian",      label: "Vegetarian" },
                            { key: "non-vegetarian",  label: "Non-Veg" },
                        ].map(({ key, label }) => (
                            <TouchableOpacity
                                key={key}
                                onPress={() => setDietaryPref(key)}
                                style={[styles.chip, dietaryPref === key && styles.chipActive]}
                            >
                                <Text style={dietaryPref === key ? styles.chipTextActive : styles.chipText}>
                                    {label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    <Text style={styles.h2}>Regional Preferences</Text>
                    <Text style={styles.hint}>This helps us recommend local dishes</Text>

                    <View style={styles.regionContainer}>
                        {["Andhra Pradesh", "Tamil Nadu", "Kerala", "Karnataka", "Maharashtra", "Punjab", "All India"].map((r) => (
                            <TouchableOpacity
                                key={r}
                                onPress={() => setRegion(r)}
                                style={[styles.regionChip, region === r && styles.regionChipActive]}
                            >
                                <Text style={region === r ? styles.regionChipTextActive : styles.regionChipText}>
                                    {r}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    <TouchableOpacity style={styles.btn} onPress={saveProfile}>
                        <Text style={styles.btnText}>Create Account</Text>
                    </TouchableOpacity>

                    </>)}

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
    modeRow: {
        flexDirection: "row",
        borderRadius: 10,
        borderWidth: 1,
        borderColor: "#ddd",
        overflow: "hidden",
        marginBottom: 20,
    },
    modeBtn: {
        flex: 1,
        paddingVertical: 11,
        alignItems: "center",
        backgroundColor: "#f5f5f5",
    },
    modeBtnActive: {
        backgroundColor: "#1A73E8",
    },
    modeBtnText: {
        fontWeight: "600",
        color: "#555",
    },
    modeBtnTextActive: {
        color: "#fff",
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
    regionContainer: {
        flexDirection: "row",
        flexWrap: "wrap",
        marginBottom: 10,
    },
    regionChip: {
        borderWidth: 1,
        borderColor: "#ccc",
        paddingVertical: 8,
        paddingHorizontal: 14,
        borderRadius: 20,
        marginRight: 8,
        marginBottom: 8,
        backgroundColor: "#f9f9f9",
    },
    regionChipActive: {
        backgroundColor: "#34A853",
        borderColor: "#34A853",
    },
    regionChipText: {
        color: "#444",
    },
    regionChipTextActive: {
        color: "white",
        fontWeight: "600",
    },
});