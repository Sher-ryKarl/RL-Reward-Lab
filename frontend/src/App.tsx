import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainLayout } from "./components/Layout/MainLayout";
import { ExperimentListPage } from "./pages/ExperimentListPage";
import { NewExperimentPage } from "./pages/NewExperimentPage";
import { ExperimentDetailPage } from "./pages/ExperimentDetailPage";
import { DemoListPage } from "./pages/DemoListPage";
import { CompareView } from "./components/CompareView/CompareView";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
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
