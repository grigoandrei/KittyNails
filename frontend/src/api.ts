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

// --- Design Tiers ---

export interface DesignTier {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
}

export async function fetchDesignTiers(): Promise<DesignTier[]> {
  const response = await fetch("/api/design-tiers");
  if (!response.ok) throw new Error("Failed to fetch design tiers");
  return response.json();
}

// --- Promotion ---

export interface Promotion {
  name: string;
  percent: number;
  start: string; // YYYY-MM-DD, Berlin date
  end: string;
  design_tiers: string[];
}

export async function fetchPromotion(): Promise<Promotion | null> {
  const response = await fetch("/api/promotion");
  if (!response.ok) return null;
  return response.json();
}

// Display only. Mirrors backend pricing.compute_price; the backend is
// authoritative for the actual charge. `day` is YYYY-MM-DD.
export function promoAppliesTo(
  promo: Promotion | null,
  designTier: string | null | undefined,
  day?: string | null
): boolean {
  if (!promo || !designTier || !promo.design_tiers.includes(designTier)) return false;
  return !day || (day >= promo.start && day <= promo.end);
}

// Berlin calendar date (YYYY-MM-DD) of an ISO timestamp, matching how the
// backend decides whether an appointment falls in the promo window.
export function berlinDay(iso: string): string {
  return new Date(iso).toLocaleDateString("en-CA", { timeZone: "Europe/Berlin" });
}

// The instant the promo ends: 23:59:59 Berlin time on its last day.
export function promoEndsAt(promo: Promotion): Date {
  const utcGuess = new Date(`${promo.end}T23:59:59Z`);
  const offset = new Intl.DateTimeFormat("en-US", {
    timeZone: "Europe/Berlin",
    timeZoneName: "longOffset",
  })
    .formatToParts(utcGuess)
    .find((p) => p.type === "timeZoneName")!
    .value.replace("GMT", "");
  return new Date(`${promo.end}T23:59:59${offset || "+00:00"}`);
}

// Mirrors backend pricing.round_promo_price: cents below 50 round down, above
// 50 round up, exactly 50 stay.
export function applyPromo(price: number, promo: Promotion): number {
  const total = Math.round(price * (1 - promo.percent / 100) * 100);
  const euros = Math.floor(total / 100);
  const cents = total % 100;
  if (cents < 50) return euros;
  if (cents > 50) return euros + 1;
  return euros + 0.5;
}

// --- Slots ---

export async function fetchAvailableDates(
  nailTypeId: string,
  designTierId: string | null,
  year: number,
  month: number
): Promise<string[]> {
  const params = new URLSearchParams({
    nail_type_id: nailTypeId,
    year: String(year),
    month: String(month),
  });
  if (designTierId) params.set("design_tier_id", designTierId);

  const response = await fetch(`/api/slots/dates?${params}`);
  if (!response.ok) {
    throw new Error("Failed to fetch available dates");
  }
  return response.json();
}

export async function fetchSlots(
  nailTypeId: string,
  designTierId: string | null,
  date: string
): Promise<string[]> {
  const params = new URLSearchParams({
    nail_type_id: nailTypeId,
    date,
  });
  if (designTierId) params.set("design_tier_id", designTierId);

  const response = await fetch(`/api/slots/?${params}`);
  if (!response.ok) {
    throw new Error("Failed to fetch available time slots");
  }
  return response.json();
}

// --- Appointments ---

export interface CreateAppointmentPayload {
  nail_type_id: string;
  design_tier_id?: string | null;
  client_email: string;
  start_time: string;
  ai_confidence?: string;
  ai_reasoning?: string;
  image_key?: string | null;
  needs_removal?: boolean;
}

export interface AppointmentResponse {
  id: string;
  nail_type_id: string;
  design_tier_id: string | null;
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
    const error = await response.json().catch(() => null);
    throw new Error(
      error?.detail || error?.message || "Failed to start checkout"
    );
  }
  return response.json();
}
