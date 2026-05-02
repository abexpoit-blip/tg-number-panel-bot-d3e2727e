import { useEffect, useMemo, useRef, useState } from "react";
import { Radio, Search, X, Pause, Play } from "lucide-react";
import { api } from "@/lib/api";
import PageHeader from "@/components/layout/PageHeader";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface OtpRow {
  id: number;
  phone: string;
  code: string | null;
  service_hint: string | null;
  raw_text: string;
  created_at: string;
  service_name?: string;
  service_emoji?: string;
  country_name?: string;
  country_flag?: string;
  username?: string;
  first_name?: string;
}

export default function LiveOTP() {
  const [list, setList] = useState<OtpRow[]>([]);
  const [tick, setTick] = useState(0);
  const [paused, setPaused] = useState(false);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<OtpRow | null>(null);
  const seenRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      if (paused) return;
      try {
        const d = await api.sms.list();
        if (!cancelled) {
          setList(d as OtpRow[]);
          setTick((t) => t + 1);
        }
      } catch { /* silent */ }
    };
    fetchData();
    const id = setInterval(fetchData, 4000);
    return () => { cancelled = true; clearInterval(id); };
  }, [paused]);

  const filtered = useMemo(() => {
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter((r) =>
      r.phone?.includes(q) ||
      r.code?.toLowerCase().includes(q) ||
      r.service_name?.toLowerCase().includes(q) ||
      r.country_name?.toLowerCase().includes(q) ||
      r.username?.toLowerCase().includes(q) ||
      r.raw_text?.toLowerCase().includes(q)
    );
  }, [list, search]);

  const counts = useMemo(() => ({
    total: list.length,
    last_hour: list.filter((r) => Date.now() - new Date(r.created_at).getTime() < 3600000).length,
    delivered: list.filter((r) => !!r.username || !!r.first_name).length,
  }), [list]);

  return (
    <>
      <PageHeader
        title="Live OTP feed"
        subtitle="Streaming directly from providers · last 200 events"
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={paused ? "default" : "secondary"}
              onClick={() => setPaused((p) => !p)}
              className={paused ? "bg-warning text-warning-foreground" : ""}
            >
              {paused ? <><Play className="mr-1.5 h-3.5 w-3.5" /> Resume</> : <><Pause className="mr-1.5 h-3.5 w-3.5" /> Pause</>}
            </Button>
            <div className="flex items-center gap-2 rounded-full border border-border bg-card/60 px-3.5 py-1.5 text-xs text-muted-foreground backdrop-blur">
              <span className={paused ? "h-2 w-2 rounded-full bg-warning" : "live-dot"} />
              <span className="ml-2 font-mono">#{tick}</span>
            </div>
          </div>
        }
      />

      {/* Quick stats strip */}
      <div className="grid gap-4 sm:grid-cols-3 mb-6">
        <div className="glass-card p-4">
          <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Total events</div>
          <div className="mt-1.5 font-display text-2xl font-bold tabular-nums">{counts.total}</div>
        </div>
        <div className="glass-card p-4">
          <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Last hour</div>
          <div className="mt-1.5 font-display text-2xl font-bold tabular-nums text-gradient-primary">{counts.last_hour}</div>
        </div>
        <div className="glass-card p-4">
          <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Delivered to user</div>
          <div className="mt-1.5 font-display text-2xl font-bold tabular-nums text-success">{counts.delivered}</div>
        </div>
      </div>

      {/* Search */}
      <div className="glass-card mb-4 p-3 flex items-center gap-2">
        <Search className="h-4 w-4 text-muted-foreground ml-2" />
        <Input
          placeholder="Filter by number, OTP, service, country, user…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border-0 bg-transparent focus-visible:ring-0"
        />
        {search && (
          <Button size="sm" variant="ghost" onClick={() => setSearch("")}><X className="h-3.5 w-3.5" /></Button>
        )}
      </div>

      <div className="glass-card overflow-hidden p-0">
        <table className="data-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Country</th>
              <th>Service</th>
              <th>Number</th>
              <th>OTP</th>
              <th>Delivered to</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => {
              const isNew = !seenRef.current.has(s.id);
              if (isNew) seenRef.current.add(s.id);
              return (
                <tr
                  key={s.id}
                  onClick={() => setDetail(s)}
                  className={`cursor-pointer ${isNew ? "animate-slide-in-right" : ""}`}
                >
                  <td className="text-muted-foreground tabular-nums text-xs">
                    {new Date(s.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </td>
                  <td><span className="mr-1.5 text-base">{s.country_flag || "🏳️"}</span>{s.country_name || "—"}</td>
                  <td><span className="mr-1">{s.service_emoji || "📱"}</span>{s.service_name || s.service_hint || "—"}</td>
                  <td><span className="code-pill">+{s.phone}</span></td>
                  <td>
                    <span className="font-mono text-base font-bold text-gradient-primary tabular-nums">
                      {s.code || "—"}
                    </span>
                  </td>
                  <td>
                    {s.first_name || s.username ? (
                      <span className="text-sm">
                        {s.first_name || ""} {s.username && <span className="text-muted-foreground">@{s.username}</span>}
                      </span>
                    ) : (
                      <span className="pill-neutral">unmatched</span>
                    )}
                  </td>
                  <td>
                    <span className="pill-purple">{s.service_hint || "scraper"}</span>
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="py-16 text-center text-muted-foreground">
                  <Radio className="mx-auto mb-2 h-6 w-6 animate-pulse text-primary" />
                  {search ? "No events match your filter." : "Waiting for incoming OTP…"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Detail dialog */}
      <Dialog open={!!detail} onOpenChange={(o) => !o && setDetail(null)}>
        <DialogContent className="glass-card border-border max-w-2xl">
          <DialogHeader>
            <DialogTitle className="font-display text-xl">
              <span className="mr-2">{detail?.country_flag || "🏳️"}</span>
              +{detail?.phone}
              {detail?.code && (
                <span className="ml-3 font-mono text-gradient-primary">{detail.code}</span>
              )}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Service</div>
                <div className="mt-0.5">{detail?.service_emoji} {detail?.service_name || detail?.service_hint || "—"}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Received</div>
                <div className="mt-0.5 tabular-nums">{detail && new Date(detail.created_at).toLocaleString()}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Delivered to</div>
                <div className="mt-0.5">
                  {detail?.first_name || detail?.username
                    ? <>{detail?.first_name} {detail?.username && <span className="text-muted-foreground">@{detail.username}</span>}</>
                    : <span className="text-muted-foreground">unmatched</span>}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Country</div>
                <div className="mt-0.5">{detail?.country_flag} {detail?.country_name}</div>
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Raw SMS</div>
              <pre className="rounded-lg border border-border bg-input/50 p-3 text-xs font-mono overflow-x-auto whitespace-pre-wrap break-words">
                {detail?.raw_text || "(empty)"}
              </pre>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
