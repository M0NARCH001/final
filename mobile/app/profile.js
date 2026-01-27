import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";

export default function Profile() {
    const router = useRouter();

    const [name, setName] = useState("");
    const [age, setAge] = useState("");
    const [gender, setGender] = useState("Male");

    const saveProfile = async () => {
        const a = Number(age);

        let life_stage = "Adult Male";
        if (gender === "Female") life_stage = "Adult Female";
        if (a < 18) life_stage = "Child";

        const profile = {
            name,
            age: a,
            gender,
            life_stage,
        };

        await AsyncStorage.setItem("nutrimate_profile", JSON.stringify(profile));

        router.replace("/(tabs)");
    };

    return (
        <View style={{ flex: 1, justifyContent: "center", padding: 20 }}>
            <Text style={{ fontSize: 26, fontWeight: "800", marginBottom: 20 }}>
                Create Profile
            </Text>

            <TextInput
                placeholder="Name"
                value={name}
                onChangeText={setName}
                style={{ borderWidth: 1, padding: 12, borderRadius: 10, marginBottom: 12 }}
            />

            <TextInput
                placeholder="Age"
                keyboardType="numeric"
                value={age}
                onChangeText={setAge}
                style={{ borderWidth: 1, padding: 12, borderRadius: 10, marginBottom: 12 }}
            />

            <TouchableOpacity
                onPress={() => setGender(gender === "Male" ? "Female" : "Male")}
                style={{ padding: 12, borderRadius: 10, borderWidth: 1, marginBottom: 20 }}
            >
                <Text>Gender: {gender}</Text>
            </TouchableOpacity>

            <TouchableOpacity
                onPress={saveProfile}
                style={{ backgroundColor: "#1A73E8", padding: 14, borderRadius: 12 }}
            >
                <Text style={{ color: "white", textAlign: "center", fontWeight: "700" }}>
                    Continue
                </Text>
            </TouchableOpacity>
        </View>
    );
}
