import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PublicRoute } from "./components/PublicRoute";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { GoogleCallback } from "./pages/GoogleCallback";
import Dashboard from "./pages/Dashboard";
import Results from "./pages/Results";
import { SubmitIdea } from "./pages/SubmitIdea";
import { IdeaDetail } from "./pages/IdeaDetail";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
          <Route path="/auth/callback" element={<PublicRoute><GoogleCallback /></PublicRoute>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/projects/new" element={<Navigate to="/ideas/new" replace />} />
          <Route
            path="/ideas/new"
            element={
              <ProtectedRoute>
                <SubmitIdea />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ideas/:id"
            element={
              <ProtectedRoute>
                <IdeaDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
