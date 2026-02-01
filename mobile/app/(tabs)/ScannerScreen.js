import { useState, useRef } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Modal,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { CameraView, useCameraPermissions } from "expo-camera";

import AsyncStorage from "@react-native-async-storage/async-storage";

// helpers
import {
  getProductFromOpenFoodFacts,
} from "../../src/openfood";
import API from "../../src/api";

export default function ScannerScreen() {
  const [barcode, setBarcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState(null);
  const [matches, setMatches] = useState([]);
  const [scannerOpen, setScannerOpen] = useState(false);
  const [scanned, setScanned] = useState(false);

  const [permission, requestPermission] = useCameraPermissions();

  // -------- Get active user id --------
  async function getUserId() {
    const uid = await AsyncStorage.getItem("user_id");
    if (!uid) {
      throw new Error("user_id not found - setup incomplete");
    }
    return parseInt(uid);
  }

  // -------- Handle barcode scanned from camera --------
  const handleBarcodeScanned = ({ type, data }) => {
    if (scanned) return; // Prevent multiple scans
    setScanned(true);
    setBarcode(data);
    setScannerOpen(false);

    // Auto-lookup after scan
    setTimeout(() => {
      lookupBarcode(data);
    }, 300);
  };

  // -------- Open camera scanner --------
  async function openScanner() {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) {
        Alert.alert(
          "Camera Permission Required",
          "Please enable camera access in your device settings to scan barcodes."
        );
        return;
      }
    }
    setScanned(false);
    setScannerOpen(true);
  }

  // -------- Lookup barcode on OpenFoodFacts --------
  async function lookupBarcode(code) {
    const barcodeToLookup = code || barcode;

    if (!barcodeToLookup) {
      Alert.alert("Enter barcode", "Type, paste, or scan a barcode.");
      return;
    }

    setLoading(true);
    setProduct(null);
    setMatches([]);

    try {
      const p = await getProductFromOpenFoodFacts(barcodeToLookup);

      if (!p) {
        Alert.alert("Not found", "No product found for that barcode.");
        return;
      }

      setProduct({ ...p });
    } catch (err) {
      Alert.alert("Lookup failed", String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  // -------- Find best match in NutriMate DB --------
  async function matchLocal() {
    if (!product) {
      Alert.alert("Nothing to match", "First lookup a product.");
      return;
    }

    const name =
      product.product_name ||
      product.generic_name ||
      product.brands ||
      "";

    if (!name) {
      Alert.alert("No name", "Could not extract product name.");
      return;
    }

    setLoading(true);
    setMatches([]);

    try {
      const clean = name.split(",")[0].slice(0, 40);
      console.log("[Scanner] searching NutriMate for:", clean);
      const results = await API.searchFoods(clean);
      setMatches(results || []);
    } catch (err) {
      Alert.alert("Match failed", String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  // -------- Add matched food to log --------
  async function addMatchToLog(food) {
    try {
      const uid = await getUserId();
      await API.addFoodLog({
        user_id: uid,
        food_id: food.food_id,
        quantity: 1,
      });
      Alert.alert("Saved", `${food.food_name} added to your log.`);
    } catch (err) {
      Alert.alert("Save failed", String(err?.message || err));
    }
  }

  return (
    <SafeAreaView style={{ flex: 1 }}>
      {/* Camera Scanner Modal */}
      <Modal visible={scannerOpen} animationType="slide">
        <SafeAreaView style={styles.cameraContainer}>
          <View style={styles.cameraHeader}>
            <Text style={styles.cameraTitle}>Scan Barcode</Text>
            <TouchableOpacity
              style={styles.closeBtn}
              onPress={() => setScannerOpen(false)}
            >
              <Text style={styles.closeBtnText}>✕</Text>
            </TouchableOpacity>
          </View>

          <CameraView
            style={styles.camera}
            facing="back"
            barcodeScannerSettings={{
              barcodeTypes: [
                "ean13",
                "ean8",
                "upc_a",
                "upc_e",
                "code128",
                "code39",
                "code93",
              ],
            }}
            onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
          />

          <View style={styles.scanOverlay}>
            <View style={styles.scanFrame} />
          </View>

          <Text style={styles.cameraHint}>
            Point camera at barcode
          </Text>
        </SafeAreaView>
      </Modal>

      <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
        <Text style={styles.h}>Barcode Scanner</Text>

        {/* Scan Button */}
        <TouchableOpacity style={styles.scanBtn} onPress={openScanner}>
          <Text style={styles.scanBtnText}>📷 Scan with Camera</Text>
        </TouchableOpacity>

        <Text style={styles.orText}>— or enter manually —</Text>

        <TextInput
          value={barcode}
          onChangeText={setBarcode}
          placeholder="Enter barcode (e.g. 3017620422003)"
          keyboardType="default"
          style={styles.input}
        />

        <TouchableOpacity style={styles.btn} onPress={() => lookupBarcode()}>
          <Text style={styles.btnText}>Lookup</Text>
        </TouchableOpacity>

        {loading && <ActivityIndicator style={{ marginTop: 16 }} />}

        {product && (
          <View style={styles.card}>
            <Text style={styles.title}>{product.product_name || "Unnamed product"}</Text>

            {product.brands && <Text style={styles.sub}>{product.brands}</Text>}
            {product.serving_size && (
              <Text style={styles.meta}>Serving: {product.serving_size}</Text>
            )}

            <Text style={{ marginTop: 8, fontWeight: "600" }}>Nutrients (per 100g)</Text>

            {Object.entries(product.nutrients_per_100g || {}).map(([k, v]) => (
              <Text key={k}>
                {k}: {v === null ? "—" : v}
              </Text>
            ))}

            {product.nutrients_per_serving && (
              <>
                <Text style={{ marginTop: 8, fontWeight: "600" }}>
                  Estimated per serving
                </Text>

                {Object.entries(product.nutrients_per_serving).map(([k, v]) => (
                  <Text key={k}>
                    {k}: {v === null ? "—" : v}
                  </Text>
                ))}
              </>
            )}

            <TouchableOpacity style={[styles.btn, { marginTop: 12 }]} onPress={matchLocal}>
              <Text style={styles.btnText}>Find best match in NutriMate DB</Text>
            </TouchableOpacity>
          </View>
        )}

        {matches.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.title}>Matches from local DB</Text>

            {matches.map((m) => (
              <View key={m.food_id} style={{ marginVertical: 8 }}>
                <Text style={{ fontWeight: "600" }}>
                  {m.food_name} ({m.source})
                </Text>

                <Text>
                  kcal: {m.Calories_kcal ?? "NA"} • protein: {m.Protein_g ?? "NA"}
                </Text>

                <TouchableOpacity
                  style={styles.smallBtn}
                  onPress={() => addMatchToLog(m)}
                >
                  <Text style={styles.smallBtnText}>Add to log</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  h: { fontSize: 22, fontWeight: "700", marginBottom: 16 },

  // Camera styles
  cameraContainer: { flex: 1, backgroundColor: "#000" },
  cameraHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#000",
  },
  cameraTitle: { color: "#fff", fontSize: 18, fontWeight: "600" },
  closeBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
    alignItems: "center",
  },
  closeBtnText: { color: "#fff", fontSize: 20 },
  camera: { flex: 1 },
  scanOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    pointerEvents: "none",
  },
  scanFrame: {
    width: 280,
    height: 150,
    borderWidth: 3,
    borderColor: "#4CAF50",
    borderRadius: 12,
    backgroundColor: "transparent",
  },
  cameraHint: {
    textAlign: "center",
    color: "#fff",
    padding: 16,
    backgroundColor: "#000",
    fontSize: 16,
  },

  // Scan button
  scanBtn: {
    backgroundColor: "#4CAF50",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginBottom: 12,
  },
  scanBtnText: { color: "#fff", fontWeight: "700", fontSize: 16 },

  orText: {
    textAlign: "center",
    color: "#888",
    marginVertical: 12,
  },

  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  btn: {
    backgroundColor: "#1976D2",
    padding: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  btnText: { color: "white", fontWeight: "600" },
  card: {
    marginTop: 16,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#eee",
  },
  title: { fontSize: 16, fontWeight: "700" },
  sub: { color: "#666" },
  meta: { color: "#444", marginTop: 4 },
  smallBtn: {
    marginTop: 6,
    backgroundColor: "#4CAF50",
    padding: 8,
    borderRadius: 8,
    alignSelf: "flex-start",
  },
  smallBtnText: { color: "white" },
});
