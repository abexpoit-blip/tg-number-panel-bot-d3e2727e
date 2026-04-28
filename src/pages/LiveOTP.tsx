import { useEffect, useRef, useState } from "react";
import { Radio } from "lucide-react";
import { api } from "@/lib/api";
import PageHeader from "@/components/layout/PageHeader";

export default function LiveOTP() {
  const [list, setList] = useState<any[]>([]);
  const [tick, setTick] = useState(0);
  const seenRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    const fetchData = () => api.sms.list().then((d) => { setList(d); setTick((t) => t + 1); }).catch(() => {});
    fetchData();
    const id = setInterval(fetchData, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <PageHeader
        title="Live OTP feed"
        subtitle="Auto-refreshing every 5s · Last 100 incoming SMS"
        actions={
          <div className="flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1.5 text-xs text-muted-foreground">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
            </span>
            Live · #{tick}
          </div>
        }
      />

      <div className="glass-card overflow-hidden p-0">
        <table className="data-table">
          <thead><tr><th>Time</th><th>Country</th><th>Service</th><th>Number</th><th>OTP</th><th>User</th><th>Paid</th><th>Group</th></tr></thead>
          <tbody>
            {list.map((s) => {
              const isNew = !seenRef.current.has(s.id);
              if (isNew) seenRef.current.add(s.id);
              return (
                <tr key={s.id} className={isNew ? "animate-fade-in-up" : ""}>
                  <td className="text-muted-foreground">{new Date(s.received_at).toLocaleTimeString()}</td>
                  <td><span className="mr-1 text-lg">{s.country_flag || "🏳️"}</span>{s.country_name || "—"}</td>
                  <td>{s.service_emoji || "📱"} {s.service_name || "—"}</td>
                  <td><span className="code-pill">+{s.msisdn}</span></td>
                  <td><span className="font-mono text-base font-bold text-primary">{s.otp_code || "—"}</span></td>
                  <td>{s.first_name || "—"} {s.username && <span className="text-muted-foreground">@{s.username}</span>}</td>
                  <td><span className="font-mono text-success">${Number(s.paid_amount || 0).toFixed(4)}</span></td>
                  <td>{s.posted_to_group ? <span className="pill-green">posted</span> : <span className="pill-neutral">—</span>}</td>
                </tr>
              );
            })}
            {list.length === 0 && (
              <tr><td colSpan={8} className="py-12 text-center text-muted-foreground">
                <Radio className="mx-auto mb-2 h-6 w-6 animate-pulse" /> Waiting for incoming OTP…
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
