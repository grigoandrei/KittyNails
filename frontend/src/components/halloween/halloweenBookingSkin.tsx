import type { BookingSkin } from "../BookingModal";

// Halloween look for the booking modal. Pass it as `skin` to BookingModal
// while the promo runs. Colors live in the `.halloween-skin` rules in index.css.
export const halloweenBookingSkin: BookingSkin = {
  className: "halloween-skin",
  overlayClassName: "!bg-[#0C0520]/70",
  header: <HalloweenModalHeader />,
  dayBadge: (date) =>
    date.getMonth() === 9 && date.getDate() === 31 ? (
      <span className="absolute -top-0.5 -right-0.5 text-[9px] leading-none" aria-hidden="true">
        🎃
      </span>
    ) : null,
  confirmedTitle: "Booking Confirmed 🎃",
};

function HalloweenModalHeader() {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 h-16 overflow-hidden" aria-hidden="true">
      <div className="h-px w-full bg-[linear-gradient(90deg,transparent,#F4A820_40%,#C47A10_60%,transparent)]" />
      <SpiderWeb className="absolute top-0 left-0" />
      <SpiderWeb className="absolute top-0 right-0 scale-x-[-1]" />
    </div>
  );
}

function SpiderWeb({ className }: { className?: string }) {
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" className={`opacity-20 ${className}`}>
      <line x1="0" y1="0" x2="64" y2="0" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="64" y2="64" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="0" y2="64" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="32" y2="64" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="64" y2="32" stroke="#F4A820" strokeWidth="0.8" />
      <path d="M16 0 Q8 8 0 16" stroke="#F4A820" strokeWidth="0.8" fill="none" />
      <path d="M32 0 Q16 16 0 32" stroke="#F4A820" strokeWidth="0.8" fill="none" />
      <path d="M48 0 Q24 24 0 48" stroke="#F4A820" strokeWidth="0.8" fill="none" />
      <path d="M64 0 Q32 32 0 64" stroke="#F4A820" strokeWidth="0.8" fill="none" />
    </svg>
  );
}
