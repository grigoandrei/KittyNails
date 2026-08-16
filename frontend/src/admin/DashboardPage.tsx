import { useEffect, useState } from "react";
import { format } from "date-fns";
import { fetchAdminAppointments, type AdminAppointment } from "./api";

export function DashboardPage() {
  const [appointments, setAppointments] = useState<AdminAppointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = format(new Date(), "yyyy-MM-dd");
    fetchAdminAppointments({
      status: "BOOKED",
      date_from: today,
      date_to: today,
    })
      .then(setAppointments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4">
          Today's Appointments ({format(new Date(), "MMMM d, yyyy")})
        </h3>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : appointments.length === 0 ? (
          <p className="text-muted-foreground py-4">
            No appointments booked for today.
          </p>
        ) : (
          <div className="overflow-x-auto"><table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="pb-3 text-sm font-medium text-muted-foreground">
                  Time
                </th>
                <th className="pb-3 text-sm font-medium text-muted-foreground">
                  Client
                </th>
                <th className="pb-3 text-sm font-medium text-muted-foreground">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((apt) => (
                <tr key={apt.id} className="border-b border-border last:border-0">
                  <td className="py-3 text-sm">
                    {format(new Date(apt.start_time), "HH:mm")}
                  </td>
                  <td className="py-3 text-sm">{apt.client_email}</td>
                  <td className="py-3">
                    <span className="text-xs px-2 py-1 rounded-full bg-primary-light text-primary-foreground font-medium">
                      {apt.status}
                    </span>
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
