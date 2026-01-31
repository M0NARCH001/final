import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  Alert
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import API from "../../src/api";

export default function ProfileScreen() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    gender: "Male",
    height_cm: "",
    weight_kg: "",
    goal: "Maintain",
  });

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const p = await AsyncStorage.getItem("nutrimate_profile");
    if (p) {
      const parsed = JSON.parse(p);
      setProfile(parsed);
      setFormData({
        name: parsed.name || "",
        age: String(parsed.age || ""),
        gender: parsed.gender || "Male",
        height_cm: String(parsed.height_cm || ""),
        weight_kg: String(parsed.weight_kg || ""),
        goal: parsed.goal || "Maintain",
      });
    }
  }

  async function save() {
    setLoading(true);
    try {
      const user_id = await AsyncStorage.getItem("user_id");
      if (!user_id) throw new Error("User ID not found");

      const updatedProfile = {
        ...profile,
        name: formData.name,
        age: Number(formData.age),
        gender: formData.gender,
        height_cm: Number(formData.height_cm),
        weight_kg: Number(formData.weight_kg),
        goal: formData.goal,
      };

      // 1. Update backend user record
      await API.request(`/users/${user_id}`, {
        method: "PUT",
        body: {
          name: updatedProfile.name,
          age: updatedProfile.age,
          gender: updatedProfile.gender,
          height_cm: updatedProfile.height_cm,
          weight_kg: updatedProfile.weight_kg,
          goal: updatedProfile.goal,
        }
      });

      // 2. Re-compute goals based on new info
      const newGoals = await API.computeGoals(updatedProfile);

      // 3. Save everything locally
      await AsyncStorage.multiSet([
        ["nutrimate_profile", JSON.stringify(updatedProfile)],
        ["nutrimate_goals", JSON.stringify(newGoals)],
      ]);

      setProfile(updatedProfile);
      setIsEditing(false);
      Alert.alert("Success", "Profile updated and goals recalibrated.");
    } catch (e) {
      Alert.alert("Error", e.message || "Failed to save profile");
    } finally {
      setLoading(false);
    }
  }

  async function reset() {
    Alert.alert(
      "Reset All Data?",
      "This will clear your profile and logs. This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Reset",
          style: "destructive",
          onPress: async () => {
            await AsyncStorage.clear();
            router.replace("/setup");
          }
        }
      ]
    );
  }

  if (!profile) {
    return (
      <SafeAreaView style={styles.center}>
        <Text>No profile found</Text>
        <TouchableOpacity style={styles.btn} onPress={() => router.replace("/setup")}>
          <Text style={styles.btnTxt}>Create Profile</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.h}>Profile</Text>
          <TouchableOpacity
            onPress={() => isEditing ? setIsEditing(false) : setIsEditing(true)}
          >
            <Text style={styles.editLink}>{isEditing ? "Cancel" : "Edit"}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <EditableRow
            label="Name"
            value={formData.name}
            isEditing={isEditing}
            onChange={(v) => setFormData({ ...formData, name: v })}
          />
          <EditableRow
            label="Age"
            value={formData.age}
            isEditing={isEditing}
            keyboardType="number-pad"
            onChange={(v) => setFormData({ ...formData, age: v })}
          />
          <EditableRow
            label="Gender"
            value={formData.gender}
            isEditing={isEditing}
            isPicker
            options={["Male", "Female"]}
            onChange={(v) => setFormData({ ...formData, gender: v })}
          />
          <EditableRow
            label="Height (cm)"
            value={formData.height_cm}
            isEditing={isEditing}
            keyboardType="number-pad"
            onChange={(v) => setFormData({ ...formData, height_cm: v })}
          />
          <EditableRow
            label="Weight (kg)"
            value={formData.weight_kg}
            isEditing={isEditing}
            keyboardType="number-pad"
            onChange={(v) => setFormData({ ...formData, weight_kg: v })}
          />
          <EditableRow
            label="Goal"
            value={formData.goal}
            isEditing={isEditing}
            isPicker
            options={["Maintain", "Weight Loss", "Weight Gain"]}
            onChange={(v) => setFormData({ ...formData, goal: v })}
          />
        </View>

        {isEditing ? (
          <TouchableOpacity style={styles.btn} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnTxt}>Save Changes</Text>}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={[styles.btn, { backgroundColor: "#e33" }]} onPress={reset}>
            <Text style={styles.btnTxt}>Reset App Data</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function EditableRow({ label, value, isEditing, onChange, keyboardType = "default", isPicker = false, options = [] }) {
  if (isEditing) {
    if (isPicker) {
      return (
        <View style={styles.row}>
          <Text style={styles.label}>{label}</Text>
          <View style={styles.pickerRow}>
            {options.map(opt => (
              <TouchableOpacity
                key={opt}
                style={[styles.chip, value === opt && styles.chipActive]}
                onPress={() => onChange(opt)}
              >
                <Text style={[styles.chipText, value === opt && styles.chipTextActive]}>{opt}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      );
    }
    return (
      <View style={styles.row}>
        <Text style={styles.label}>{label}</Text>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChange}
          keyboardType={keyboardType}
        />
      </View>
    );
  }

  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 20 },
  h: { fontSize: 24, fontWeight: "700" },
  editLink: { color: "#1A73E8", fontWeight: "600", fontSize: 16 },
  card: { backgroundColor: "#f8f9fa", borderRadius: 12, padding: 16, marginBottom: 20 },
  row: { marginBottom: 16 },
  label: { fontSize: 14, color: "#666", marginBottom: 4 },
  value: { fontSize: 16, fontWeight: "600", color: "#333" },
  input: { borderBottomWidth: 1, borderBottomColor: "#1A73E8", fontSize: 16, paddingVertical: 4, fontWeight: "600", color: "#333" },
  pickerRow: { flexDirection: "row", flexWrap: "wrap", marginTop: 4 },
  chip: { borderWidth: 1, borderColor: "#ddd", paddingVertical: 4, paddingHorizontal: 12, borderRadius: 12, marginRight: 8, marginBottom: 8 },
  chipActive: { backgroundColor: "#1A73E8", borderColor: "#1A73E8" },
  chipText: { fontSize: 13, color: "#666" },
  chipTextActive: { color: "#fff", fontWeight: "600" },
  btn: {
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    backgroundColor: "#1A73E8",
  },
  btnTxt: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
