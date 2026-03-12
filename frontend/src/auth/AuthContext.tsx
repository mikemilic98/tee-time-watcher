import axios from "axios";
import React, { createContext, useContext, useEffect, useState } from "react";

interface User {
  id: number;
  email: string;
  priority_tier: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    const storedUser = localStorage.getItem("auth_user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      axios.defaults.headers.common.Authorization = `Bearer ${storedToken}`;
    }
  }, []);

  const login = async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const tokenRes = await axios.post("/auth/token", form);
    const accessToken: string = tokenRes.data.access_token;
    axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
    setToken(accessToken);
    localStorage.setItem("auth_token", accessToken);

    // For now, decode user by calling a simple /me endpoint would be ideal.
    // As a placeholder, we store email only.
    const meRes = await axios.get<User>("/me");
    setUser(meRes.data);
    localStorage.setItem("auth_user", JSON.stringify(meRes.data));
  };

  const register = async (email: string, password: string) => {
    await axios.post("/auth/register", { email, password });
    await login(email, password);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    delete axios.defaults.headers.common.Authorization;
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
};

