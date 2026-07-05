import { useEffect, useState } from "react";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  fetchBlockedTimes,
  createBlockedTime,
  deleteBlockedTime,
  type BlockedTime,
} from "./api";

export function BlockedTimesPage() {
  const [blockedTimes, setBlockedTimes] = useState<BlockedTime[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formStart, setFormStart] = useState("");
  const [formEnd, setFormEnd] = useState("");
  const [formReason, setFormReason] = useState("");

  const loadBlockedTimes = () => {
    setLoading(true);
    fetchBlockedTimes()
      .then(setBlockedTimes)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadBlockedTimes();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createBlockedTime({
        start_time: new Date(formStart).toISOString(),
        end_time: new Date(formEnd).toISOString(),
        reason: formReason || undefined,
      });
      toast.success("Blocked time added");
      setShowForm(false);
      setFormStart("");
      setFormEnd("");
      setFormReason("");
      loadBlockedTimes();
    } catch {
      // error toasted
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this blocked time?")) return;
    try {
      await deleteBlockedTime(id);
      toast.success("Blocked time deleted");
      loadBlockedTimes();
    } catch {
      // error toasted
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Blocked Times</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
        >
          + Block Time
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-card border border-border rounded-xl p-6 mb-6"
        >
          <h3 className="font-semibold mb-4">Block a Time Period</h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Start Time
              </label>
              <input
                type="datetime-local"
                value={formStart}
                onChange={(e) => setFormStart(e.target.value)}
                required
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                End Time
              </label>
              <input
                type="datetime-local"
                value={formEnd}
                onChange={(e) => setFormEnd(e.target.value)}
                required
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Reason (optional)
              </label>
              <input
                type="text"
                value={formReason}
                onChange={(e) => setFormReason(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-secondary transition-colors cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : blockedTimes.length === 0 ? (
          <p className="text-muted-foreground p-6">No blocked times.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left bg-secondary">
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Start
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  End
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Reason
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {blockedTimes.map((bt) => (
                <tr
                  key={bt.id}
                  className="border-b border-border last:border-0"
                >
                  <td className="px-6 py-4 text-sm">
                    {format(new Date(bt.start_time), "MMM d, yyyy HH:mm")}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {format(new Date(bt.end_time), "MMM d, yyyy HH:mm")}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {bt.reason || "—"}
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleDelete(bt.id)}
                      className="text-xs px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors cursor-pointer"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
