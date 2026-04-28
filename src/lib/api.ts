// API client for the Seven1tel admin panel.
// Configure VITE_API_BASE in .env (e.g. https://tg.nexus-x.site/api). Falls back to "/api".

const BASE = (import.meta.env.VITE_API_BASE as string) || "/api";

export function token(): string | null {
  return localStorage.getItem("token");
}
export function setToken(t: string | null) {
  if (t) localStorage.setItem("token", t);
  else localStorage.removeItem("token");
}

async function req<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init.headers as Record<string, string>) || {}),
  };
  const t = token();
  if (t) headers["Authorization"] = `Bearer ${t}`;
  const res = await fetch(BASE + path, { ...init, headers });
  if (res.status === 401) {
    setToken(null);
    if (location.pathname !== "/login") location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = j.detail || j.message || msg;
    } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    req<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  dashboard: () => req<any>("/dashboard"),
  settings: {
    list: () => req<Record<string, any>>("/settings"),
    set: (key: string, value: any) =>
      req(`/settings/${key}`, { method: "PUT", body: JSON.stringify({ value }) }),
  },
  services: {
    list: () => req<any[]>("/services"),
    create: (b: any) => req("/services", { method: "POST", body: JSON.stringify(b) }),
    update: (id: number, b: any) => req(`/services/${id}`, { method: "PUT", body: JSON.stringify(b) }),
    remove: (id: number) => req(`/services/${id}`, { method: "DELETE" }),
  },
  countries: {
    list: () => req<any[]>("/countries"),
    create: (b: any) => req("/countries", { method: "POST", body: JSON.stringify(b) }),
    update: (id: number, b: any) => req(`/countries/${id}`, { method: "PUT", body: JSON.stringify(b) }),
    remove: (id: number) => req(`/countries/${id}`, { method: "DELETE" }),
  },
  numbers: {
    list: (q: Record<string, any> = {}) => {
      const clean: Record<string, string> = {};
      Object.entries(q).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") clean[k] = String(v);
      });
      const p = new URLSearchParams(clean).toString();
      return req<any[]>(`/numbers${p ? "?" + p : ""}`);
    },
    create: (b: any) => req("/numbers", { method: "POST", body: JSON.stringify(b) }),
    bulk: (b: any) => req<{ inserted: number; submitted: number }>("/numbers/bulk", {
      method: "POST",
      body: JSON.stringify(b),
    }),
    update: (id: number, b: any) => req(`/numbers/${id}`, { method: "PUT", body: JSON.stringify(b) }),
    remove: (id: number) => req(`/numbers/${id}`, { method: "DELETE" }),
  },
  users: {
    list: (q?: string) => req<any[]>(`/users${q ? "?q=" + encodeURIComponent(q) : ""}`),
    adjust: (id: number, delta: number) =>
      req(`/users/${id}/adjust`, { method: "POST", body: JSON.stringify({ delta }) }),
    ban: (id: number) => req(`/users/${id}/ban`, { method: "POST" }),
    unban: (id: number) => req(`/users/${id}/unban`, { method: "POST" }),
  },
  withdrawals: {
    list: (status?: string) =>
      req<any[]>(`/withdrawals${status ? "?status=" + status : ""}`),
    pay: (id: number, note?: string) =>
      req(`/withdrawals/${id}/pay`, { method: "POST", body: JSON.stringify({ note }) }),
    reject: (id: number, note?: string) =>
      req(`/withdrawals/${id}/reject`, { method: "POST", body: JSON.stringify({ note }) }),
  },
  sms: { list: () => req<any[]>("/sms") },
};
