import { useEffect, useState } from "react";
import { Users, UserPlus, Phone, Radio, Inbox, Wallet, DollarSign, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import PageHeader from "@/components/layout/PageHeader";

interface Stats {
  users?: number;
  users_24h?: number;
  numbers_available?: number;
  numbers_total?: number;
  otp_24h?: number;
  otp_total?: number;
  pending_withdrawals?: number;
  paid_total?: number;
}

const STATS = [
  { key: "users", label: "Total users", icon: Users, accent: "from-primary to-primary-glow" },
  { key: "users_24h", label: "New users (24h)", icon: UserPlus, accent: "from-accent to-primary-glow" },
  { key: "numbers", label: "Numbers available", icon: Phone, accent: "from-primary to-accent" },
  { key: "otp_24h", label: "OTPs (24h)", icon: Radio, accent: "from-accent to-success" },
  { key: "otp_total", label: "OTPs total", icon: Inbox, accent: "from-primary-glow to-accent" },
  { key: "pending_withdrawals", label: "Pending withdrawals", icon: Wallet, accent: "from-warning to-destructive" },
  { key: "paid_total", label: "Paid out total", icon: DollarSign, accent: "from-success to-accent" },
] as const;

export default function Dashboard() {
  const [s, setS] = useState<Stats | null>(null);

  useEffect(() => { api.dashboard().then(setS).catch(() => setS({})); }, []);

  const value = (k: string) => {
    if (!s) return "—";
    if (k === "numbers") return `${s.numbers_available ?? 0} / ${s.numbers_total ?? 0}`;
    if (k === "paid_total") return `$${Number(s.paid_total ?? 0).toFixed(2)}`;
    return String((s as any)[k] ?? 0);
  };

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Live operational overview" />
      {!s ? (
        <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Loading…</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map(({ key, label, icon: Icon, accent }) => (
            <div key={key} className="stat-card group relative overflow-hidden">
              <div className={`absolute -right-8 -top-8 h-28 w-28 rounded-full bg-gradient-to-br ${accent} opacity-15 blur-2xl transition-opacity group-hover:opacity-30`} />
              <div className="relative flex items-start justify-between">
                <div>
                  <div className="label">{label}</div>
                  <div className="value">{value(key)}</div>
                </div>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted/60 text-primary">
                  <Icon className="h-4 w-4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
