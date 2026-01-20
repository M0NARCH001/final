// mobile/app/ProfileScreen.js
import React, { useState, useEffect } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { createUser, getUser, updateUser } from "../../src/api";
import { useRouter, useLocalSearchParams } from "expo-router";

export default function ProfileScreen() {
  const router = useRouter();
  const [userId, setUserId] = useState(null); // you can store locally after creating
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("");
  const [height_cm, setHeight] = useState("");
  const [weight_kg, setWeight] = useState("");
  const [medical_conditions, setMedical] = useState("");

  useEffect(() => {
    // optionally load saved user id from async storage / dev stub
  }, []);

  async function handleSave() {
    const payload = {
      name,
      age: age ? Number(age) : null,
      sex,
      height_cm: height_cm ? Number(height_cm) : null,
      weight_kg: weight_kg ? Number(weight_kg) : null,
      medical_conditions
    };
    try {
      let resp;
      if (!userId) {
        resp = await createUser(payload);
        setUserId(resp.user_id);
        Alert.alert("Profile created");
      } else {
        resp = await updateUser(userId, payload);
        Alert.alert("Profile updated");
      }
    } catch (err) {
      Alert.alert("Save failed", String(err));
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Your profile</Text>

      <TextInput placeholder="Name" value={name} onChangeText={setName} style={styles.input} />
      <TextInput placeholder="Age" keyboardType="numeric" value={age} onChangeText={setAge} style={styles.input} />
      <TextInput placeholder="Sex (Male/Female)" value={sex} onChangeText={setSex} style={styles.input} />
      <TextInput placeholder="Height (cm)" keyboardType="numeric" value={height_cm} onChangeText={setHeight} style={styles.input} />
      <TextInput placeholder="Weight (kg)" keyboardType="numeric" value={weight_kg} onChangeText={setWeight} style={styles.input} />
      <TextInput placeholder="Medical conditions (comma)" value={medical_conditions} onChangeText={setMedical} style={styles.input} />

      <TouchableOpacity style={styles.btn} onPress={handleSave}>
        <Text style={styles.btnText}>Save Profile</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex:1, padding:16 },
  title: { fontSize:22, fontWeight:"700", marginBottom:12 },
  input: { borderWidth:1, borderColor:"#ddd", padding:10, borderRadius:8, marginBottom:8 },
  btn: { backgroundColor:"#1976D2", padding:12, borderRadius:8, alignItems:"center", marginTop:8 },
  btnText: { color:"white", fontWeight:"700" }
});