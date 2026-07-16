import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Navbar } from "@/components/layout/Navbar";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ContractsPage } from "@/contracts/ContractsPage";
import { DashboardPage } from "@/dashboard/DashboardPage";
import { Login } from "@/pages/Login";
import { PropertiesPage } from "@/properties/PropertiesPage";
import { SettingsPage } from "@/settings/SettingsPage";
import { TenantsPage } from "@/tenants/TenantsPage";

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/properties" element={<PropertiesPage />} />
          <Route path="/tenants" element={<TenantsPage />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;