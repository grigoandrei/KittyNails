import { useState, useEffect } from "react";
import { motion } from "motion/react";

function getTimeLeft(endsAt: Date) {
  const diff = endsAt.getTime() - Date.now();
  if (diff <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true };

  return {
    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
    hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
    minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
    seconds: Math.floor((diff % (1000 * 60)) / 1000),
    expired: false,
  };
}

function Unit({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <motion.div
        key={value}
        initial={{ opacity: 0.4, scale: 0.88 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="font-[family-name:var(--font-serif)] text-4xl md:text-5xl tabular-nums leading-none text-halloween-amber [text-shadow:0_0_24px_rgba(244,168,32,0.45)]"
      >
        {String(value).padStart(2, "0")}
      </motion.div>
      <span className="text-[9px] tracking-[0.35em] uppercase text-halloween-ivory/35">
        {label}
      </span>
    </div>
  );
}

function Colon() {
  return (
    <span className="font-[family-name:var(--font-serif)] text-3xl pb-4 select-none text-halloween-amber/30">
      :
    </span>
  );
}

interface HalloweenCountdownProps {
  endsAt: Date;
  caption: string;
  onExpire: () => void;
}

export function HalloweenCountdown({ endsAt, caption, onExpire }: HalloweenCountdownProps) {
  const [time, setTime] = useState(() => getTimeLeft(endsAt));

  useEffect(() => {
    const id = setInterval(() => setTime(getTimeLeft(endsAt)), 1000);
    return () => clearInterval(id);
  }, [endsAt]);

  useEffect(() => {
    if (time.expired) onExpire();
  }, [time.expired, onExpire]);

  if (time.expired) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.25 }}
      className="relative flex flex-col items-center gap-6 py-10 px-8 rounded-2xl mx-auto max-w-lg bg-white/[0.03] border border-halloween-amber/10"
    >
      <SpiderWeb className="absolute top-0 left-0 opacity-20" />
      <SpiderWeb className="absolute top-0 right-0 opacity-20 scale-x-[-1]" />

      <p className="text-[10px] tracking-[0.4em] uppercase relative z-10 text-halloween-ivory/40">
        Offer ends in
      </p>

      <div className="flex items-end gap-3 sm:gap-4 relative z-10">
        <Unit value={time.days} label="days" />
        <Colon />
        <Unit value={time.hours} label="hours" />
        <Colon />
        <Unit value={time.minutes} label="min" />
        <Colon />
        <Unit value={time.seconds} label="sec" />
      </div>

      <p className="text-xs relative z-10 text-halloween-ivory/30">{caption}</p>
    </motion.div>
  );
}

function SpiderWeb({ className }: { className?: string }) {
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" className={className} aria-hidden="true">
      <line x1="0" y1="0" x2="72" y2="0" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="72" y2="72" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="0" y2="72" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="36" y2="72" stroke="#F4A820" strokeWidth="0.8" />
      <line x1="0" y1="0" x2="72" y2="36" stroke="#F4A820" strokeWidth="0.8" />
      <path d="M18 0 Q9 9 0 18" stroke="#F4A820" strokeWidth="0.8" fill="none" />
      <path d="M36 0 Q18 18 0 36" stroke="#F4A820" strokeWidth="0.8" fill="none" />
      <path d="M54 0 Q27 27 0 54" stroke="#F4A820" strokeWidth="0.8" fill="none" />
      <path d="M72 0 Q36 36 0 72" stroke="#F4A820" strokeWidth="0.8" fill="none" />
    </svg>
  );
}
