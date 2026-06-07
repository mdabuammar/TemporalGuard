import { AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert } from "lucide-react";

const toneMap: Record<string, string> = {
  safe: "border-green-200 bg-green-50 text-green-800",
  supported: "border-green-200 bg-green-50 text-green-800",
  corrected: "border-amber-200 bg-amber-50 text-amber-800",
  outdated: "border-amber-200 bg-amber-50 text-amber-800",
  unverified: "border-orange-200 bg-orange-50 text-orange-800",
  high: "border-red-200 bg-red-50 text-red-700",
  critical: "border-red-200 bg-red-50 text-red-700"
};

function getTone(label: string) {
  const lower = label.toLowerCase();
  const key = Object.keys(toneMap).find((item) => lower.includes(item));
  return key ? toneMap[key] : "border-sage-200 bg-sage-100 text-sage-700";
}

function getIcon(label: string) {
  const lower = label.toLowerCase();
  if (lower.includes("safe") || lower.includes("supported")) return CheckCircle2;
  if (lower.includes("correct")) return RefreshCw;
  if (lower.includes("high") || lower.includes("critical")) return ShieldAlert;
  return AlertTriangle;
}

export function StatusBadge({ label }: { label: string }) {
  const Icon = getIcon(label);
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold ${getTone(label)}`}>
      <Icon size={15} aria-hidden="true" />
      {label.replaceAll("_", " ").toUpperCase()}
    </span>
  );
}
