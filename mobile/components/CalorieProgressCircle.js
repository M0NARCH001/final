import React from "react";
import { View, Text } from "react-native";
import Svg, { Circle } from "react-native-svg";

export default function CalorieProgressCircle({
    size = 160,
    strokeWidth = 14,
    progress = 0,
    goal = 2000,
}) {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;

    const pct = Math.min(progress / goal, 1);
    const strokeDashoffset = circumference * (1 - pct);

    return (
        <View style={{ alignItems: "center", justifyContent: "center" }}>
            <Svg width={size} height={size}>
                {/* Background */}
                <Circle
                    stroke="#eee"
                    fill="none"
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                />

                {/* Progress */}
                <Circle
                    stroke="#3b82f6"
                    fill="none"
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                    strokeDasharray={`${circumference} ${circumference}`}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    rotation="-90"
                    origin={`${size / 2}, ${size / 2}`}
                />
            </Svg>

            {/* Center text */}
            <View style={{ position: "absolute", alignItems: "center" }}>
                <Text style={{ fontSize: 22, fontWeight: "700" }}>
                    {Math.round(progress)}
                </Text>
                <Text style={{ color: "#666" }}>kcal</Text>
            </View>
        </View>
    );
}