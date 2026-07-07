import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Navbar } from "@/components/layout/Navbar";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { Contracts } from "@/pages/Contracts";
import { Dashboard } from "@/pages/Dashboard";
import { Login } from "@/pages/Login";
import { Properties } from "@/pages/Properties";
import { Settings } from "@/pages/Settings";
import { Tenants } from "@/pages/Tenants";

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
          <Route path="/" element={<Dashboard />} />
          <Route path="/properties" element={<Properties />} />
          <Route path="/tenants" element={<Tenants />} />
          <Route path="/contracts" element={<Contracts />} />
          <Route path="/settings" element={<Settings />} />
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
