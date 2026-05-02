import { useState } from "react";
import { CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { validateEmojiId } from "@/lib/validateEmojiId";

interface Props {
  value: string;
  onChange: (v: string) => void;
  className?: string;
  placeholder?: string;
  /** Show "missing" warning ⚠ when value is empty (e.g. for enabled rows). */
  showMissingWarning?: boolean;
  /** Compact = inline row mode (no full-width). */
  compact?: boolean;
}

/**
 * Input + "Validate" button for a Telegram custom_emoji_id.
 * Pure client-side check (no network) — Telegram has no public lookup endpoint.
 */
export default function EmojiIdField({
  value,
  onChange,
  className = "h-8 w-44 font-mono text-xs",
  placeholder = "—",
  showMissingWarning = false,
  compact = true,
}: Props) {
  const [status, setStatus] = useState<"idle" | "ok" | "warn" | "bad">("idle");

  const handleValidate = () => {
    const res = validateEmojiId(value);
    if (!res.ok) {
      setStatus("bad");
      toast.error(`Invalid emoji ID: ${res.error}`);
      return;
    }
    if (res.cleaned !== value) onChange(res.cleaned); // strip whitespace
    if (res.warning) {
      setStatus("warn");
      toast.warning(res.warning);
    } else {
      setStatus("ok");
      toast.success("Looks like a valid Telegram custom_emoji_id ✓");
    }
  };

  const handleChange = (v: string) => {
    onChange(v);
    if (status !== "idle") setStatus("idle");
  };

  return (
    <div className={compact ? "flex items-center gap-1" : "flex items-center gap-2"}>
      <Input
        value={value ?? ""}
        onChange={(e) => handleChange(e.target.value)}
        className={className}
        placeholder={placeholder}
      />
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={handleValidate}
        title="Validate format of this custom_emoji_id"
        className="h-8 px-2"
      >
        <ShieldCheck className="h-3.5 w-3.5" />
      </Button>
      {status === "ok" && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
      {status === "warn" && <span className="text-amber-400" title="Format is acceptable but unusual">⚠</span>}
      {status === "bad" && <XCircle className="h-4 w-4 text-rose-400" />}
      {status === "idle" && showMissingWarning && !value && (
        <span title="Missing premium emoji ID — users see plain unicode" className="text-amber-400">⚠</span>
      )}
    </div>
  );
}
