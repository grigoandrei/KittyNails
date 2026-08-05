import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  fetchDesignTiers,
  createDesignTier,
  updateDesignTier,
  type DesignTier,
} from "./api";

export function DesignTiersPage() {
  const [designTiers, setDesignTiers] = useState<DesignTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // Form state
  const [formName, setFormName] = useState("");
  const [formDuration, setFormDuration] = useState("");
  const [formPrice, setFormPrice] = useState("");
  const [formSortOrder, setFormSortOrder] = useState("0");

  const loadDesignTiers = () => {
    setLoading(true);
    fetchDesignTiers()
      .then(setDesignTiers)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDesignTiers();
  }, []);

  const resetForm = () => {
    setFormName("");
    setFormDuration("");
    setFormPrice("");
    setFormSortOrder("0");
    setEditingId(null);
    setShowCreate(false);
  };

  const startEdit = (tier: DesignTier) => {
    setEditingId(tier.id);
    setFormName(tier.name);
    setFormDuration(String(tier.duration_minutes));
    setFormPrice(String(tier.price));
    setFormSortOrder(String(tier.sort_order));
    setShowCreate(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createDesignTier({
        name: formName,
        duration_minutes: Number(formDuration),
        price: Number(formPrice),
        sort_order: Number(formSortOrder),
      });
      toast.success("Design tier created");
      resetForm();
      loadDesignTiers();
    } catch {
      // error already toasted by adminFetch
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    try {
      await updateDesignTier(editingId, {
        name: formName,
        duration_minutes: Number(formDuration),
        price: Number(formPrice),
        sort_order: Number(formSortOrder),
      });
      toast.success("Design tier updated");
      resetForm();
      loadDesignTiers();
    } catch {
      // error already toasted
    }
  };

  const toggleActive = async (tier: DesignTier) => {
    try {
      await updateDesignTier(tier.id, { is_active: !tier.is_active });
      toast.success(
        `Design tier ${tier.is_active ? "deactivated" : "activated"}`
      );
      loadDesignTiers();
    } catch {
      // error already toasted
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Design Tiers</h2>
        <button
          onClick={() => {
            resetForm();
            setShowCreate(true);
          }}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
        >
          + Add Design Tier
        </button>
      </div>

      {/* Create / Edit form */}
      {(showCreate || editingId) && (
        <form
          onSubmit={editingId ? handleUpdate : handleCreate}
          className="bg-card border border-border rounded-xl p-6 mb-6"
        >
          <h3 className="font-semibold mb-4">
            {editingId ? "Edit Design Tier" : "New Design Tier"}
          </h3>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Duration (min)
              </label>
              <input
                type="number"
                value={formDuration}
                onChange={(e) => setFormDuration(e.target.value)}
                required
                min={1}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Price (€)
              </label>
              <input
                type="number"
                step="0.01"
                value={formPrice}
                onChange={(e) => setFormPrice(e.target.value)}
                required
                min={0}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Sort Order
              </label>
              <input
                type="number"
                value={formSortOrder}
                onChange={(e) => setFormSortOrder(e.target.value)}
                min={0}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
            >
              {editingId ? "Save Changes" : "Create"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-secondary transition-colors cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Design tiers table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left bg-secondary">
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Name
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Duration
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Price
                </th>
                <th className="px-6 py-3 text-sm font-medium text-muted-foreground">
                  Sort Order
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
              {designTiers.map((tier) => (
                <tr
                  key={tier.id}
                  className="border-b border-border last:border-0"
                >
                  <td className="px-6 py-4 text-sm">{tier.name}</td>
                  <td className="px-6 py-4 text-sm">
                    {tier.duration_minutes} min
                  </td>
                  <td className="px-6 py-4 text-sm">
                    €{tier.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm">{tier.sort_order}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${
                        tier.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {tier.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEdit(tier)}
                        className="text-xs px-3 py-1.5 border border-border rounded-lg hover:bg-secondary transition-colors cursor-pointer"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => toggleActive(tier)}
                        className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                          tier.is_active
                            ? "bg-red-50 text-red-600 hover:bg-red-100"
                            : "bg-green-50 text-green-600 hover:bg-green-100"
                        }`}
                      >
                        {tier.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </div>
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
