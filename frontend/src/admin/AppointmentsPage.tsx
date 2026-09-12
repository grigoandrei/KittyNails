import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  fetchAdminAppointments,
  cancelAppointment,
  noShowAppointment,
  completeAppointment,
  createAdminAppointment,
  fetchNailTypes,
  fetchDesignTiers,
  type AdminAppointment,
  type NailType,
  type DesignTier,
} from "./api";

const STATUS_OPTIONS = ["", "BOOKED", "CANCELLED", "NO_SHOW", "COMPLETED"];

/**
 * Human-readable duration between two ISO timestamps, e.g. "3h", "90 min",
 * "1h 30m". Duration is end - start (both stored on the appointment).
 */
function formatDuration(startIso: string, endIso: string): string {
  const mins = Math.round(
    (new Date(endIso).getTime() - new Date(startIso).getTime()) / 60000
  );
  if (!Number.isFinite(mins) || mins <= 0) return "—";
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

/**
 * Convert a `datetime-local` value ("YYYY-MM-DDTHH:mm", Berlin wall-clock)
 * into an ISO string carrying Berlin's UTC offset for that date, e.g.
 * "2026-09-14T10:00:00+02:00" (CEST) or "...+01:00" (CET). This matches the
 * public booking flow and keeps the backend's Berlin-local working-hours check
 * correct. Using toISOString() (UTC) would shift the time and fail that check.
 */
function toBerlinISO(localValue: string): string {
  // Interpret the wall-clock as if it were UTC to get a stable instant, then
  // measure how Berlin renders that instant to derive the offset.
  const asUtc = new Date(`${localValue}:00Z`);
  const berlinParts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Europe/Berlin",
    hour: "numeric",
    hour12: false,
  }).formatToParts(asUtc);
  const berlinHour = Number(berlinParts.find((p) => p.type === "hour")?.value);
  // Difference between Berlin's rendered hour and the UTC hour gives the offset.
  let offsetHours = berlinHour - asUtc.getUTCHours();
  if (offsetHours > 12) offsetHours -= 24;
  if (offsetHours < -12) offsetHours += 24;
  const sign = offsetHours >= 0 ? "+" : "-";
  const hh = String(Math.abs(offsetHours)).padStart(2, "0");
  return `${localValue}:00${sign}${hh}:00`;
}


