import { motion } from "motion/react";
import { format, parseISO } from "date-fns";
import { X } from "lucide-react";
import type { Promotion } from "../../api";

export const BANNER_HEIGHT = 40;

interface HalloweenBannerProps {
  promo: Promotion;
  onClose: () => void;
  onBookNow: () => void;
}

export function HalloweenBanner({ promo, onClose, onBookNow }: HalloweenBannerProps) {
  const period = `${format(parseISO(promo.start), "MMM d")} to ${format(parseISO(promo.end), "MMM d")}`;

  return (
    <motion.div
      initial={{ y: -BANNER_HEIGHT, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: -BANNER_HEIGHT, opacity: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-[60] flex items-center justify-between px-4 md:px-8 border-b border-orange-400/20 bg-[linear-gradient(90deg,#12052B_0%,#1F0A3A_40%,#2B0D40_60%,#12052B_100%)]"
      style={{ height: BANNER_HEIGHT }}
    >
      {/* Subtle bat decoration */}
      <svg
        className="absolute left-4 top-1/2 -translate-y-1/2 opacity-20 hidden lg:block"
        width="18"
        height="10"
        viewBox="0 0 18 10"
        fill="#F4A820"
        aria-hidden="true"
      >
        <path d="M9 4c-1-2-3-4-5-4C2 0 0 2 0 4c1 0 2-1 3-1 0 1-1 2-1 3 1-1 2-1 3-2 0 1 0 2 1 2 0-1 1-2 2-2s2 1 2 2c1 0 1-1 1-2 1 1 2 1 3 2 0-1-1-2-1-3 1 0 2 1 3 1 0-2-2-4-4-4C12 0 10 2 9 4z" />
      </svg>

      <div className="flex-1 flex items-center justify-center gap-2.5 min-w-0">
        <span aria-label="pumpkin" role="img" className="text-base leading-none">🎃</span>
        <span className="text-[11px] md:text-xs tracking-wide text-[#FFDCB4]/85 truncate">
          <span className="md:hidden">{promo.name}: {promo.percent}% off · {period}</span>
          <span className="hidden md:inline">
            {promo.name} week · {promo.percent}% off {promo.design_tiers.join(" & ")} designs · appointments {period}
          </span>
        </span>
        <button
          onClick={onBookNow}
          className="hidden md:inline-flex text-[11px] tracking-wide ml-0.5 text-halloween-amber hover:text-halloween-amber-light transition-colors cursor-pointer"
        >
          Book now →
        </button>
        <span aria-label="sparkles" role="img" className="text-sm leading-none">✨</span>
      </div>

      <button
        onClick={onClose}
        aria-label="Dismiss Halloween banner"
        className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded text-[#FFC896]/45 hover:text-[#FFC896]/85 transition-colors cursor-pointer"
      >
        <X size={13} />
      </button>
    </motion.div>
  );
}
