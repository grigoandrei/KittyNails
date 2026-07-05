import { Star } from "lucide-react";

const testimonials = [
  {
    name: "Sarah M.",
    text: "Absolutely love my nails! The attention to detail is incredible. Best nail salon I have ever been to.",
    rating: 5,
  },
  {
    name: "Emily K.",
    text: "The Korean nail art techniques are next level. My friends always ask where I get my nails done.",
    rating: 5,
  },
  {
    name: "Jessica L.",
    text: "So relaxing and the results are always perfect. The team is talented and professional.",
    rating: 5,
  },
];

export function Testimonials() {
  return (
    <section id="testimonials" className="py-20 sm:py-28 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="font-[family-name:var(--font-serif)] text-3xl sm:text-4xl font-semibold mb-4">
            What Our Clients Say
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            We take pride in making every client feel special and beautiful.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="bg-card rounded-2xl p-6 border border-border shadow-sm"
            >
              <div className="flex gap-0.5 mb-4">
                {Array.from({ length: testimonial.rating }).map((_, i) => (
                  <Star
                    key={i}
                    className="w-4 h-4 fill-primary text-primary"
                  />
                ))}
              </div>
              <p className="text-foreground mb-4 leading-relaxed">
                &ldquo;{testimonial.text}&rdquo;
              </p>
              <p className="text-sm text-muted-foreground font-medium">
                {testimonial.name}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
