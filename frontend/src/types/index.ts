// Service Types

export interface NailService {
  id: number;
  name: string; // 1-100 chars
  description: string | null; // max 500 chars
  duration_minutes: number; // 1-210
  price: number; // > 0, euros
}

export interface NailServiceCreate {
  name: string;
  description?: string | null;
  duration_minutes: number;
  price: number;
}

export interface NailServiceUpdate {
  name?: string;
  description?: string | null;
  duration_minutes?: number;
  price?: number;
}

// Appointment Types

export interface AppointmentCreate {
  client_name: string; // 1-100 chars
  client_phone: string; // 7-20 chars
  client_email?: string | null;
  service_id: number;
  appointment_date: string; // ISO date "YYYY-MM-DD"
  appointment_time: string; // "HH:MM" on 15-min boundary
}

export interface AppointmentResponse {
  id: number;
  client_name: string;
  client_phone: string;
  client_email: string | null;
  service: NailService;
  appointment_date: string;
  appointment_time: string;
  end_time: string;
  status: string;
  created_at: string;
}

// Availability Types

export interface TimeSlot {
  start_time: string; // "HH:MM"
  end_time: string; // "HH:MM"
  available: boolean;
}

export interface DaySchedule {
  date: string;
  slots: TimeSlot[];
  is_working_day: boolean;
}

export interface WeeklyAvailabilityCreate {
  day_of_week: number; // 0=Monday ... 6=Sunday
  start_time: string; // "HH:MM"
  end_time: string; // "HH:MM", must be after start_time
}

export interface WeeklyAvailability extends WeeklyAvailabilityCreate {
  id: number;
}

export interface BlockedTimeCreate {
  blocked_date: string; // ISO date
  start_time?: string | null; // null = entire day blocked
  end_time?: string | null;
  reason?: string | null;
}

export interface BlockedTimeResponse extends BlockedTimeCreate {
  id: number;
}

// API Error Type

export interface ApiError {
  status: number;
  detail: string;
}
