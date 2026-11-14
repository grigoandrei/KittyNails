import { useEffect, useState } from "react";
import { Clock, Expand, Loader2, Sparkles, X } from "lucide-react";
import { fetchMonthlySets, formatDuration, type MonthlySetDesign } from "../api";
import { INSTAGRAM_HANDLE, INSTAGRAM_URL, InstagramIcon } from "./Instagram";

interface MonthlySetsSectionProps {
  onBook: (design: MonthlySetDesign) => void;
}

/** One-of-one designs the artist wants to do. Booked ones are never listed. */
export function MonthlySetsSection({ onBook }: MonthlySetsSectionProps) {
  const [designs, setDesigns] = useState<MonthlySetDesign[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [viewing, setViewing] = useState<MonthlySetDesign | null>(null);

  useEffect(() => {
    fetchMonthlySets()
      .then(setDesigns)
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!viewing) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setViewing(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [viewing]);

  // Keep the landing page clean if the API is down.
  if (failed) return null;

  return (
    <section id="monthly-sets" className="relative overflow-hidden py-20 sm:py-28 px-4">
      <div className="pointer-events-none absolute -right-24 top-20 h-72 w-72 rounded-full bg-primary-light/45 blur-3xl" />
      <div className="relative max-w-6xl mx-auto">
        <div className="mb-10 sm:mb-14 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <p className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.28em] text-primary-dark">
              <Sparkles className="w-3.5 h-3.5" />
              Artist's pick
            </p>
            <h2 className="font-[family-name:var(--font-serif)] text-3xl sm:text-5xl font-semibold">
              Monthly sets
            </h2>
            <p className="mt-4 max-w-xl text-sm sm:text-base leading-7 text-muted-foreground">
              Sets that show off my creativity, my style and some discounts for you 🤭
            </p>
            <p className="mt-2 max-w-xl text-xs sm:text-sm text-muted-foreground">
              Each set is one of a kind. Once it's booked, it's gone.
            </p>
          </div>
          {!loading && designs.length > 0 && (
            <span className="self-start md:self-auto rounded-full bg-primary-light/60 px-3 py-2 text-xs text-muted-foreground">
              {designs.length} available
            </span>
          )}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-primary animate-spin" />
            <span className="ml-3 text-muted-foreground">Loading designs...</span>
          </div>
        ) : designs.length === 0 ? (
          <MonthlySetEmpty />
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {designs.map((design) => (
              <article
                key={design.id}
                className="group overflow-hidden rounded-[28px] border border-border bg-card shadow-[0_12px_40px_rgba(83,52,65,0.07)]"
              >
                <button
                  type="button"
                  onClick={() => setViewing(design)}
                  className="relative block aspect-[4/4.6] w-full overflow-hidden bg-primary-light/30 cursor-zoom-in"
                  aria-label={`View ${design.title} full screen`}
                >
                  {design.image_url && (
                    <img
                      src={design.image_url}
                      alt={design.title}
                      loading="lazy"
                      className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]"
                    />
                  )}
                  <span className="absolute bottom-4 right-4 grid h-9 w-9 place-items-center rounded-full bg-white/90 text-foreground opacity-0 shadow-sm backdrop-blur transition group-hover:opacity-100">
                    <Expand className="w-4 h-4" />
                  </span>
                </button>
                <div className="p-5 sm:p-6">
                  <h3 className="font-[family-name:var(--font-serif)] text-xl font-semibold mb-2">
                    {design.title}
                  </h3>
                  <div className="mb-3 flex items-center justify-between gap-4">
                    <span className="font-[family-name:var(--font-serif)] text-2xl text-primary-dark">
                      €{design.price}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Clock className="w-3.5 h-3.5" /> {formatDuration(design.duration_minutes)}
                    </span>
                  </div>
                  {design.description && (
                    <p className="mb-5 text-sm leading-6 text-muted-foreground">{design.description}</p>
                  )}
                  <button
                    type="button"
                    onClick={() => onBook(design)}
                    className="w-full rounded-full bg-primary px-5 py-3 text-sm font-medium text-primary-foreground transition hover:bg-primary-dark cursor-pointer"
                  >
                    Book this design
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {viewing && (
        <div
          className="fixed inset-0 z-[60] flex flex-col items-center justify-center gap-4 bg-[#2e2227]/95 p-4 sm:p-10"
          onClick={() => setViewing(null)}
          role="dialog"
          aria-label={viewing.title}
        >
          <button
            className="absolute right-5 top-5 grid h-11 w-11 place-items-center rounded-full bg-white/10 text-white hover:bg-white/20 cursor-pointer"
            onClick={() => setViewing(null)}
            aria-label="Close full screen photo"
          >
            <X className="w-5 h-5" />
          </button>
          {viewing.image_url && (
            <img
              src={viewing.image_url}
              alt={viewing.title}
              className="max-h-[75vh] max-w-full rounded-2xl object-contain shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          )}
          <div
            className="flex flex-wrap items-center justify-center gap-4 text-white"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="font-[family-name:var(--font-serif)] text-xl">{viewing.title}</span>
            <span className="text-white/70 text-sm">
              €{viewing.price} · {formatDuration(viewing.duration_minutes)}
            </span>
            <button
              type="button"
              onClick={() => {
                const design = viewing;
                setViewing(null);
                onBook(design);
              }}
              className="rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary-dark cursor-pointer"
            >
              Book this design
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function MonthlySetEmpty() {
  return (
    <div className="rounded-[28px] border border-dashed border-primary-light bg-card px-6 py-16 text-center shadow-sm">
      <div className="mx-auto mb-5 grid h-14 w-14 place-items-center rounded-full bg-primary-light/60 text-primary-dark">
        <Sparkles className="w-5 h-5" />
      </div>
      <h3 className="font-[family-name:var(--font-serif)] text-2xl font-semibold">
        Fresh ideas are blooming
      </h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        All current designs have found their person. Follow along for the next drop.
      </p>
      <a
        href={INSTAGRAM_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary-light px-5 py-2.5 text-sm font-medium text-primary-dark"
      >
        <InstagramIcon className="w-4 h-4" /> {INSTAGRAM_HANDLE}
      </a>
    </div>
  );
}
