// --- Nail Analysis ---

export interface NailAnalysisResponse {
  nail_type_id: string;
  design_tier_id: string;
  nail_type: string;
  design_tier: string;
  estimated_price: number;
  estimated_duration_minutes: number;
  confidence: string;
  reasoning: string;
  image_key?: string | null;
}

export async function analyzeNails(image: File): Promise<NailAnalysisResponse> {
  const formData = new FormData();
  formData.append("image", image);

  const response = await fetch("/api/analyze-nails", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      error?.detail || error?.message || "Failed to analyze photo"
    );
  }
  return response.json();
}

// --- Nail Types ---

export interface NailType {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
  sort_order: number;
  is_active: boolean;
}

export async function fetchNailTypes(): Promise<NailType[]> {
  const response = await fetch("/api/nail-types");
  if (!response.ok) throw new Error("Failed to fetch nail types");
  return response.json();
}

// --- Errors ---

/** Error carrying the HTTP status so callers can react to 404 or 409. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function apiError(response: Response, fallback: string): Promise<ApiError> {
  const error = await response.json().catch(() => null);
  const detail = typeof error?.detail === "string" ? error.detail : null;
  return new ApiError(detail || error?.message || fallback, response.status);
}

// --- monthly set ---

export interface MonthlySetDesign {
  id: string;
  title: string;
  price: number;
  duration_minutes: number;
  description: string | null;
  image_url: string | null;
}

/** Designs that can be booked right now. Taken ones are never returned. */
export async function fetchMonthlySets(): Promise<MonthlySetDesign[]> {
  const response = await fetch("/api/monthly-sets");
  if (!response.ok) throw await apiError(response, "Failed to load designs");
  return response.json();
}

export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (!hours) return `${mins} min`;
  return mins ? `${hours}h ${mins}m` : `${hours}h`;
}

// --- Slots ---

/** What is being booked: a regular service or a monthly set. */
export type ServiceRef =
  | { kind: "regular"; nailTypeId: string; designTierId: string | null }
  | { kind: "monthlySet"; monthlySetModelId: string };

function serviceParams(service: ServiceRef): Record<string, string> {
  if (service.kind === "monthlySet") return { monthly_set_model_id: service.monthlySetModelId };
  const params: Record<string, string> = { nail_type_id: service.nailTypeId };
  if (service.designTierId) params.design_tier_id = service.designTierId;
  return params;
}

export async function fetchAvailableDates(
  service: ServiceRef,
  year: number,
  month: number
): Promise<string[]> {
  const params = new URLSearchParams({
    ...serviceParams(service),
    year: String(year),
    month: String(month),
  });

  const response = await fetch(`/api/slots/dates?${params}`);
  if (!response.ok) {
    throw await apiError(response, "Failed to fetch available dates");
  }
  return response.json();
}

export async function fetchSlots(
  service: ServiceRef,
  date: string
): Promise<string[]> {
  const params = new URLSearchParams({ ...serviceParams(service), date });

  const response = await fetch(`/api/slots/?${params}`);
  if (!response.ok) {
    throw await apiError(response, "Failed to fetch available time slots");
  }
  return response.json();
}

// --- Appointments ---

export interface CreateAppointmentPayload {
  nail_type_id?: string | null;
  design_tier_id?: string | null;
  monthly_set_model_id?: string | null;
  client_email: string;
  start_time: string;
  ai_confidence?: string;
  ai_reasoning?: string;
  image_key?: string | null;
  needs_removal?: boolean;
}

export interface AppointmentResponse {
  id: string;
  nail_type_id: string | null;
  design_tier_id: string | null;
  monthly_set_model_id?: string | null;
  client_email: string;
  start_time: string;
  end_time: string;
  status: string;
  quoted_price: number;
  ai_confidence: string | null;
  ai_reasoning: string | null;
  created_at: string;
  image_url?: string | null;
  needs_removal?: boolean;
}

export async function createAppointment(
  payload: CreateAppointmentPayload
): Promise<AppointmentResponse> {
  const response = await fetch("/api/appointments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      error?.detail || error?.message || "Failed to create appointment"
    );
  }
  return response.json();
}

// --- Stripe Checkout ---

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
  appointment_id: string;
}

export async function createCheckoutSession(
  payload: CreateAppointmentPayload
): Promise<CheckoutSessionResponse> {
  const response = await fetch("/api/checkout/create-session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await apiError(response, "Failed to start checkout");
  }
  return response.json();
}
