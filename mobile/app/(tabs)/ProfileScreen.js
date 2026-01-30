import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

export default function ProfileScreen() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const p = await AsyncStorage.getItem("nutrimate_profile");
    if (p) setProfile(JSON.parse(p));
  }

  async function reset() {
    await AsyncStorage.clear();
    router.replace("/setup");
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
      <Text style={styles.h}>Profile</Text>

      <Row label="Name" value={profile.name} />
      <Row label="Age" value={profile.age} />
      <Row label="Gender" value={profile.gender} />
      <Row label="Height" value={`${profile.height_cm} cm`} />
      <Row label="Weight" value={`${profile.weight_kg} kg`} />
      <Row label="Goal" value={profile.goal} />

      <TouchableOpacity style={styles.btn} onPress={() => router.push("/setup")}>
        <Text style={styles.btnTxt}>Edit</Text>
      </TouchableOpacity>

      <TouchableOpacity style={[styles.btn, { backgroundColor: "#e33" }]} onPress={reset}>
        <Text style={styles.btnTxt}>Reset</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

function Row({ label, value }) {
  return (
    <View style={styles.row}>
      <Text>{label}</Text>
      <Text style={{ fontWeight: "600" }}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  h: { fontSize: 22, fontWeight: "700", marginBottom: 16 },
  row: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 8 },
  btn: {
    marginTop: 20,
    backgroundColor: "#34b889",
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  btnTxt: { color: "#fff", fontWeight: "600" },
});