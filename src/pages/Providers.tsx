import { useEffect, useState } from "react";
import { Plus, Save, Trash2, KeyRound, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import PageHeader from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

interface Provider {
  id: number;
  name: string;
  type: string;
  base_url: string;
  username: string;
  password: string;
  currency: string;
  enabled: boolean;
  poll_interval: number;
  has_cookies: boolean;
  last_login_at: string | null;
  last_poll_at: string | null;
  last_error: string | null;
}

const blankDraft = {
  name: "",
  type: "iprn",
  base_url: "https://panel.iprn-sms.com",
  username: "",
  password: "",
  currency: "EUR",
  enabled: true,
  poll_interval: 15,
};

export default function Providers() {
  const [list, setList] = useState<Provider[]>([]);
  const [draft, setDraft] = useState(blankDraft);

  const load = () => api.providers.list().then(setList).catch((e: any) => toast.error(e.message));
  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, []);

  const create = async () => {
    if (!draft.name || !draft.username || !draft.password) return toast.error("Name, username and password are required");
    try { await api.providers.create(draft); setDraft(blankDraft); load(); toast.success("Provider added"); }
    catch (e: any) { toast.error(e.message); }
  };
  const save = async (p: Provider) => {
    const body: any = { ...p };
    if (body.password === "********") delete body.password;
    try { await api.providers.update(p.id, body); toast.success("Saved"); load(); }
    catch (e: any) { toast.error(e.message); }
  };
  const del = async (id: number) => {
    if (!confirm("Delete provider? Linked numbers stay but lose their provider link.")) return;
    try { await api.providers.remove(id); toast.success("Deleted"); load(); } catch (e: any) { toast.error(e.message); }
  };
  const clearCookies = async (id: number) => {
    try { await api.providers.clearCookies(id); toast.success("Cookies cleared, will re-login on next poll"); load(); }
    catch (e: any) { toast.error(e.message); }
  };
  const patch = (id: number, k: keyof Provider, v: any) =>
    setList(list.map((x) => (x.id === id ? { ...x, [k]: v } : x)));

  return (
    <>
      <PageHeader title="Providers" subtitle="External SMS gateways (IPRN-SMS, Seven1Tel, …). Cookies are saved automatically — login is fast next time." />

      <div className="glass-card mb-6 p-5">
        <h3 className="mb-3 font-display text-base font-semibold">Add provider</h3>
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-7">
          <Input placeholder="Label (e.g. IPRN EUR)" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          <Select value={draft.type} onValueChange={(v) => setDraft({ ...draft, type: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="iprn">IPRN-SMS</SelectItem>
              <SelectItem value="seven1tel" disabled>Seven1Tel (soon)</SelectItem>
            </SelectContent>
          </Select>
          <Input placeholder="Username" value={draft.username} onChange={(e) => setDraft({ ...draft, username: e.target.value })} />
          <Input placeholder="Password" type="password" value={draft.password} onChange={(e) => setDraft({ ...draft, password: e.target.value })} />
          <Select value={draft.currency} onValueChange={(v) => setDraft({ ...draft, currency: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="EUR">EUR €</SelectItem>
              <SelectItem value="USD">USD $</SelectItem>
              <SelectItem value="GBP">GBP £</SelectItem>
            </SelectContent>
          </Select>
          <Input type="number" placeholder="Poll s" value={draft.poll_interval} onChange={(e) => setDraft({ ...draft, poll_interval: +e.target.value })} />
          <Button onClick={create} className="bg-gradient-primary text-primary-foreground">
            <Plus className="mr-1 h-4 w-4" /> Add
          </Button>
        </div>
        <Input className="mt-3" placeholder="Base URL" value={draft.base_url} onChange={(e) => setDraft({ ...draft, base_url: e.target.value })} />
      </div>

      <div className="glass-card overflow-hidden p-0">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Name</th><th>Type</th><th>User</th><th>Password</th>
              <th>Currency</th><th>Poll</th><th>Status</th><th>Last poll</th><th>Enabled</th><th></th>
            </tr>
          </thead>
          <tbody>
            {list.map((p) => (
              <tr key={p.id}>
                <td className="text-muted-foreground">#{p.id}</td>
                <td><Input value={p.name} onChange={(e) => patch(p.id, "name", e.target.value)} className="h-8 w-40" /></td>
                <td className="text-muted-foreground">{p.type}</td>
                <td><Input value={p.username} onChange={(e) => patch(p.id, "username", e.target.value)} className="h-8 w-32" /></td>
                <td><Input type="password" value={p.password} onChange={(e) => patch(p.id, "password", e.target.value)} className="h-8 w-32" /></td>
                <td>
                  <Select value={p.currency} onValueChange={(v) => patch(p.id, "currency", v)}>
                    <SelectTrigger className="h-8 w-24"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="GBP">GBP</SelectItem>
                    </SelectContent>
                  </Select>
                </td>
                <td><Input type="number" value={p.poll_interval} onChange={(e) => patch(p.id, "poll_interval", +e.target.value)} className="h-8 w-20" /></td>
                <td>
                  {p.last_error ? (
                    <span className="inline-flex items-center gap-1 text-destructive text-xs" title={p.last_error}>
                      <AlertCircle className="h-3.5 w-3.5" /> error
                    </span>
                  ) : p.has_cookies ? (
                    <span className="inline-flex items-center gap-1 text-emerald-500 text-xs">
                      <CheckCircle2 className="h-3.5 w-3.5" /> logged in
                    </span>
                  ) : (
                    <span className="text-muted-foreground text-xs">no session</span>
                  )}
                </td>
                <td className="text-muted-foreground text-xs">{p.last_poll_at ? new Date(p.last_poll_at).toLocaleTimeString() : "—"}</td>
                <td><Switch checked={p.enabled} onCheckedChange={(v) => patch(p.id, "enabled", v)} /></td>
                <td className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="secondary" onClick={() => save(p)}><Save className="h-3.5 w-3.5" /></Button>
                    <Button size="sm" variant="secondary" onClick={() => clearCookies(p.id)} title="Force re-login">
                      <KeyRound className="h-3.5 w-3.5" />
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => del(p.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                  </div>
                </td>
              </tr>
            ))}
            {list.length === 0 && (
              <tr><td colSpan={11} className="py-10 text-center text-muted-foreground">No providers yet. Add IPRN-SMS above to start scraping OTPs.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
