import { toast } from "sonner";

const TOKEN_KEY = "admin_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function adminFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    clearToken();
    window.location.href = "/admin/login";
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const message = error?.detail || error?.message || "Request failed";
    toast.error(message);
    throw new Error(message);
  }
  return response;
}

// Auth
export async function login(
  username: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const response = await fetch("/api/admin/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Login failed");
  }
  return response.json();
}

// Services
export interface AdminService {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchAdminServices(
  skip = 0,
  limit = 50
): Promise<AdminService[]> {
  const res = await adminFetch(
    `/api/admin/services?skip=${skip}&limit=${limit}`
  );
  return res.json();
}

export async function createService(data: {
  name: string;
  duration_minutes: number;
  price: number;
}): Promise<AdminService> {
  const res = await adminFetch("/api/admin/services", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function updateService(
  id: string,
  data: Partial<{
    name: string;
    duration_minutes: number;
    price: number;
    is_active: boolean;
  }>
): Promise<AdminService> {
  const res = await adminFetch(`/api/admin/services/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.json();
}

// Availability Rules
export interface AvailabilityRule {
  id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export async function fetchAvailabilityRules(): Promise<AvailabilityRule[]> {
  const res = await adminFetch("/api/admin/availability-rules");
  return res.json();
}

export async function createAvailabilityRule(data: {
  day_of_week: number;
  start_time: string;
  end_time: string;
}): Promise<AvailabilityRule> {
  const res = await adminFetch("/api/admin/availability-rules", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function updateAvailabilityRule(
  id: string,
  data: Partial<{ day_of_week: number; start_time: string; end_time: string }>
): Promise<AvailabilityRule> {
  const res = await adminFetch(`/api/admin/availability-rules/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteAvailabilityRule(id: string): Promise<void> {
  await adminFetch(`/api/admin/availability-rules/${id}`, {
    method: "DELETE",
  });
}

// Blocked Times
export interface BlockedTime {
  id: string;
  start_time: string;
  end_time: string;
  reason?: string;
}

export async function fetchBlockedTimes(): Promise<BlockedTime[]> {
  const res = await adminFetch("/api/admin/blocked-times");
  return res.json();
}

export async function createBlockedTime(data: {
  start_time: string;
  end_time: string;
  reason?: string;
}): Promise<BlockedTime> {
  const res = await adminFetch("/api/admin/blocked-times", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteBlockedTime(id: string): Promise<void> {
  await adminFetch(`/api/admin/blocked-times/${id}`, { method: "DELETE" });
}

// Appointments
export interface AdminAppointment {
  id: string;
  service_id: string;
  client_email: string;
  start_time: string;
  status: string;
  created_at: string;
  service?: AdminService;
}

export async function fetchAdminAppointments(params: {
  status?: string;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}): Promise<AdminAppointment[]> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.date_from) searchParams.set("date_from", params.date_from);
  if (params.date_to) searchParams.set("date_to", params.date_to);
  if (params.skip !== undefined)
    searchParams.set("skip", String(params.skip));
  if (params.limit !== undefined)
    searchParams.set("limit", String(params.limit));
  const res = await adminFetch(
    `/api/admin/appointments/?${searchParams.toString()}`
  );
  return res.json();
}

export async function cancelAppointment(id: string): Promise<void> {
  await adminFetch(`/api/admin/appointments/${id}/cancel`, {
    method: "PATCH",
  });
}

export async function noShowAppointment(id: string): Promise<void> {
  await adminFetch(`/api/admin/appointments/${id}/no-show`, {
    method: "PATCH",
  });
}

export async function completeAppointment(id: string): Promise<void> {
  await adminFetch(`/api/admin/appointments/${id}/complete`, {
    method: "PATCH",
  });
}
