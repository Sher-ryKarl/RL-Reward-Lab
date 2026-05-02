import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainLayout } from "./components/Layout/MainLayout";
import { ExperimentListPage } from "./pages/ExperimentListPage";
import { NewExperimentPage } from "./pages/NewExperimentPage";
import { ExperimentDetailPage } from "./pages/ExperimentDetailPage";
import { DemoListPage } from "./pages/DemoListPage";
import { CompareView } from "./components/CompareView/CompareView";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { useAuthStore } from "./stores/authStore";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<ExperimentListPage />} />
            <Route path="/new" element={<NewExperimentPage />} />
            <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
            <Route path="/demos" element={<DemoListPage />} />
            <Route path="/compare" element={<CompareView />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
