import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  fetchAvailabilityRules,
  createAvailabilityRule,
  updateAvailabilityRule,
  deleteAvailabilityRule,
  type AvailabilityRule,
} from "./api";

const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export function AvailabilityPage() {
  const [rules, setRules] = useState<AvailabilityRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingRule, setEditingRule] = useState<AvailabilityRule | null>(null);
  const [formDay, setFormDay] = useState("0");
  const [formStart, setFormStart] = useState("09:00");
  const [formEnd, setFormEnd] = useState("17:00");

  const loadRules = () => {
    setLoading(true);
    fetchAvailabilityRules()
      .then(setRules)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRules();
  }, []);

  const startEdit = (rule: AvailabilityRule) => {
    setEditingRule(rule);
    setFormDay(String(rule.day_of_week));
    setFormStart(rule.start_time.slice(0, 5));
    setFormEnd(rule.end_time.slice(0, 5));
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingRule) {
        await updateAvailabilityRule(editingRule.id, {
          day_of_week: Number(formDay),
          start_time: formStart + ":00",
          end_time: formEnd + ":00",
        });
        toast.success("Availability rule updated");
      } else {
        await createAvailabilityRule({
          day_of_week: Number(formDay),
          start_time: formStart + ":00",
          end_time: formEnd + ":00",
        });
        toast.success("Availability rule added");
      }
      setShowForm(false);
      setEditingRule(null);
      loadRules();
    } catch {
      // error toasted by adminFetch
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this availability rule?")) return;
    try {
      await deleteAvailabilityRule(id);
      toast.success("Rule deleted");
      loadRules();
    } catch {
      // error toasted
    }
  };

  // Sort rules by day_of_week then start_time
  const sortedRules = [...rules].sort((a, b) => {
    if (a.day_of_week !== b.day_of_week) return a.day_of_week - b.day_of_week;
    return a.start_time.localeCompare(b.start_time);
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Availability Rules</h2>
        <button
          onClick={() => { setEditingRule(null); setFormDay("0"); setFormStart("09:00"); setFormEnd("17:00"); setShowForm(true); }}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
        >
          + Add Rule
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-card border border-border rounded-xl p-6 mb-6"
        >
          <h3 className="font-semibold mb-4">{editingRule ? "Edit Availability Rule" : "New Availability Rule"}</h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Day</label>
              <select
                value={formDay}
                onChange={(e) => setFormDay(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {DAY_NAMES.map((name, i) => (
                  <option key={i} value={i}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Start Time
              </label>
              <input
                type="time"
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
                type="time"
                value={formEnd}
                onChange={(e) => setFormEnd(e.target.value)}
                required
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
            >
              {editingRule ? "Update" : "Create"}
            </button>
            <button
              type="button"
              onClick={() => { setShowForm(false); setEditingRule(null); }}
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
        ) : sortedRules.length === 0 ? (
          <p className="text-muted-foreground p-6">
            No availability rules configured.
          </p>
        ) : (
          <div className="overflow-x-auto"><table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-border text-left bg-secondary">
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Day
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Start Time
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  End Time
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedRules.map((rule) => (
                <tr
                  key={rule.id}
                  className="border-b border-border last:border-0"
                >
                  <td className="px-6 py-4 text-sm">
                    {DAY_NAMES[rule.day_of_week]}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {rule.start_time.slice(0, 5)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {rule.end_time.slice(0, 5)}
                  </td>
                  <td className="px-6 py-4 flex gap-2">
                    <button
                      onClick={() => startEdit(rule)}
                      className="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-xs px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors cursor-pointer"
                    >
                      Delete
                    </button>
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
