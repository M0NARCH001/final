import { Stack } from "expo-router";
import { useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function RootLayout() {
  const [ready, setReady] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    (async () => {
      const p = await AsyncStorage.getItem("nutrimate_profile");
      setHasProfile(!!(p && p.length > 10));
      setReady(true);
    })();
  }, []);

  if (!ready) return null;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      {!hasProfile && <Stack.Screen name="profile" />}
      <Stack.Screen name="(tabs)" />
    </Stack>
  );
}
