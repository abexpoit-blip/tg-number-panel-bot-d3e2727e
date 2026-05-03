import { Facebook, Instagram, Send, MessageCircle, Music2, Phone, Smartphone } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface BrandSpec {
  Icon: LucideIcon;
  bg: string; // tailwind bg-*
  fg: string; // tailwind text-*
  label: string;
}

/** Resolve a service to a branded icon/colour. Matches by `code` first, then by `name`. */
function resolve(input: { code?: string | null; name?: string | null } | string | null | undefined): BrandSpec {
  const s = typeof input === "string" ? input : `${input?.code ?? ""} ${input?.name ?? ""}`;
  const k = s.toLowerCase();
  if (k.includes("whatsapp")) return { Icon: MessageCircle, bg: "bg-emerald-500/15", fg: "text-emerald-400", label: "WhatsApp" };
  if (k.includes("facebook") || k === "fb") return { Icon: Facebook, bg: "bg-blue-500/15", fg: "text-blue-400", label: "Facebook" };
  if (k.includes("instagram") || k === "ig") return { Icon: Instagram, bg: "bg-pink-500/15", fg: "text-pink-400", label: "Instagram" };
  if (k.includes("telegram") || k === "tg") return { Icon: Send, bg: "bg-sky-500/15", fg: "text-sky-400", label: "Telegram" };
  if (k.includes("tiktok") || k === "tt") return { Icon: Music2, bg: "bg-fuchsia-500/15", fg: "text-fuchsia-400", label: "TikTok" };
  if (k.includes("signal") || k.includes("call")) return { Icon: Phone, bg: "bg-indigo-500/15", fg: "text-indigo-400", label: "Call" };
  return { Icon: Smartphone, bg: "bg-muted", fg: "text-muted-foreground", label: "Service" };
}

interface ServiceBadgeProps {
  service?: { code?: string | null; name?: string | null; emoji?: string | null } | null;
  /** Override label (else the service name is shown) */
  label?: string;
  size?: "sm" | "md";
  /** Show only the icon (compact) */
  iconOnly?: boolean;
  className?: string;
}

/**
 * Branded service chip used across the admin panel for visual parity with the
 * Telegram bot messages — shown as a coloured icon + (optionally) the service name.
 * The Telegram premium <tg-emoji> is intentionally NOT rendered here — premium
 * emojis only render inside Telegram clients, not on the web admin.
 */
export default function ServiceBadge({ service, label, size = "sm", iconOnly = false, className = "" }: ServiceBadgeProps) {
  const spec = resolve(service ?? null);
  const text = label ?? service?.name ?? spec.label;
  const dim = size === "md" ? "h-4 w-4" : "h-3.5 w-3.5";
  const pad = iconOnly ? "p-1.5" : size === "md" ? "px-2.5 py-1" : "px-2 py-0.5";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md ${spec.bg} ${spec.fg} ${pad} ${className}`}>
      <spec.Icon className={dim} />
      {!iconOnly && <span className="text-xs font-medium">{text}</span>}
    </span>
  );
}

export { resolve as resolveServiceBrand };
