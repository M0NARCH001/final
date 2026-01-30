import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

export default function TabsLayout() {
    return (
        <Tabs
            screenOptions={{
                headerShown: false,
                tabBarActiveTintColor: "#1A73E8",
            }}
        >
            <Tabs.Screen
                name="index"
                options={{
                    title: "Home",
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="home-outline" size={size} color={color} />
                    ),
                }}
            />

            <Tabs.Screen
                name="FoodLogScreen"
                options={{
                    title: "Log",
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="add-circle-outline" size={size} color={color} />
                    ),
                }}
            />

            <Tabs.Screen
                name="ScannerScreen"
                options={{
                    title: "Scan",
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="barcode-outline" size={size} color={color} />
                    ),
                }}
            />

            <Tabs.Screen
                name="RecommendationsScreen"
                options={{
                    title: "Recommendations",
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="stats-chart-outline" size={size} color={color} />
                    ),
                }}
            />

            <Tabs.Screen
                name="ProfileScreen"
                options={{
                    title: "Profile",
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="person-outline" size={size} color={color} />
                    ),
                }}
            />
        </Tabs>
    );
}