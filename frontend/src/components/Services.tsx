import { useEffect, useState } from "react";
import { Clock, Loader2 } from "lucide-react";

interface NailType {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
}

interface DesignTier {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
}

export function Services() {
  const [nailTypes, setNailTypes] = useState<NailType[]>([]);
  const [designTiers, setDesignTiers] = useState<DesignTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [ntRes, dtRes] = await Promise.all([
        fetch("/api/nail-types"),
        fetch("/api/design-tiers"),
      ]);
      if (!ntRes.ok || !dtRes.ok) throw new Error("Failed to load");
      setNailTypes(await ntRes.json());
      setDesignTiers(await dtRes.json());
    } catch {
      setError("Unable to load services. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="services" className="py-20 sm:py-28 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="font-[family-name:var(--font-serif)] text-3xl sm:text-4xl font-semibold mb-4">
            Our Services
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            From classic manicures to intricate nail art — upload a photo and our AI will recommend the best option for you.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-primary animate-spin" />
            <span className="ml-3 text-muted-foreground">Loading services...</span>
          </div>
        )}

        {error && (
          <div className="text-center py-16">
            <p className="text-destructive mb-4">{error}</p>
            <button
              onClick={loadData}
              className="text-sm text-primary hover:text-primary-dark underline underline-offset-4 cursor-pointer"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-12">
            {/* Nail Types */}
            <div>
              <h3 className="font-[family-name:var(--font-serif)] text-xl font-semibold mb-4 text-center">
                Nail Types
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
                {nailTypes.map((nt) => (
                  <div
                    key={nt.id}
                    className="bg-card rounded-2xl p-5 border border-border shadow-sm text-center"
                  >
                    <h4 className="font-semibold text-lg mb-2">{nt.name}</h4>
                    <p className="text-2xl font-bold text-primary mb-1">
                      €{nt.price.toFixed(0)}
                    </p>
                    <p className="text-sm text-muted-foreground flex items-center justify-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {nt.duration_minutes} min
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Design Tiers */}
            <div>
              <h3 className="font-[family-name:var(--font-serif)] text-xl font-semibold mb-4 text-center">
                Design Complexity
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto">
                {designTiers.map((dt) => (
                  <div
                    key={dt.id}
                    className="bg-card rounded-2xl p-5 border border-border shadow-sm text-center"
                  >
                    <h4 className="font-semibold text-lg mb-2">{dt.name}</h4>
                    <p className="text-2xl font-bold text-primary mb-1">
                      +€{dt.price.toFixed(0)}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <p className="text-center text-sm text-muted-foreground">
              Total price = nail type + design tier. Upload a photo when booking and our AI will recommend the best combination.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
