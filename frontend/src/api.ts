export interface Service {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Appointment {
  id: string;
  service_id: string;
  client_email: string;
  start_time: string;
  created_at: string;
}

export interface CreateAppointmentPayload {
  service_id: string;
  client_email: string;
  start_time: string;
}

export async function fetchServices(): Promise<Service[]> {
  const response = await fetch("/api/services");
  if (!response.ok) {
    throw new Error("Failed to fetch services");
  }
  return response.json();
}

export async function fetchAvailableDates(
  serviceId: string,
  year: number,
  month: number
): Promise<string[]> {
  const response = await fetch(
    `/api/slots/dates/?service_id=${serviceId}&year=${year}&month=${month}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch available dates");
  }
  return response.json();
}

export async function fetchSlots(
  serviceId: string,
  date: string
): Promise<string[]> {
  const response = await fetch(
    `/api/slots/?service_id=${serviceId}&date=${date}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch available time slots");
  }
  return response.json();
}

export async function createAppointment(
  payload: CreateAppointmentPayload
): Promise<Appointment> {
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