export function AppointmentsPage() {
  const [appointments, setAppointments] = useState<AdminAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);

  // Add-appointment modal
  const [showAdd, setShowAdd] = useState(false);
  const [nailTypes, setNailTypes] = useState<NailType[]>([]);
  const [designTiers, setDesignTiers] = useState<DesignTier[]>([]);
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [form, setForm] = useState({
    nail_type_id: "",
    design_tier_id: "",
    client_email: "",
    start_time: "",
    needs_removal: false,
  });

  const loadAppointments = () => {
    setLoading(true);
    fetchAdminAppointments({
      status: statusFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      limit: 50,
    })
      .then(setAppointments)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAppointments();
  }, [statusFilter, dateFrom, dateTo]);

  const handleCancel = async (id: string) => {
    if (!confirm("Cancel this appointment?")) return;
    try {
      await cancelAppointment(id);
      toast.success("Appointment cancelled");
      loadAppointments();
    } catch {
      // toasted
    }
  };

  const handleNoShow = async (id: string) => {
    if (!confirm("Mark as no-show?")) return;
    try {
      await noShowAppointment(id);
      toast.success("Marked as no-show");
      loadAppointments();
    } catch {
      // toasted
    }
  };

  const handleComplete = async (id: string) => {
    try {
      await completeAppointment(id);
      toast.success("Marked as completed");
      loadAppointments();
    } catch {
      // toasted
    }
  };

  const openAddModal = async () => {
    setForm({
      nail_type_id: "",
      design_tier_id: "",
      client_email: "",
      start_time: "",
      needs_removal: false,
    });
    setShowAdd(true);
    try {
      const [nt, dt] = await Promise.all([fetchNailTypes(), fetchDesignTiers()]);
      setNailTypes(nt.filter((t) => t.is_active));
      setDesignTiers(dt.filter((t) => t.is_active));
    } catch {
      // toasted by adminFetch
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nail_type_id || !form.client_email || !form.start_time) {
      toast.error("Nail type, email, and date/time are required.");
      return;
    }
    setAddSubmitting(true);
    try {
      // The datetime-local value is Berlin wall-clock (the artist is in Berlin).
      // Send it with Berlin's UTC offset for that date so the backend sees the
      // correct local time in its working-hours check — matching the public
      // booking flow, which sends Berlin-offset slot times. Sending UTC
      // (toISOString) would shift 10:00 → 08:00 and fail the hours check.
      await createAdminAppointment({
        nail_type_id: form.nail_type_id,
        design_tier_id: form.design_tier_id || null,
        client_email: form.client_email,
        start_time: toBerlinISO(form.start_time),
        needs_removal: form.needs_removal,
      });
      toast.success("Appointment created");
      setShowAdd(false);
      loadAppointments();
    } catch {
      // toasted
    } finally {
      setAddSubmitting(false);
    }
  };

  const statusBadgeClass = (status: string) => {
    switch (status) {
      case "BOOKED":
        return "bg-blue-100 text-blue-700";
      case "CANCELLED":
        return "bg-red-100 text-red-700";
      case "NO_SHOW":
        return "bg-yellow-100 text-yellow-700";
      case "COMPLETED":
        return "bg-green-100 text-green-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Appointments</h2>
        <button
          onClick={openAddModal}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
        >
          + Add Appointment
        </button>
      </div>

      {/* Filters */}
      <div className="bg-card border border-border rounded-xl p-4 mb-6">
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">All</option>
              {STATUS_OPTIONS.filter(Boolean).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            onClick={() => {
              setStatusFilter("");
              setDateFrom("");
              setDateTo("");
            }}
            className="px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-secondary transition-colors cursor-pointer"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : appointments.length === 0 ? (
          <p className="text-muted-foreground p-6">No appointments found.</p>
        ) : (
          <div className="overflow-x-auto"><table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-border text-left bg-secondary">
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Date/Time
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Duration
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Client
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Photo
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Price
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((apt) => (
                <tr
                  key={apt.id}
                  className="border-b border-border last:border-0"
                >
                  <td className="px-6 py-4 text-sm">
                    {new Date(apt.start_time).toLocaleString("de-DE", { timeZone: "Europe/Berlin", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {formatDuration(apt.start_time, apt.end_time)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {apt.client_email}
                    {apt.source === "instagram" && (
                      <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-pink-100 text-pink-700 font-medium">
                        Instagram
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {apt.image_url ? (
                      <button
                        type="button"
                        onClick={() => setLightboxUrl(apt.image_url ?? null)}
                        className="cursor-pointer"
                        aria-label="View nail photo"
                      >
                        <img
                          src={apt.image_url}
                          alt="Client nail inspiration"
                          className="w-12 h-12 object-cover rounded-lg border border-border hover:opacity-80 transition-opacity"
                        />
                      </button>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    €{apt.quoted_price.toFixed(2)}
                    {apt.needs_removal && (
                      <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-medium">
                        + removal
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${statusBadgeClass(apt.status)}`}
                    >
                      {apt.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {apt.status === "BOOKED" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleComplete(apt.id)}
                          className="text-xs px-3 py-1.5 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors cursor-pointer"
                        >
                          Complete
                        </button>
                        <button
                          onClick={() => handleNoShow(apt.id)}
                          className="text-xs px-3 py-1.5 bg-yellow-50 text-yellow-600 rounded-lg hover:bg-yellow-100 transition-colors cursor-pointer"
                        >
                          No-Show
                        </button>
                        <button
                          onClick={() => handleCancel(apt.id)}
                          className="text-xs px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
      </div>

      {/* Add appointment modal */}
      {showAdd && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => !addSubmitting && setShowAdd(false)}
          role="dialog"
          aria-modal="true"
        >
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleAddSubmit}
            className="bg-card border border-border rounded-xl p-6 w-full max-w-md space-y-4"
          >
            <h3 className="text-lg font-bold">Add Appointment</h3>
            <p className="text-xs text-muted-foreground">
              For clients who booked via Instagram. Creates a confirmed booking
              with no deposit and no confirmation email.
            </p>

            <div>
              <label className="block text-sm font-medium mb-1">Nail type *</label>
              <select
                value={form.nail_type_id}
                onChange={(e) => setForm({ ...form, nail_type_id: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
                required
              >
                <option value="">Select…</option>
                {nailTypes.map((nt) => (
                  <option key={nt.id} value={nt.id}>
                    {nt.name} — €{nt.price.toFixed(2)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Design tier (optional)
              </label>
              <select
                value={form.design_tier_id}
                onChange={(e) => setForm({ ...form, design_tier_id: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              >
                <option value="">None</option>
                {designTiers.map((dt) => (
                  <option key={dt.id} value={dt.id}>
                    {dt.name} — +€{dt.price.toFixed(2)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Client email *</label>
              <input
                type="email"
                value={form.client_email}
                onChange={(e) => setForm({ ...form, client_email: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Date & time *</label>
              <input
                type="datetime-local"
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
                required
              />
            </div>

            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={form.needs_removal}
                onChange={(e) => setForm({ ...form, needs_removal: e.target.checked })}
                className="h-4 w-4 accent-primary cursor-pointer"
              />
              Needs nail removal (+€15)
            </label>

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowAdd(false)}
                disabled={addSubmitting}
                className="px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-secondary transition-colors cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addSubmitting}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50"
              >
                {addSubmitting ? "Creating…" : "Create"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Photo lightbox */}
      {lightboxUrl && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setLightboxUrl(null)}
          role="dialog"
          aria-modal="true"
        >
          <img
            src={lightboxUrl}
            alt="Client nail inspiration"
            className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
