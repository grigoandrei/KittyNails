import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  fetchNailTypes,
  createNailType,
  updateNailType,
  type NailType,
} from "./api";

export function NailTypesPage() {
  const [nailTypes, setNailTypes] = useState<NailType[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // Form state
  const [formName, setFormName] = useState("");
  const [formDuration, setFormDuration] = useState("");
  const [formPrice, setFormPrice] = useState("");
  const [formSortOrder, setFormSortOrder] = useState("0");

  const loadNailTypes = () => {
    setLoading(true);
    fetchNailTypes()
      .then(setNailTypes)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadNailTypes();
  }, []);

  const resetForm = () => {
    setFormName("");
    setFormDuration("");
    setFormPrice("");
    setFormSortOrder("0");
    setEditingId(null);
    setShowCreate(false);
  };

  const startEdit = (nailType: NailType) => {
    setEditingId(nailType.id);
    setFormName(nailType.name);
    setFormDuration(String(nailType.duration_minutes));
    setFormPrice(String(nailType.price));
    setFormSortOrder(String(nailType.sort_order));
    setShowCreate(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createNailType({
        name: formName,
        duration_minutes: Number(formDuration),
        price: Number(formPrice),
        sort_order: Number(formSortOrder),
      });
      toast.success("Nail type created");
      resetForm();
      loadNailTypes();
    } catch {
      // error already toasted by adminFetch
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    try {
      await updateNailType(editingId, {
        name: formName,
        duration_minutes: Number(formDuration),
        price: Number(formPrice),
        sort_order: Number(formSortOrder),
      });
      toast.success("Nail type updated");
      resetForm();
      loadNailTypes();
    } catch {
      // error already toasted
    }
  };

  const toggleActive = async (nailType: NailType) => {
    try {
      await updateNailType(nailType.id, { is_active: !nailType.is_active });
      toast.success(
        `Nail type ${nailType.is_active ? "deactivated" : "activated"}`
      );
      loadNailTypes();
    } catch {
      // error already toasted
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Nail Types</h2>
        <button
          onClick={() => {
            resetForm();
            setShowCreate(true);
          }}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
        >
          + Add Nail Type
        </button>
      </div>

      {/* Create / Edit form */}
      {(showCreate || editingId) && (
        <form
          onSubmit={editingId ? handleUpdate : handleCreate}
          className="bg-card border border-border rounded-xl p-6 mb-6"
        >
          <h3 className="font-semibold mb-4">
            {editingId ? "Edit Nail Type" : "New Nail Type"}
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

      {/* Nail types table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto"><table className="w-full min-w-[600px]">
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
              {nailTypes.map((nailType) => (
                <tr
                  key={nailType.id}
                  className="border-b border-border last:border-0"
                >
                  <td className="px-6 py-4 text-sm">{nailType.name}</td>
                  <td className="px-6 py-4 text-sm">
                    {nailType.duration_minutes} min
                  </td>
                  <td className="px-6 py-4 text-sm">
                    €{nailType.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm">{nailType.sort_order}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${
                        nailType.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {nailType.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEdit(nailType)}
                        className="text-xs px-3 py-1.5 border border-border rounded-lg hover:bg-secondary transition-colors cursor-pointer"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => toggleActive(nailType)}
                        className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                          nailType.is_active
                            ? "bg-red-50 text-red-600 hover:bg-red-100"
                            : "bg-green-50 text-green-600 hover:bg-green-100"
                        }`}
                      >
                        {nailType.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </div>
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
