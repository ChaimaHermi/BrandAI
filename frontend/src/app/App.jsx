import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { PublicRoute } from "@/components/PublicRoute";
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import { GoogleCallback } from "@/pages/GoogleCallback";
import DashboardPage from "@/pages/DashboardPage";
import ResultsPage from "@/pages/ResultsPage";
import SubmitIdeaPage from "@/pages/SubmitIdeaPage";
import IdeaPage from "@/pages/IdeaPage";
import PipelineLayout from "@/app/layout/PipelineLayout";
import ClarifierPage from "@/agents/clarifier/pages/ClarifierPage";
import MarketPage from "@/agents/market/pages/MarketPage";

function PlaceholderPage({ name }) {
  return (
    <div
      style={{
        background: "white",
        border: "0.5px solid #e8e4ff",
        borderRadius: 14,
        padding: "40px 24px",
        textAlign: "center",
        boxShadow: "0 2px 8px rgba(124,58,237,0.04)",
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: "50%",
          background: "#f0eeff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 16px",
        }}
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M10 4v8M10 14v.5"
            stroke="#7F77DD"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div
        style={{
          fontSize: 15,
          fontWeight: 700,
          color: "#1a1040",
          marginBottom: 8,
        }}
      >
        {name}
      </div>
      <div
        style={{
          fontSize: 13,
          color: "#9ca3af",
        }}
      >
        Cet agent sera disponible dans le Sprint 2
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<PublicRoute><LandingPage /></PublicRoute>} />
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
          <Route path="/auth/callback" element={<PublicRoute><GoogleCallback /></PublicRoute>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="/projects/new" element={<Navigate to="/ideas/new" replace />} />
          <Route
            path="/ideas/new"
            element={
              <ProtectedRoute>
                <SubmitIdeaPage />
              </ProtectedRoute>
            }
          />
          {/* Redirection legacy vers la nouvelle structure de pipeline */}
          <Route
            path="/ideas/:id"
            element={
              <ProtectedRoute>
                <IdeaPage />
              </ProtectedRoute>
            }
          />
          {/* Pipeline multi-agents */}
          <Route
            path="/ideas/:id/*"
            element={
              <ProtectedRoute>
                <PipelineLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="clarifier" replace />} />
            <Route path="clarifier" element={<ClarifierPage />} />
            <Route
              path="market"
              element={<MarketPage />}
            />
            <Route
              path="brand"
              element={<PlaceholderPage name="Brand Identity" />}
            />
            <Route
              path="content"
              element={<PlaceholderPage name="Content Creator" />}
            />
            <Route
              path="website"
              element={<PlaceholderPage name="Website Builder" />}
            />
            <Route
              path="optimizer"
              element={<PlaceholderPage name="Optimizer" />}
            />
          </Route>
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <ResultsPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

