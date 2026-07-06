import { createContext, useContext, useEffect, useState } from "react";

import api from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [email, setEmail] = useState(null);
  const [userName, setUserName] = useState(null);

  // On mount, treat a stored token as a session. The API will reject it
  // via the axios 401 interceptor if it's invalid/expired, which clears
  // the token and flips isAuthenticated back to false.
  useEffect(() => {
    setIsAuthenticated(!!getToken());
    setIsLoading(false);
  }, []);

  const login = async (email, password) => {
    const resp = await api.post("/auth/login", { email, password });
    setUserName(resp.data.user_name)
    setToken(resp.data.access_token);
    setIsAuthenticated(true);
    setEmail(email);
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