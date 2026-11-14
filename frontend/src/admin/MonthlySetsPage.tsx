import { useEffect, useRef, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { toast } from "sonner";
import {
  Clock,
  Eye,
  EyeOff,
  ImagePlus,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import {
  createMonthlySetDesign,
  deleteMonthlySetDesign,
  fetchMonthlySetDesigns,
  replaceMonthlySetImage,
  updateMonthlySetDesign,
  type MonthlySetDesign,
  type MonthlySetState,
} from "./api";

const TITLE_MAX = 80;
const DESCRIPTION_MAX = 500;
const DURATION_MIN = 15;
const DURATION_MAX = 600;
const PRICE_MAX = 9999;
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

const STATES: MonthlySetState[] = ["available", "reserved", "booked", "hidden"];

const stateBadge: Record<MonthlySetState, string> = {
  available: "bg-green-50 text-green-700",
  reserved: "bg-amber-50 text-amber-700",
  booked: "bg-primary-light text-primary-dark",
  hidden: "bg-secondary text-muted-foreground",
};

function formatMinutes(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (!hours) return `${mins} min`;
  return `${hours}h${mins ? ` ${mins}m` : ""}`;
}

function formatBerlin(iso: string): string {
  return new Date(iso).toLocaleString("de-DE", {
    timeZone: "Europe/Berlin",
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Returns an error message, or null when the file is acceptable. */
function checkImage(file: File): string | null {
  if (!IMAGE_TYPES.includes(file.type)) return "Please choose a JPG, PNG, WebP or GIF image.";
  if (file.size > MAX_IMAGE_BYTES) return "Image is too large. Please keep it under 5 MB.";
  return null;
}

export function MonthlySetsPage() {
  const [designs, setDesigns] = useState<MonthlySetDesign[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<MonthlySetDesign | "new" | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const photoInputRef = useRef<HTMLInputElement>(null);
  const photoTargetRef = useRef<MonthlySetDesign | null>(null);

  const load = () => {
    setLoading(true);
    fetchMonthlySetDesigns()
      .then(setDesigns)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const toggleVisibility = async (design: MonthlySetDesign) => {
    setBusyId(design.id);
    try {
      await updateMonthlySetDesign(design.id, { is_active: !design.is_active });
      toast.success(design.is_active ? "Design hidden from the website" : "Design is now live");
      load();
    } catch {
      // toasted by adminFetch
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (design: MonthlySetDesign) => {
    if (!confirm(`Delete "${design.title}"? This can't be undone.`)) return;
    setBusyId(design.id);
    try {
      await deleteMonthlySetDesign(design.id);
      toast.success("Design deleted");
      load();
    } catch {
      // toasted
    } finally {
      setBusyId(null);
    }
  };

  const pickPhoto = (design: MonthlySetDesign) => {
    photoTargetRef.current = design;
    photoInputRef.current?.click();
  };

  const onPhotoPicked = async (file: File | undefined) => {
    const design = photoTargetRef.current;
    if (photoInputRef.current) photoInputRef.current.value = "";
    if (!file || !design) return;
    const error = checkImage(file);
    if (error) {
      toast.error(error);
      return;
    }
    setBusyId(design.id);
    try {
      await replaceMonthlySetImage(design.id, file);
      toast.success("Photo replaced");
      load();
    } catch {
      // toasted
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-primary-dark">
            Limited designs
          </p>
          <h2 className="text-2xl font-bold mt-1">Monthly sets</h2>
          <p className="text-sm text-muted-foreground mt-1">
            One of a kind designs. Each can be booked by one client only.
          </p>
        </div>
        <button
          onClick={() => setEditing("new")}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Add design
        </button>
      </div>

      {/* Status counters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {STATES.map((state) => (
          <div key={state} className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs capitalize text-muted-foreground">{state}</p>
            <p className="mt-1 text-2xl font-semibold">
              {designs.filter((d) => d.state === state).length}
            </p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : designs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card py-16 text-center">
          <ImagePlus className="mx-auto w-8 h-8 text-primary" />
          <h3 className="mt-4 text-lg font-semibold">Your idea board is empty</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Post a design you'd love to do and clients can book it.
          </p>
          <button
            onClick={() => setEditing("new")}
            className="mt-5 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
          >
            Add your first design
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {designs.map((design) => {
            const held = design.state === "reserved" || design.state === "booked";
            const busy = busyId === design.id;
            return (
              <article
                key={design.id}
                className={`bg-card border border-border rounded-xl p-3 sm:flex gap-4 ${busy ? "opacity-60" : ""}`}
              >
                {design.image_url ? (
                  <img
                    src={design.image_url}
                    alt={design.title}
                    className="aspect-[4/3] w-full rounded-lg object-cover sm:w-40 sm:h-44 sm:aspect-auto shrink-0"
                  />
                ) : (
                  <div className="aspect-[4/3] w-full rounded-lg bg-secondary flex items-center justify-center sm:w-40 sm:h-44 sm:aspect-auto shrink-0">
                    <ImagePlus className="w-6 h-6 text-muted-foreground" />
                  </div>
                )}
                <div className="flex min-w-0 flex-1 flex-col pt-3 sm:pt-1">
                  <div className="flex items-start justify-between gap-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${stateBadge[design.state]}`}
                    >
                      {design.state}
                    </span>
                    <span className="text-lg font-semibold text-primary-dark">
                      €{design.price}
                    </span>
                  </div>
                  <h3 className="mt-2 font-[family-name:var(--font-serif)] text-lg font-semibold truncate">
                    {design.title}
                  </h3>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {design.description || <em>No description</em>}
                  </p>
                  <p className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="w-3.5 h-3.5" /> {formatMinutes(design.duration_minutes)}
                  </p>
                  {held && design.client_email && (
                    <div className="mt-3 rounded-lg bg-secondary px-3 py-2 text-xs">
                      <strong className="font-medium">{design.client_email}</strong>
                      {design.appointment_start && (
                        <div className="text-muted-foreground">
                          {formatBerlin(design.appointment_start)}
                          {design.state === "reserved" && " · awaiting payment"}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="h-3 shrink-0" />
                  <div className="mt-auto flex flex-wrap gap-1 border-t border-border pt-3">
                    <ActionButton
                      icon={<Pencil className="w-3.5 h-3.5" />}
                      label="Edit"
                      onClick={() => setEditing(design)}
                      disabled={busy}
                    />
                    <span title={held ? "Reserved or booked designs can't be hidden" : undefined}>
                      <ActionButton
                        icon={design.is_active ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        label={design.is_active ? "Hide" : "Show"}
                        onClick={() => toggleVisibility(design)}
                        disabled={busy || held}
                      />
                    </span>
                    <ActionButton
                      icon={<ImagePlus className="w-3.5 h-3.5" />}
                      label="Photo"
                      onClick={() => pickPhoto(design)}
                      disabled={busy}
                    />
                    <span
                      title={
                        design.has_bookings
                          ? "Booked designs are kept for appointment history. Hide it instead."
                          : undefined
                      }
                    >
                      <ActionButton
                        icon={<Trash2 className="w-3.5 h-3.5" />}
                        label="Delete"
                        onClick={() => remove(design)}
                        disabled={busy || design.has_bookings}
                        danger
                      />
                    </span>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <input
        ref={photoInputRef}
        type="file"
        accept={IMAGE_TYPES.join(",")}
        className="hidden"
        onChange={(e) => onPhotoPicked(e.target.files?.[0])}
      />

      <DesignEditor
        key={editing === "new" ? "new" : editing?.id ?? "closed"}
        value={editing}
        onClose={() => setEditing(null)}
        onSaved={(isNew) => {
          setEditing(null);
          toast.success(isNew ? "Design published" : "Changes saved");
          load();
        }}
      />
    </div>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
  disabled,
  danger,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-30 ${
        danger ? "text-red-600 hover:bg-red-50" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function DesignEditor({
  value,
  onClose,
  onSaved,
}: {
  value: MonthlySetDesign | "new" | null;
  onClose: () => void;
  onSaved: (isNew: boolean) => void;
}) {
  const existing = value && value !== "new" ? value : null;
  const [title, setTitle] = useState(existing?.title ?? "");
  const [price, setPrice] = useState(existing ? String(existing.price) : "");
  const [duration, setDuration] = useState(existing ? String(existing.duration_minutes) : "");
  const [description, setDescription] = useState(existing?.description ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(existing?.image_url ?? null);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const inputRef = useRef<HTMLInputElement>(null);

  // Revoke local preview URLs so they don't leak.
  useEffect(() => {
    return () => {
      if (preview?.startsWith("blob:")) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const choose = (picked?: File) => {
    if (!picked) return;
    const error = checkImage(picked);
    if (error) {
      setErrors((e) => ({ ...e, image: error }));
      return;
    }
    setErrors((e) => ({ ...e, image: "" }));
    setFile(picked);
    setPreview(URL.createObjectURL(picked));
  };

  const durationNumber = Number(duration);

  const save = async () => {
    const next: Record<string, string> = {};
    if (!existing && !file) next.image = "A design photo is required.";
    if (!title.trim()) next.title = "Give the design a title.";
    const priceNumber = Number(price);
    if (!price || !(priceNumber > 0) || priceNumber > PRICE_MAX)
      next.price = `Enter a price between €1 and €${PRICE_MAX}.`;
    if (!Number.isInteger(durationNumber) || durationNumber < DURATION_MIN || durationNumber > DURATION_MAX)
      next.duration = `Duration must be ${DURATION_MIN} to ${DURATION_MAX} minutes.`;
    setErrors(next);
    if (Object.values(next).some(Boolean)) return;

    const fields = {
      title: title.trim(),
      price: priceNumber,
      duration_minutes: durationNumber,
      description: description.trim(),
    };
    setSaving(true);
    try {
      if (existing) {
        await updateMonthlySetDesign(existing.id, fields);
        if (file) await replaceMonthlySetImage(existing.id, file);
      } else {
        await createMonthlySetDesign(fields, file as File);
      }
      onSaved(!existing);
    } catch {
      // toasted by adminFetch
    } finally {
      setSaving(false);
    }
  };

  const inputClass = (error?: string) =>
    `w-full px-3 py-2 border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 ${
      error ? "border-red-400" : "border-border"
    }`;

  return (
    <Dialog.Root open={!!value} onOpenChange={(open) => !open && !saving && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
        <Dialog.Content
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4"
          aria-describedby={undefined}
        >
          <div className="w-full max-w-xl max-h-[95vh] overflow-y-auto bg-card rounded-t-2xl sm:rounded-2xl shadow-xl">
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card px-6 py-4">
              <Dialog.Title className="text-lg font-semibold">
                {existing ? "Edit design" : "Add a monthly set"}
              </Dialog.Title>
              <button
                onClick={onClose}
                disabled={saving}
                className="p-1 text-muted-foreground hover:text-foreground cursor-pointer"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-5 p-6">
              <div>
                <FieldLabel>Design photo</FieldLabel>
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    choose(e.dataTransfer.files[0]);
                  }}
                  className={`relative flex min-h-52 w-full items-center justify-center overflow-hidden rounded-xl border-2 border-dashed bg-background cursor-pointer ${
                    errors.image ? "border-red-400" : "border-border hover:border-primary"
                  }`}
                >
                  {preview ? (
                    <>
                      <img src={preview} alt="Design preview" className="h-64 w-full object-cover" />
                      <span className="absolute bottom-3 right-3 rounded-full bg-card px-3 py-1.5 text-xs shadow">
                        Replace photo
                      </span>
                    </>
                  ) : (
                    <span className="flex flex-col items-center gap-3 text-center text-sm text-muted-foreground">
                      <UploadCloud className="w-6 h-6 text-primary" />
                      <span>
                        <strong className="font-medium text-primary-dark">Choose a photo</strong> or drag it here
                        <br />
                        <small>JPG, PNG, WebP or GIF up to 5 MB</small>
                      </span>
                    </span>
                  )}
                </button>
                <input
                  ref={inputRef}
                  type="file"
                  accept={IMAGE_TYPES.join(",")}
                  className="hidden"
                  onChange={(e) => choose(e.target.files?.[0])}
                />
                {errors.image && <ErrorText>{errors.image}</ErrorText>}
              </div>

              <div>
                <div className="flex justify-between">
                  <FieldLabel>Title</FieldLabel>
                  <span className="text-xs text-muted-foreground">
                    {title.length}/{TITLE_MAX}
                  </span>
                </div>
                <input
                  value={title}
                  maxLength={TITLE_MAX}
                  onChange={(e) => setTitle(e.target.value)}
                  className={inputClass(errors.title)}
                  placeholder="Cherry Blossom Aura"
                />
                {errors.title && <ErrorText>{errors.title}</ErrorText>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel>Price in euros</FieldLabel>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-sm text-muted-foreground">€</span>
                    <input
                      type="number"
                      min={1}
                      max={PRICE_MAX}
                      step="0.01"
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      className={`${inputClass(errors.price)} pl-7`}
                      placeholder="95"
                    />
                  </div>
                  {errors.price && <ErrorText>{errors.price}</ErrorText>}
                </div>
                <div>
                  <FieldLabel>Duration</FieldLabel>
                  <div className="relative">
                    <input
                      type="number"
                      min={DURATION_MIN}
                      max={DURATION_MAX}
                      step={15}
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      className={`${inputClass(errors.duration)} pr-12`}
                      placeholder="120"
                    />
                    <span className="absolute right-3 top-2 text-xs text-muted-foreground">min</span>
                  </div>
                  {durationNumber > 0 && !errors.duration && (
                    <p className="mt-1.5 text-xs text-muted-foreground">{formatMinutes(durationNumber)}</p>
                  )}
                  {errors.duration && <ErrorText>{errors.duration}</ErrorText>}
                </div>
              </div>

              <div>
                <div className="flex justify-between">
                  <FieldLabel>
                    Description <span className="font-normal text-muted-foreground">optional</span>
                  </FieldLabel>
                  <span className="text-xs text-muted-foreground">
                    {description.length}/{DESCRIPTION_MAX}
                  </span>
                </div>
                <textarea
                  value={description}
                  maxLength={DESCRIPTION_MAX}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className={`${inputClass()} resize-none`}
                  placeholder="What makes this design special?"
                />
              </div>

              {existing && (
                <p className="rounded-lg bg-primary-light/50 p-3 text-xs text-foreground">
                  Changing the price only applies to future bookings. Existing bookings keep their
                  original price.
                </p>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={saving}
                  className="flex-1 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-secondary transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={save}
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer disabled:opacity-50"
                >
                  {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                  {saving ? "Saving..." : existing ? "Save changes" : "Publish design"}
                </button>
              </div>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="mb-1.5 block text-sm font-medium">{children}</label>;
}

function ErrorText({ children }: { children: React.ReactNode }) {
  return <p className="mt-1.5 text-xs text-red-600">{children}</p>;
}
