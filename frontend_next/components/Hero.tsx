import { motion } from "framer-motion";
import { CheckCircle2, ScanSearch, Sparkles } from "lucide-react";

const chips = [
  { label: "Detect", icon: ScanSearch },
  { label: "Verify", icon: CheckCircle2 },
  { label: "Correct", icon: Sparkles }
];

export function Hero() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="hero-glow relative overflow-hidden rounded-[28px] border border-warm-border bg-cream-50 px-6 py-8 shadow-soft md:px-10 md:py-11"
    >
      <div className="relative z-10 max-w-3xl">
        <div className="mb-5 inline-flex items-center rounded-full border border-sage-200 bg-white/65 px-3 py-1 text-sm font-medium text-sage-700">
          AI reliability workspace
        </div>
        <h1 className="text-5xl font-semibold tracking-[-0.03em] text-warm-text md:text-7xl">TemporalGuard</h1>
        <p className="mt-4 max-w-2xl text-lg leading-8 text-warm-muted md:text-xl">
          Verify, correct, and trust time-sensitive AI answers.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          {chips.map(({ label, icon: Icon }) => (
            <span key={label} className="secondary-pill inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold">
              <Icon size={16} aria-hidden="true" />
              {label}
            </span>
          ))}
        </div>
      </div>
    </motion.section>
  );
}
