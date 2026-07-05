import { useEffect, useState } from "react";
import { Clock, DollarSign, Loader2 } from "lucide-react";
import { fetchServices, type Service } from "../api";

export function Services() {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadServices();
  }, []);

  async function loadServices() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchServices();
      setServices(data);
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
            From classic manicures to intricate nail art, we offer a full range
            of services tailored to you.
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
              onClick={loadServices}
              className="text-sm text-primary hover:text-primary-dark underline underline-offset-4"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && services.length === 0 && (
          <p className="text-center text-muted-foreground py-16">
            No services available at the moment.
          </p>
        )}

        {!loading && !error && services.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service) => (
              <div
                key={service.id}
                className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="font-[family-name:var(--font-serif)] text-lg font-semibold mb-3">
                  {service.name}
                </h3>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4" />
                    {service.duration_minutes} min
                  </span>
                  <span className="flex items-center gap-1.5">
                    <DollarSign className="w-4 h-4" />
                    {service.price.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
