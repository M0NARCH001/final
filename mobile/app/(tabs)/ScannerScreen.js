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
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

// helpers (your existing module)
import {
  addFoodLog,
  findLocalFoods,
  getProductFromOpenFoodFacts,
} from "../../src/openfood";

export default function ScannerScreen() {
  const [barcode, setBarcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState(null);
  const [matches, setMatches] = useState([]);

  // -------- Lookup barcode on OpenFoodFacts --------
  async function lookup() {
    if (!barcode) {
      Alert.alert("Enter barcode", "Type or paste the barcode number and press Lookup.");
      return;
    }

    setLoading(true);
    setProduct(null);
    setMatches([]);

    try {
      const p = await getProductFromOpenFoodFacts(barcode);

      if (!p) {
        Alert.alert("Not found", "No product found for that barcode.");
        return;
      }

      // force new object for Android re-render
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
      // keep query short to avoid slow LIKE searches
      const clean = name.split(",")[0].slice(0, 40);

      console.log("[Scanner] searching NutriMate for:", clean);

      const results = await findLocalFoods(clean);
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
      await addFoodLog({
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
      <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
        <Text style={styles.h}>Barcode lookup (OpenFoodFacts)</Text>

        <TextInput
          value={barcode}
          onChangeText={setBarcode}
          placeholder="Enter or paste barcode (e.g. 3017620422003)"
          keyboardType="default"
          style={styles.input}
        />

        <TouchableOpacity style={styles.btn} onPress={lookup}>
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
  h: { fontSize: 20, fontWeight: "700", marginBottom: 12 },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    padding: 10,
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
