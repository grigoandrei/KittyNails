import { Sparkles } from "lucide-react";

interface HeroProps {
  onBookNow: () => void;
}

export function Hero({ onBookNow }: HeroProps) {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center px-4 pt-20 overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/photo-1555231955-348aa2312e19.avif')",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-[#FEF7F5]/75 via-[#FEF7F5]/60 to-[#FEF7F5]" />

      <div className="relative text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-secondary px-4 py-2 rounded-full mb-6">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm text-muted-foreground">
            Nail Art Studio
          </span>
        </div>

        <h1 className="font-[family-name:var(--font-serif)] text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-semibold leading-tight mb-6">
          Nails that speak{" "}
          <span className="text-primary italic">your style</span>
        </h1>

        <p className="text-lg sm:text-xl text-muted-foreground max-w-xl mx-auto mb-10 leading-relaxed">
          Experience the artistry of Asian nail design. From minimalist chic to
          intricate art, we bring your vision to life.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onBookNow}
            className="bg-primary text-primary-foreground px-8 py-3.5 rounded-full text-base font-medium hover:bg-primary-dark transition-colors shadow-md hover:shadow-lg cursor-pointer"
          >
            Book Your Appointment
          </button>
          <a
            href="#services"
            className="text-muted-foreground hover:text-foreground transition-colors text-sm underline underline-offset-4"
          >
            View our services
          </a>
        </div>
      </div>
    </section>
  );
}
