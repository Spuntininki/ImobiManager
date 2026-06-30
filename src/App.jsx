import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Navbar } from "@/components/layout/Navbar";
import { Contracts } from "@/pages/Contracts";
import { Dashboard } from "@/pages/Dashboard";
import { Properties } from "@/pages/Properties";
import { Tenants } from "@/pages/Tenants";

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/properties" element={<Properties />} />
            <Route path="/tenants" element={<Tenants />} />
            <Route path="/contracts" element={<Contracts />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
