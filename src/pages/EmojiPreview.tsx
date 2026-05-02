import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import PageHeader from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface Service { id: number; name: string; emoji: string; custom_emoji_id?: string | null; enabled: boolean }
interface Country { id: number; name: string; code: string; flag: string; custom_emoji_id?: string | null; enabled: boolean }

/**
 * Render a Telegram-like preview of premium emoji.
 * Telegram clients fetch the actual sticker by ID — in the admin we can't load
 * those CDN assets directly (they're protected), so we show the unicode fallback
 * with a glowing badge to confirm an ID is present and will render in-app.
 */
function EmojiTag({ unicode, id, label }: { unicode: string; id?: string | null; label?: string }) {
  if (id) {
    return (
      <span
        className="relative inline-flex items-center justify-center"
        title={`Premium emoji ID: ${id}${label ? ` (${label})` : ""}`}
      >
        <span className="text-xl leading-none">{unicode}</span>
        <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-primary shadow-glow" />
      </span>
    );
  }
  return <span className="text-xl leading-none opacity-60" title="Plain unicode (no premium ID)">{unicode}</span>;
}

export default function EmojiPreview() {
  const [services, setServices] = useState<Service[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [svcId, setSvcId] = useState<number | null>(null);
  const [ctryId, setCtryId] = useState<number | null>(null);
  const [phone, setPhone] = useState("+255627228779");
  const [otp, setOtp] = useState("140-335");

  useEffect(() => {
    Promise.all([api.services.list(), api.countries.list()])
      .then(([s, c]) => {
        setServices(s);
        setCountries(c);
        if (s.length && svcId == null) setSvcId(s[0].id);
        if (c.length && ctryId == null) setCtryId(c[0].id);
      })
      .catch((e) => toast.error(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const svc = useMemo(() => services.find((s) => s.id === svcId) || null, [services, svcId]);
  const ctry = useMemo(() => countries.find((c) => c.id === ctryId) || null, [countries, ctryId]);

  const missingSvc = services.filter((s) => s.enabled && !s.custom_emoji_id);
  const missingCtry = countries.filter((c) => c.enabled && !c.custom_emoji_id);
  const totalEnabled = services.filter((s) => s.enabled).length + countries.filter((c) => c.enabled).length;
  const missingTotal = missingSvc.length + missingCtry.length;
  const coverage = totalEnabled === 0 ? 100 : Math.round(((totalEnabled - missingTotal) / totalEnabled) * 100);

  return (
    <>
      <PageHeader
        title="Emoji Preview"
        subtitle="Validate premium custom emoji rendering before users see it"
      />

      {/* Coverage banner */}
      <div className="glass-card mb-6 p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {missingTotal === 0 ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-amber-400" />
            )}
            <div>
              <div className="font-display text-lg font-semibold">
                Emoji coverage: <span className={coverage === 100 ? "text-emerald-400" : "text-amber-400"}>{coverage}%</span>
              </div>
              <div className="text-xs text-muted-foreground">
                {missingTotal === 0
                  ? "All enabled services & countries have premium emoji IDs configured."
                  : `${missingTotal} enabled item${missingTotal === 1 ? "" : "s"} still use plain unicode (no premium ID).`}
              </div>
            </div>
          </div>
          <div className="h-2 w-full max-w-xs overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-gradient-primary transition-all"
              style={{ width: `${coverage}%` }}
            />
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Live preview */}
        <div className="glass-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="font-display text-base font-semibold">Telegram message preview</h3>
          </div>

          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wider text-muted-foreground">Service</label>
              <select
                className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm"
                value={svcId ?? ""}
                onChange={(e) => setSvcId(+e.target.value)}
              >
                {services.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.emoji} {s.name} {s.custom_emoji_id ? "✓" : "·"}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wider text-muted-foreground">Country</label>
              <select
                className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm"
                value={ctryId ?? ""}
                onChange={(e) => setCtryId(+e.target.value)}
              >
                {countries.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.flag} {c.name} {c.custom_emoji_id ? "✓" : "·"}
                  </option>
                ))}
              </select>
            </div>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+255..." />
            <Input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="OTP code" />
          </div>

          {/* Mock Telegram bubble */}
          <div className="rounded-2xl bg-[#e7f5dc] p-4 text-[#111] shadow-elegant">
            <div className="text-sm leading-relaxed">
              <div className="font-semibold">🔔 New OTP received!</div>
              <div className="mt-2 flex items-center gap-2">
                <EmojiTag unicode={ctry?.flag || "🌍"} id={ctry?.custom_emoji_id} label={ctry?.name} />
                <EmojiTag unicode={svc?.emoji || "📱"} id={svc?.custom_emoji_id} label={svc?.name} />
                <span className="font-semibold">{svc?.name || "Service"}</span>
              </div>
              <div className="mt-1">📱 Number: <code className="rounded bg-black/10 px-1">{phone}</code></div>
              <div>🔑 OTP: <code className="rounded bg-black/10 px-1">{otp}</code></div>
              <div className="mt-2 text-xs opacity-70">Tap below to copy <b>number|otp</b>:</div>
              <div className="mt-2 inline-block rounded-lg bg-white px-3 py-2 text-xs shadow">📋 {phone} | {otp}</div>
            </div>
          </div>

          <div className="mt-3 space-y-1 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-primary shadow-glow" />
              Glow dot = premium emoji ID is set, will animate in Telegram.
            </div>
            <div>⚠ Buttons (green ones in chat) always show plain unicode — Telegram API limitation.</div>
          </div>
        </div>

        {/* Missing IDs panel */}
        <div className="glass-card p-5">
          <h3 className="mb-4 font-display text-base font-semibold">Missing premium emoji IDs</h3>

          <div className="mb-5">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium">Services</span>
              <span className="text-xs text-muted-foreground">{missingSvc.length} of {services.filter((s) => s.enabled).length} missing</span>
            </div>
            {missingSvc.length === 0 ? (
              <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-400">
                ✓ All enabled services have premium IDs.
              </div>
            ) : (
              <ul className="space-y-1">
                {missingSvc.map((s) => (
                  <li key={s.id} className="flex items-center justify-between rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm">
                    <span>{s.emoji} {s.name}</span>
                    <Link to="/services"><Button size="sm" variant="ghost" className="h-7">Fix →</Button></Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium">Countries</span>
              <span className="text-xs text-muted-foreground">{missingCtry.length} of {countries.filter((c) => c.enabled).length} missing</span>
            </div>
            {missingCtry.length === 0 ? (
              <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-400">
                ✓ All enabled countries have premium flag IDs.
              </div>
            ) : (
              <ul className="max-h-72 space-y-1 overflow-auto pr-1">
                {missingCtry.map((c) => (
                  <li key={c.id} className="flex items-center justify-between rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm">
                    <span>{c.flag} {c.name} (+{c.code})</span>
                    <Link to="/countries"><Button size="sm" variant="ghost" className="h-7">Fix →</Button></Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-5 rounded-md bg-muted/30 p-3 text-xs text-muted-foreground">
            💡 Get IDs by sending the exact premium emoji to <a className="underline" href="https://t.me/RawDataBot" target="_blank" rel="noreferrer">@RawDataBot</a>, then copy
            the <code>custom_emoji_id</code> from the returned JSON. Use
            {" "}<a className="underline" href="https://t.me/addemoji/ApplicationEmoji" target="_blank" rel="noreferrer">ApplicationEmoji</a> for services and
            {" "}<a className="underline" href="https://t.me/addemoji/FlagsByKoylli" target="_blank" rel="noreferrer">FlagsByKoylli</a> for flags.
          </div>
        </div>
      </div>
    </>
  );
}
