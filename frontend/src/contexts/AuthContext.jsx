import { createContext, useContext, useEffect, useState } from "react";

import api from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [email, setEmail] = useState(null);
  const [userName, setUserName] = useState(null);

  // Validate the stored token via /auth/me and rehydrate the in-memory
  // profile (user name, email). If the token is invalid/expired, the
  // backend returns 401, the axios interceptor clears the token, and we
  // flip to logged-out. isLoading stays true until the call settles so
  // AppRoutes doesn't flash the Login page on refresh.
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      setIsAuthenticated(false);
      return;
    }

    api
      .get("/auth/me")
      .then((resp) => {
        setUserName(resp.data.user_name);
        setEmail(resp.data.email);
        setIsAuthenticated(true);
      })
      .catch(() => {
        // 401 interceptor already cleared the token; ensure logged-out state.
        setUserName(null);
        setEmail(null);
        setIsAuthenticated(false);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email, password) => {
    const resp = await api.post("/auth/login", { email, password });
    setToken(resp.data.access_token);
    // Fetch the profile from /auth/me so login and page refresh share one
    // single source of truth for the user's name/email.
    const me = await api.get("/auth/me");
    setUserName(me.data.user_name);
    setEmail(me.data.email);
    setIsAuthenticated(true);
    return resp.data;
  };

  const logout = () => {
    clearToken();
    setIsAuthenticated(false);
    setEmail(null);
  };

  const value = {
    userName,
    email,
    isAuthenticated,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}