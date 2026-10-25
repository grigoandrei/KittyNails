import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { format, parseISO } from "date-fns";
import { Clock } from "lucide-react";
import {
  applyPromo,
  fetchDesignTiers,
  fetchNailTypes,
  promoEndsAt,
  type DesignTier,
  type NailType,
  type Promotion,
} from "../../api";
import { HalloweenCountdown } from "./HalloweenCountdown";

const TIER_EMOJI: Record<string, string> = { Medium: "🕸", Advanced: "🦇" };

interface Deal {
  id: string;
  nailType: NailType;
  designTier: DesignTier;
}

interface HalloweenSectionProps {
  promo: Promotion;
  onBookNow: () => void;
}

export function HalloweenSection({ promo, onBookNow }: HalloweenSectionProps) {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [expired, setExpired] = useState(false);
  const endsAt = useMemo(() => promoEndsAt(promo), [promo]);

  // Every nail type that uses a design tier, paired with every promo tier.
  useEffect(() => {
    Promise.all([fetchNailTypes(), fetchDesignTiers()])
      .then(([nailTypes, designTiers]) => {
        const tiers = designTiers.filter((dt) => promo.design_tiers.includes(dt.name));
        setDeals(
          nailTypes
            .filter((nt) => nt.name !== "Japanese Manicure")
            .flatMap((nt) => tiers.map((dt) => ({ id: `${nt.id}-${dt.id}`, nailType: nt, designTier: dt })))
        );
      })
      .catch(() => setDeals([]));
  }, [promo]);

  if (expired) return null;

  const period = `${format(parseISO(promo.start), "MMM d")} to ${format(parseISO(promo.end), "MMM d, yyyy")}`;

  return (
    <section
      id="halloween"
      className="relative py-24 px-6 overflow-hidden bg-[linear-gradient(180deg,#0C0520_0%,#170B2E_55%,#0C0520_100%)]"
    >
      <Particles />

      <div
        className="absolute right-[-60px] top-1/2 -translate-y-1/2 text-[320px] leading-none select-none pointer-events-none opacity-[0.03] hidden xl:block"
        aria-hidden="true"
      >
        🎃
      </div>

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-14">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-[11px] tracking-[0.4em] uppercase mb-3 text-halloween-amber"
          >
            {promo.name} week · {promo.percent}% off
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.08 }}
            className="font-[family-name:var(--font-serif)] text-4xl md:text-5xl text-halloween-ivory"
          >
            Hauntingly beautiful nails
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.14 }}
            className="text-sm leading-relaxed mt-4 max-w-md mx-auto text-halloween-ivory/50"
          >
            Get {promo.percent}% off {promo.design_tiers.join(" and ")} designs for appointments
            from {period}. Book before they vanish into the night.
          </motion.p>
        </div>

        <div className="mb-14">
          <HalloweenCountdown
            endsAt={endsAt}
            caption={`Appointments ${period}`}
            onExpire={() => setExpired(true)}
          />
        </div>

        {deals.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-3xl mx-auto">
            {deals.map((deal, i) => (
              <DealCard key={deal.id} deal={deal} promo={promo} index={i} onBook={onBookNow} />
            ))}
          </div>
        )}

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="text-center text-xs mt-10 text-halloween-ivory/40"
        >
          Upload your inspo photo when booking. Our AI picks the design tier and the discount
          applies automatically.
        </motion.p>
      </div>
    </section>
  );
}

function DealCard({ deal, promo, index, onBook }: {
  deal: Deal;
  promo: Promotion;
  index: number;
  onBook: () => void;
}) {
  const { nailType, designTier } = deal;
  const price = nailType.price + designTier.price;

  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.07 }}
      whileHover={{ y: -3 }}
      className="flex flex-col gap-4 rounded-2xl p-6 bg-white/[0.04] border border-halloween-amber/10 hover:border-halloween-amber/30 hover:bg-halloween-amber/5 transition-colors"
    >
      <span className="self-start text-[10px] tracking-[0.2em] uppercase px-2.5 py-0.5 rounded-full bg-halloween-amber/15 text-halloween-amber">
        {promo.percent}% off
      </span>

      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-xl flex items-center justify-center text-xl flex-shrink-0 bg-halloween-amber/10">
          {TIER_EMOJI[designTier.name] ?? "🎃"}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-[family-name:var(--font-serif)] text-lg mb-1 leading-snug text-halloween-ivory">
            {nailType.name} · {designTier.name} design
          </h3>
          <p className="text-sm leading-relaxed text-halloween-ivory/50">
            {designTier.name === "Advanced"
              ? "Detailed hand painted art. Bats, webs, ghosts and more."
              : "Spooky accents on a few nails. Moons, pumpkins and glitter."}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-1">
        <div>
          <span className="text-sm mr-2 line-through text-halloween-ivory/35">€{price.toFixed(2)}</span>
          <span className="font-[family-name:var(--font-serif)] text-xl text-halloween-amber">
            €{applyPromo(price, promo).toFixed(2)}
          </span>
          <div className="flex items-center gap-1 text-xs mt-0.5 text-halloween-ivory/35">
            <Clock size={11} />
            <span>{nailType.duration_minutes + designTier.duration_minutes} min</span>
          </div>
        </div>
        <button
          onClick={onBook}
          className="text-xs tracking-wide px-4 py-2 rounded-full transition-all duration-200 cursor-pointer bg-halloween-amber/10 text-halloween-amber border border-halloween-amber/20 hover:bg-halloween-amber hover:text-halloween-night hover:border-halloween-amber"
        >
          Book
        </button>
      </div>
    </motion.div>
  );
}

const DOTS = [
  { x: "8%", y: "15%", r: 1.5, delay: 0 },
  { x: "22%", y: "72%", r: 1, delay: 0.8 },
  { x: "38%", y: "8%", r: 2, delay: 0.4 },
  { x: "55%", y: "85%", r: 1.2, delay: 1.2 },
  { x: "68%", y: "20%", r: 1, delay: 0.6 },
  { x: "80%", y: "60%", r: 1.8, delay: 0.2 },
  { x: "92%", y: "40%", r: 1, delay: 1.0 },
  { x: "14%", y: "45%", r: 1.3, delay: 0.3 },
  { x: "75%", y: "88%", r: 1, delay: 0.9 },
];

function Particles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {DOTS.map((dot, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-halloween-amber"
          style={{ left: dot.x, top: dot.y, width: dot.r * 2, height: dot.r * 2 }}
          animate={{ opacity: [0.08, 0.35, 0.08], scale: [1, 1.4, 1] }}
          transition={{ duration: 3.5 + i * 0.3, repeat: Infinity, delay: dot.delay, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
