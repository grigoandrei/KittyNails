import gallery1 from "../assets/gallery-1.jpeg";
import gallery2 from "../assets/gallery-2.jpeg";
import gallery3 from "../assets/gallery-3.jpeg";
import gallery4 from "../assets/gallery-4.jpeg";
import gallery5 from "../assets/gallery-5.jpeg";
import gallery6 from "../assets/gallery-6.jpeg";

export function Gallery() {
  const images = [
    { src: gallery1, alt: "Nail design by KittyNails" },
    { src: gallery2, alt: "Nail design by KittyNails" },
    { src: gallery3, alt: "Nail design by KittyNails" },
    { src: gallery4, alt: "Nail design by KittyNails" },
    { src: gallery5, alt: "Nail design by KittyNails" },
    { src: gallery6, alt: "Nail design by KittyNails" },
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
          {images.map((image, index) => (
            <div
              key={index}
              className="rounded-2xl aspect-square overflow-hidden border border-border/50"
            >
              <img
                src={image.src}
                alt={image.alt}
                loading="lazy"
                className="w-full h-full object-cover"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
