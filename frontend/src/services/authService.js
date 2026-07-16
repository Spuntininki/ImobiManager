import api from "@/lib/api";

// --- Auth ---

export async function login(email, password) {
  const resp = await api.post("/auth/login", { email, password });
  return resp.data;
}

export async function getMe() {
  const resp = await api.get("/auth/me");
  return resp.data;
}