import { useState } from "react";
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

import { getProductFromOpenFoodFacts } from "../../src/openfood";
import API from "../../src/api";

// Barcode types for each scan mode
const BARCODE_TYPES = ["ean13", "ean8", "upc_a", "upc_e", "code128", "code39", "code93"];
const QR_TYPES = ["qr"];

export default function ScannerScreen() {
  const [barcode, setBarcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState(null);
  const [matches, setMatches] = useState([]);
  const [noMatch, setNoMatch] = useState(false);
  const [searchedName, setSearchedName] = useState("");
  const [scannerOpen, setScannerOpen] = useState(false);
  const [scanned, setScanned] = useState(false);
  const [scanMode, setScanMode] = useState("barcode"); // "barcode" | "qr"

  const [permission, requestPermission] = useCameraPermissions();

  async function getUserId() {
    const uid = await AsyncStorage.getItem("user_id");
    if (!uid) throw new Error("user_id not found — complete setup first");
    return parseInt(uid);
  }

  // ── Camera scan handler ──────────────────────────────────────────────────────
  const handleBarcodeScanned = ({ type, data }) => {
    if (scanned) return;
    setScanned(true);
    setScannerOpen(false);

    // For QR codes, the data might be a URL or a plain barcode/identifier
    const resolved = extractIdentifier(data);
    setBarcode(resolved);

    setTimeout(() => lookupBarcode(resolved), 300);
  };

  // Extract a usable product identifier from QR data (URL or plain string)
  function extractIdentifier(data) {
    if (!data) return data;
    // If it looks like an OpenFoodFacts URL, pull the barcode from the path
    const offMatch = data.match(/openfoodfacts\.org\/product\/(\d+)/i);
    if (offMatch) return offMatch[1];
    // If it's a pure numeric string (barcode), use as-is
    if (/^\d{6,14}$/.test(data.trim())) return data.trim();
    // Otherwise return raw (could be a URL or text — we'll show the user)
    return data.trim();
  }

  async function openScanner(mode = "barcode") {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) {
        Alert.alert(
          "Camera Permission Required",
          "Enable camera access in your device settings to scan."
        );
        return;
      }
    }
    setScanMode(mode);
    setScanned(false);
    setScannerOpen(true);
  }

  // ── OpenFoodFacts lookup ─────────────────────────────────────────────────────
  async function lookupBarcode(code) {
    const barcodeToLookup = code || barcode;
    if (!barcodeToLookup) {
      Alert.alert("Enter barcode", "Type, paste, or scan a barcode / QR code.");
      return;
    }

    // If the identifier doesn't look numeric (e.g. a non-OF URL), alert the user
    if (!/^\d+$/.test(barcodeToLookup)) {
      Alert.alert(
        "QR Code Scanned",
        `Content: ${barcodeToLookup}\n\nThis QR code doesn't appear to link to a food product.`
      );
      return;
    }

    setLoading(true);
    setProduct(null);
    setMatches([]);
    setNoMatch(false);

    try {
      const p = await getProductFromOpenFoodFacts(barcodeToLookup);
      if (!p) {
        Alert.alert("Not found", "No product found for that barcode.");
        setLoading(false);
        return;
      }
      setProduct({ ...p });
      // Auto-search NutriMate DB immediately after product found
      await matchLocalWithProduct(p);
    } catch (err) {
      Alert.alert("Lookup failed", String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  // ── Match against NutriMate DB (accepts product directly for auto-search) ───
  async function matchLocalWithProduct(p) {
    const name = p?.product_name || p?.generic_name || p?.brands || "";
    if (!name) return;

    const clean = name.split(",")[0].slice(0, 40);
    setSearchedName(clean);
    try {
      const results = await API.searchFoods(clean);
      if (!results || results.length === 0) {
        setNoMatch(true);
      } else {
        setMatches(results);
      }
    } catch (err) {
      console.warn("[Scanner] Local match failed:", err.message);
    }
  }

  async function matchLocal() {
    if (!product) {
      Alert.alert("Nothing to match", "First lookup a product.");
      return;
    }
    setLoading(true);
    setMatches([]);
    setNoMatch(false);
    try {
      await matchLocalWithProduct(product);
    } catch (err) {
      Alert.alert("Match failed", String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  // ── Add scanned product (new) to DB and log ──────────────────────────────────
  async function addToDbAndLog() {
    if (!product) {
      Alert.alert("No product", "Scan a product first.");
      return;
    }
    setLoading(true);
    try {
      const uid = await getUserId();
      const nutrients = product.nutrients_per_100g || {};
      const result = await API.createFoodAndLog({
        food_name: product.product_name || product.brands || "Unknown Product",
        source: "OpenFoodFacts",
        is_vegetarian: null, // unknown from barcode scan
        Calories_kcal: nutrients.Calories_kcal,
        Protein_g: nutrients.Protein_g,
        Carbohydrates_g: nutrients.Carbohydrates_g,
        Fats_g: nutrients.Fats_g,
        FreeSugar_g: nutrients.FreeSugar_g,
        Fibre_g: nutrients.Fibre_g,
        Sodium_mg: nutrients.Sodium_mg,
        Calcium_mg: nutrients.Calcium_mg,
        Iron_mg: nutrients.Iron_mg,
        VitaminC_mg: nutrients.VitaminC_mg,
        Folate_ug: nutrients.Folate_ug,
        serving_size: product.serving_size,
        user_id: uid,
        quantity: 1,
        unit: "serving",
      });
      Alert.alert(
        "Added & Logged",
        `"${result.food_name}" saved to your food database and logged.`
      );
      setNoMatch(false);
      setProduct(null);
      setBarcode("");
      setMatches([]);
    } catch (err) {
      Alert.alert("Failed", String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  // ── Log an existing matched food ─────────────────────────────────────────────
  async function addMatchToLog(food) {
    try {
      const uid = await getUserId();
      await API.addFoodLog({ user_id: uid, food_id: food.food_id, quantity: 1 });
      Alert.alert("Logged", `${food.food_name} added to today's log.`);
    } catch (err) {
      Alert.alert("Save failed", String(err?.message || err));
    }
  }

  const isQR = scanMode === "qr";

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#fff" }}>
      {/* ── Camera Modal ────────────────────────────────────────────── */}
      <Modal visible={scannerOpen} animationType="slide">
        <SafeAreaView style={styles.cameraContainer}>
          <View style={styles.cameraHeader}>
            <Text style={styles.cameraTitle}>
              {isQR ? "Scan QR Code" : "Scan Barcode"}
            </Text>
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
              barcodeTypes: isQR ? QR_TYPES : BARCODE_TYPES,
            }}
            onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
          />

          {/* Scan frame overlay — does not intercept touches */}
          <View pointerEvents="none" style={styles.scanOverlay}>
            <View style={isQR ? styles.scanFrameQR : styles.scanFrameBarcode} />
          </View>

          <Text style={styles.cameraHint}>
            {isQR
              ? "Point camera at QR code"
              : "Point camera at barcode"}
          </Text>
        </SafeAreaView>
      </Modal>

      {/* ── Main Screen ─────────────────────────────────────────────── */}
      <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
        <Text style={styles.h}>Scan Food</Text>

        {/* Mode toggle */}
        <View style={styles.modeRow}>
          <TouchableOpacity
            style={[styles.modeBtn, scanMode === "barcode" && styles.modeBtnActive]}
            onPress={() => setScanMode("barcode")}
          >
            <Text style={scanMode === "barcode" ? styles.modeBtnTextActive : styles.modeBtnText}>
              Barcode
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeBtn, scanMode === "qr" && styles.modeBtnActive]}
            onPress={() => setScanMode("qr")}
          >
            <Text style={scanMode === "qr" ? styles.modeBtnTextActive : styles.modeBtnText}>
              QR Code
            </Text>
          </TouchableOpacity>
        </View>

        {/* Camera open button */}
        <TouchableOpacity
          style={styles.scanBtn}
          onPress={() => openScanner(scanMode)}
        >
          <Text style={styles.scanBtnText}>
            {scanMode === "qr" ? "Scan QR Code" : "Scan Barcode"}
          </Text>
        </TouchableOpacity>

        <Text style={styles.orText}>— or enter barcode manually —</Text>

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

        {/* Product info */}
        {product && (
          <View style={styles.card}>
            <Text style={styles.title}>{product.product_name || "Unnamed product"}</Text>
            {product.brands && <Text style={styles.sub}>{product.brands}</Text>}
            {product.serving_size && (
              <Text style={styles.meta}>Serving: {product.serving_size}</Text>
            )}

            <Text style={styles.sectionLabel}>Nutrients (per 100g)</Text>
            {Object.entries(product.nutrients_per_100g || {}).map(([k, v]) => (
              <Text key={k} style={styles.nutrientRow}>
                {k.replace(/_/g, " ")}: {v === null ? "—" : v}
              </Text>
            ))}

            {matches.length === 0 && !noMatch && (
              <TouchableOpacity style={[styles.btn, { marginTop: 12 }]} onPress={matchLocal}>
                <Text style={styles.btnText}>Search in NutriMate DB</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Local DB matches */}
        {matches.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.title}>Matches in NutriMate DB</Text>
            {matches.map((m) => (
              <View key={m.food_id} style={styles.matchRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.matchName}>{m.food_name}</Text>
                  <View style={styles.matchMeta}>
                    {m.is_vegetarian === true && (
                      <View style={styles.vegBadge}>
                        <Text style={styles.vegBadgeText}>VEG</Text>
                      </View>
                    )}
                    {m.is_vegetarian === false && (
                      <View style={[styles.vegBadge, styles.nonVegBadge]}>
                        <Text style={styles.vegBadgeText}>NON-VEG</Text>
                      </View>
                    )}
                    <Text style={styles.matchNutrients}>
                      {m.Calories_kcal ?? "—"} kcal · {m.Protein_g ?? "—"}g protein
                    </Text>
                  </View>
                </View>
                <TouchableOpacity
                  style={styles.logBtn}
                  onPress={() => addMatchToLog(m)}
                >
                  <Text style={styles.logBtnText}>Log</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* No match — offer to import from OpenFoodFacts */}
        {noMatch && (
          <View style={styles.card}>
            <Text style={styles.title}>Not in NutriMate DB</Text>
            <Text style={styles.sub}>"{searchedName}" was not found locally.</Text>
            <Text style={styles.hint}>
              Import from OpenFoodFacts and log it now.
            </Text>
            <TouchableOpacity
              style={[styles.btn, { marginTop: 12, backgroundColor: "#2E7D32" }]}
              onPress={addToDbAndLog}
            >
              <Text style={styles.btnText}>Import & Log</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  h: { fontSize: 22, fontWeight: "700", marginBottom: 12 },

  // Mode toggle
  modeRow: { flexDirection: "row", marginBottom: 12, gap: 8 },
  modeBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ddd",
    alignItems: "center",
  },
  modeBtnActive: { borderColor: "#1565C0", backgroundColor: "#E3F2FD" },
  modeBtnText: { color: "#555", fontWeight: "500" },
  modeBtnTextActive: { color: "#1565C0", fontWeight: "700" },

  // Scan button
  scanBtn: {
    backgroundColor: "#1565C0",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginBottom: 12,
  },
  scanBtnText: { color: "#fff", fontWeight: "700", fontSize: 16 },

  orText: { textAlign: "center", color: "#888", marginVertical: 10 },

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
  btnText: { color: "#fff", fontWeight: "600" },

  // Camera
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
    top: 0, left: 0, right: 0, bottom: 0,
    justifyContent: "center",
    alignItems: "center",
  },
  scanFrameBarcode: {
    width: 280,
    height: 130,
    borderWidth: 3,
    borderColor: "#4CAF50",
    borderRadius: 10,
    backgroundColor: "transparent",
  },
  scanFrameQR: {
    width: 220,
    height: 220,
    borderWidth: 3,
    borderColor: "#FF9800",
    borderRadius: 10,
    backgroundColor: "transparent",
  },
  cameraHint: {
    textAlign: "center",
    color: "#fff",
    padding: 16,
    backgroundColor: "#000",
    fontSize: 15,
  },

  // Cards
  card: {
    marginTop: 16,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    backgroundColor: "#fafafa",
  },
  title: { fontSize: 16, fontWeight: "700", marginBottom: 2 },
  sub: { color: "#666", marginBottom: 4 },
  meta: { color: "#444", marginTop: 4 },
  hint: { color: "#666", marginTop: 6, fontSize: 13 },
  sectionLabel: { fontWeight: "600", marginTop: 10, marginBottom: 4 },
  nutrientRow: { color: "#333", fontSize: 13, lineHeight: 20 },

  // Match rows
  matchRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
    gap: 8,
  },
  matchName: { fontWeight: "600", fontSize: 14 },
  matchMeta: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 2 },
  matchNutrients: { color: "#555", fontSize: 12 },
  vegBadge: {
    backgroundColor: "#4CAF50",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  nonVegBadge: { backgroundColor: "#F44336" },
  vegBadgeText: { color: "#fff", fontSize: 10, fontWeight: "700" },
  logBtn: {
    backgroundColor: "#4CAF50",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  logBtnText: { color: "#fff", fontWeight: "600" },
});
