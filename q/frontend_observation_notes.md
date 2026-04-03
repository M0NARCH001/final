# NutriMate v2: Frontend Architecture & Design Observation

## 1. Technology Stack
**Core Framework**:
- **React Native** (v0.81.5): Core mobile framework
- **Expo SDK** (v54): Managed workflow for easier development and build
- **React** (v19): UI library with functional components and hooks

**Key Libraries**:
- **Navigation**: `expo-router` (v6) - File-based routing (similar to Next.js)
- **Storage**: `@react-native-async-storage/async-storage` - Local persistent data
- **Graphics**: `react-native-svg` - For drawing charts (Calorie Progress Circle)
- **Hardware**: `expo-camera` - Accessing device camera for barcode scanning
- **Gestures**: `react-native-gesture-handler` - Smooth touch interactions
- **Safe Area**: `react-native-safe-area-context` - Handling notches and dynamic islands

## 2. Design System & UI/UX

### 2.1 Color Palette
The app uses a consistent, functional color scheme inspired by **Material Design**:
- **Primary Brand**: `#1A73E8` (Google Blue) - Used for buttons, active states, and links.
- **Backgrounds**:
  - Main: `#ffffff` (White)
  - Cards: `#f6f7fb` (Light Blue/Grey) - Distinguishes content sections
  - Inputs/Checkboxes: `#f8f8f8`
- **Functional Colors**:
  - **Protein**: `#22c55e` (Green)
  - **Carbs**: `#3b82f6` (Blue)
  - **Fat**: `#f59e0b` (Amber/Orange)
  - **Fiber**: `#10b981` (Teal)
  - **Sodium**: `#ef4444` (Red) - Indicates caution
  - **Iron**: `#8b5cf6` (Purple)
  - **Calcium**: `#06b6d4` (Cyan)
- **Status Colors**:
  - **Warning**: `#fff3cd` (Yellow bg) with `#856404` (Brown text)
  - **Info**: `#d1ecf1` (Blue bg) with `#0c5460` (Dark Blue text)

### 2.2 Typography
- **Headings**: Bold (`fontWeight: "700"`), typically 22px (`h1`) and 18px (`h2`) for hierarchy.
- **Body**: Regular sans-serif system fonts (`fontSize: 14-15px`).
- **Labels**: Slightly smaller (`fontSize: 13px`), muted colors (`#666666`) for secondary information.

### 2.3 Layout Patterns
- **Safe Area**: All screens wrapped in `SafeAreaView` to prevent overlap with status bars/notches.
- **Card-based Design**: Dashboard segments (Macros, Micros) grouped in rounded cards (`borderRadius: 12`, `padding: 14`).
- **Scrollable Content**: `ScrollView` used for main screens to handle dynamic height; `FlatList` used for long lists (search results) for performance.
- **Chips & Pills**: Filter selections (Gender, Activity Level) use pill-shaped touchables (`borderRadius: 16`) that toggle color on active state.

## 3. Component Architecture

### 3.1 Screen Structure
The app follows a flat hierarchy managed by `expo-router`:
- **`app/_layout.tsx`**: Root layout definition (Stack navigator).
- **`app/setup.js`**: Standalone onboarding screen.
- **`app/(tabs)/`**: directory for tab-based main navigation:
  - **`index.js`**: Dashboard/Home screen.
  - **`FoodLogScreen.js`**: Search and log interface.
  - **`ScannerScreen.js`**: Camera interface.
  - **`RecommendScreen.js`**: Suggestions interface.

### 3.2 Key Reusable Components
1. **`ProgressBar`** (in `index.js`):
   - **Props**: `label`, `value`, `target`, `color`
   - **Logic**: Calculates percentage `Math.min(100, (value/target)*100)`
   - **Render**: Renders a label row and a background track with a colored fill bar.

2. **`CalorieProgressCircle`**:
   - Uses `react-native-svg` to draw a circular progress ring.
   - likely accepts `progress` and `goal` to calculate stroke dashoffset.

3. **`WarningBadge`**:
   - **Props**: `warning` object (`severity`, `message`)
   - **Logic**: Conditionally selects background/text color based on severity.
   - **Render**: Simple rounded container with icon and text.

## 4. State Management Strategy

### 4.1 Local Component State (`useState`)
- Used for UI state like `loading`, `query` (search text), `results` (list data).
- **Example**: `const [loading, setLoading] = useState(true)` in `Home`.

### 4.2 Application State (`AsyncStorage`)
- **Persistence**: User session and profile data survive app restarts.
- **Key Stores**:
  - `user_id`: Integer ID for API requests.
  - `nutrimate_goals`: JSON string containing BMR, TDEE, and macro targets.
  - `nutrimate_profile`: JSON string with raw inputs (age, weight etc).

### 4.3 Data Fetching & Sync
- **Hooks**: `useEffect` for initial load, `useFocusEffect` (React Navigation) for re-fetching data when returning to a screen.
- **Pattern**: "Fetch-on-focus" ensures the Dashboard updates immediately after a user logs food in the Log screen.

## 5. Integration Points

### 5.1 API Client (`src/api.js`)
- **Wrapper**: `API` object wraps `fetch` calls.
- **Environment Aware**: Automatically selects `localhost` (dev) or production URL (`expo-constants`).
- **Methods**: `getTodayLogs`, `getDailySummary`, `searchFoods`.

### 5.2 Device Integrations
- **Camera**: integrated via `expo-camera` in `ScannerScreen`. Handles permission requests (`useCameraPermissions`).
- **Keyboard**: Handled via `TouchableWithoutFeedback` and `Keyboard.dismiss()` to improve form usability.

## 6. Development Workflow Observations
- **Linting**: `eslint` with `eslint-config-expo`.
- **Types**: Project allows TypeScript (`.tsx`) but codebase is primarily JavaScript (`.js`), showing a transition or mixed usage.
- **Assets**: Uses `expo-vector-icons` for lightweight UI iconography (warnings, navigation).

## 7. Frontend Code Quality
- **Modularization**: Styles separated into `StyleSheet.create` blocks at bottom of files.
- **Efficiency**: Use of `FlatList` for lists ensures memory efficiency.
- **Responsiveness**: Flexbox layout used throughout (`flex: 1`, `flexDirection: "row"`) ensures scaling across screen sizes.
- **Feedback**: `ActivityIndicator` used during async operations to indicate loading state.
