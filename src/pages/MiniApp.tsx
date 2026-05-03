import { useEffect, useState } from "react";
import ServiceBadge from "@/components/ServiceBadge";
import { api } from "@/lib/api";

/**
 * Telegram Mini App (WebApp) — opened from the bot's "✨ Open Premium Menu"
 * button. Because button labels in Telegram cannot render <tg-emoji> premium
 * icons or HTML, this Mini App is the supported workaround: it renders fully
 * branded icons (WhatsApp/Facebook/Telegram/TikTok/etc.) inside Telegram and
 * sends the chosen service back to the bot via Telegram.WebApp.sendData.
 */
declare global {
  interface Window { Telegram?: { WebApp?: any } }
}

export default function MiniApp() {
  const [services, setServices] = useState<any[]>([]);
  const [countries, setCountries] = useState<any[]>([]);
  const [svc, setSvc] = useState<any | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    tg?.ready();
    tg?.expand();
    api.services.list().then(setServices).catch(() => {});
    api.countries.list().then((rows) => setCountries(rows.filter((c: any) => c.enabled !== false))).catch(() => {});
  }, []);

  const pick = (payload: object) => {
    const tg = window.Telegram?.WebApp;
    if (tg?.sendData) { tg.sendData(JSON.stringify(payload)); tg.close(); }
  };

  return (
    <div className="min-h-screen bg-background p-4 text-foreground">
      {!svc ? (
        <>
          <h1 className="mb-4 font-display text-xl font-semibold">✨ Select a Service</h1>
          <div className="grid grid-cols-2 gap-3">
            {services.map((s) => (
              <button key={s.id} onClick={() => setSvc(s)}
                className="glass-card flex items-center gap-2 p-3 text-left hover:bg-accent">
                <ServiceBadge service={s} size="md" />
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <button onClick={() => setSvc(null)} className="mb-3 text-sm text-muted-foreground">← Back</button>
          <h1 className="mb-4 font-display text-xl font-semibold">
            <ServiceBadge service={svc} size="md" /> · Pick a country
          </h1>
          <div className="grid grid-cols-2 gap-2">
            {countries.map((c) => (
              <button key={c.id} onClick={() => pick({ service_id: svc.id, country_id: c.id })}
                className="glass-card flex items-center gap-2 p-3 text-left hover:bg-accent">
                <span className="text-xl">{c.flag}</span><span className="text-sm">{c.name}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
