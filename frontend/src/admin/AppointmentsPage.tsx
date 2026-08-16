import { useEffect, useState } from "react";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  fetchAdminAppointments,
  cancelAppointment,
  noShowAppointment,
  completeAppointment,
  type AdminAppointment,
} from "./api";

const STATUS_OPTIONS = ["", "BOOKED", "CANCELLED", "NO_SHOW", "COMPLETED"];

export function AppointmentsPage() {
  const [appointments, setAppointments] = useState<AdminAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

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
      <h2 className="text-2xl font-bold mb-6">Appointments</h2>

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
                  Client
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
                    {format(new Date(apt.start_time), "MMM d, yyyy HH:mm")}
                  </td>
                  <td className="px-6 py-4 text-sm">{apt.client_email}</td>
                  <td className="px-6 py-4 text-sm">€{apt.quoted_price.toFixed(2)}</td>
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
    </div>
  );
}
