/**
 * frontend/src/App.jsx
 * Application router and top-level provider setup.
 * Supported routes: /login, /register, /, /redeem, /quiz/:id, /result/:id, /badges, /history, /settings, /change-pin.
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SessionProvider } from "./session.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import PublicOnlyRoute from "./components/PublicOnlyRoute.jsx";
import AppLayout from "./components/AppLayout.jsx";

import LoginScreen from "./screens/LoginScreen.jsx";
import RegisterScreen from "./screens/RegisterScreen.jsx";
import ChangePinScreen from "./screens/ChangePinScreen.jsx";
import HomeScreen from "./screens/HomeScreen.jsx";
import RedeemScreen from "./screens/RedeemScreen.jsx";
import QuizScreen from "./screens/QuizScreen.jsx";
import ResultScreen from "./screens/ResultScreen.jsx";
import BadgesScreen from "./screens/BadgesScreen.jsx";
import HistoryScreen from "./screens/HistoryScreen.jsx";
import SettingsScreen from "./screens/SettingsScreen.jsx";

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <LoginScreen />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnlyRoute>
                <RegisterScreen />
              </PublicOnlyRoute>
            }
          />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/change-pin" element={<ChangePinScreen />} />

            <Route element={<AppLayout />}>
              <Route path="/" element={<HomeScreen />} />
              <Route path="/redeem" element={<RedeemScreen />} />
              <Route path="/quiz/:id" element={<QuizScreen />} />
              <Route path="/result/:id" element={<ResultScreen />} />
              <Route path="/badges" element={<BadgesScreen />} />
              <Route path="/history" element={<HistoryScreen />} />
              <Route path="/settings" element={<SettingsScreen />} />
            </Route>
          </Route>

          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
}
