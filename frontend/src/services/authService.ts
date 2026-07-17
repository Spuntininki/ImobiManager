import api from "@/lib/api";

// --- Auth ---

export async function login(
  email: string,
  password: string,
): Promise<{ access_token: string }> {
  const resp = await api.post("/auth/login", { email, password });
  return resp.data;
}

export async function getMe(): Promise<{
  email: string;
  user_name: string;
}> {
  const resp = await api.get("/auth/me");
  return resp.data;
}
