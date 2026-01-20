import React from "react";
import { Tabs } from "expo-router";
import { MaterialIcons, Ionicons } from "@expo/vector-icons";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#1A73E8",
        tabBarLabelStyle: { fontSize: 12 },
        tabBarStyle: { height: 60, paddingBottom: 6 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size ?? 20} color={color} />
          ),
        }}
      />

      <Tabs.Screen
        name="FoodLogScreen"
        options={{
          title: "Log Food",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="list" size={size ?? 20} color={color} />
          ),
        }}
      />

      <Tabs.Screen
        name="ScannerScreen"
        options={{
          title: "Scan",
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons name="camera-alt" size={size ?? 20} color={color} />
          ),
        }}
      />

      <Tabs.Screen
        name="ReportScreen"
        options={{
          title: "Report",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="stats-chart" size={size ?? 20} color={color} />
          ),
        }}
      />

      <Tabs.Screen
        name="ProfileScreen"
        options={{
          title: "Profile",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size ?? 20} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
