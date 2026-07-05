export function Gallery() {
  const placeholders = [
    { label: "Minimalist French Tips", color: "bg-pink-100" },
    { label: "Floral Art Design", color: "bg-rose-100" },
    { label: "Chrome Finish", color: "bg-purple-100" },
    { label: "Pastel Ombre", color: "bg-amber-100" },
    { label: "Gemstone Accents", color: "bg-teal-100" },
    { label: "Abstract Line Art", color: "bg-sky-100" },
  ];

  return (
    <section id="gallery" className="py-20 sm:py-28 px-4 bg-secondary">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="font-[family-name:var(--font-serif)] text-3xl sm:text-4xl font-semibold mb-4">
            Our Work
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            A glimpse into the artistry we create for our clients every day.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {placeholders.map((item, index) => (
            <div
              key={index}
              className={`${item.color} rounded-2xl aspect-square flex items-center justify-center p-6 border border-border/50`}
            >
              <span className="text-sm text-muted-foreground text-center font-medium">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
