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

// --- Slots ---

export async function fetchAvailableDates(
  nailTypeId: string,
  designTierId: string,
  year: number,
  month: number
): Promise<string[]> {
  const response = await fetch(
    `/api/slots/dates?nail_type_id=${nailTypeId}&design_tier_id=${designTierId}&year=${year}&month=${month}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch available dates");
  }
  return response.json();
}

export async function fetchSlots(
  nailTypeId: string,
  designTierId: string,
  date: string
): Promise<string[]> {
  const response = await fetch(
    `/api/slots/?nail_type_id=${nailTypeId}&design_tier_id=${designTierId}&date=${date}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch available time slots");
  }
  return response.json();
}

// --- Appointments ---

export interface CreateAppointmentPayload {
  nail_type_id: string;
  design_tier_id: string;
  client_email: string;
  start_time: string;
  ai_confidence?: string;
  ai_reasoning?: string;
}

export interface AppointmentResponse {
  id: string;
  nail_type_id: string;
  design_tier_id: string;
  client_email: string;
  start_time: string;
  end_time: string;
  status: string;
  quoted_price: number;
  ai_confidence: string | null;
  ai_reasoning: string | null;
  created_at: string;
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
