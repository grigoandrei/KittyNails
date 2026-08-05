import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";

interface NailType {
  id: string;
  name: string;
}

export function Footer() {
  const [nailTypes, setNailTypes] = useState<NailType[]>([]);

  useEffect(() => {
    fetch("/api/nail-types")
      .then((r) => r.json())
      .then(setNailTypes)
      .catch(() => {
        /* silently fail in footer */
      });
  }, []);

  return (
    <footer className="bg-foreground text-white py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-primary" />
              <span className="font-[family-name:var(--font-serif)] text-xl font-semibold">
                KittyNails
              </span>
            </div>
            <p className="text-white/60 text-sm leading-relaxed">
              Korean nail art studio specializing in minimalist, elegant designs
              that express your unique style.
            </p>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4 text-white/80">
              Services
            </h4>
            <ul className="space-y-2">
              {nailTypes.length > 0 ? (
                nailTypes.map((nt) => (
                  <li key={nt.id}>
                    <span className="text-sm text-white/60">{nt.name}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-white/40">Loading...</li>
              )}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4 text-white/80">
              Visit Us
            </h4>
            <div className="text-sm text-white/60 space-y-2">
              <p>123 Blossom Lane</p>
              <p>Suite 4B</p>
              <p>Open Tue - Sat, 10am - 7pm</p>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 mt-12 pt-8 text-center">
          <p className="text-xs text-white/40">
            &copy; {new Date().getFullYear()} KittyNails. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
