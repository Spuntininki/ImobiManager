import { createContext, useContext, useEffect, useState } from "react";

import { getMe, login as loginRequest } from "@/services/authService";
import { clearToken, getToken, setToken } from "@/lib/auth";

interface AuthContextType {
  userName: string | null;
  email: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<unknown>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [email, setEmail] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);

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

    getMe()
      .then((me) => {
        setUserName(me.user_name);
        setEmail(me.email);
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

  const login = async (email: string, password: string) => {
    const data = await loginRequest(email, password);
    setToken(data.access_token);
    // Fetch the profile from /auth/me so login and page refresh share one
    // single source of truth for the user's name/email.
    const me = await getMe();
    setUserName(me.user_name);
    setEmail(me.email);
    setIsAuthenticated(true);
    return data;
  };

  const logout = () => {
    clearToken();
    setIsAuthenticated(false);
    setEmail(null);
  };

  const value: AuthContextType = {
    userName,
    email,
    isAuthenticated,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
