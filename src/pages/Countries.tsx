import { useEffect, useState } from "react";
import { Plus, Save, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import PageHeader from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

interface Country { id: number; code: string; name: string; dial_code: string; flag: string; custom_emoji_id?: string | null; enabled: boolean }

export default function Countries() {
  const [list, setList] = useState<Country[]>([]);
  const [draft, setDraft] = useState({ code: "", name: "", dial_code: "+", flag: "🏳️", custom_emoji_id: "", enabled: true });

  const load = () => api.countries.list().then(setList).catch((e) => toast.error(e.message));
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!draft.code || !draft.name) return toast.error("Code and name required");
    try { await api.countries.create(draft); setDraft({ code: "", name: "", dial_code: "+", flag: "🏳️", custom_emoji_id: "", enabled: true }); load(); toast.success("Country added"); }
    catch (e: any) { toast.error(e.message); }
  };
  const save = async (c: Country) => {
    if (c.enabled && !c.custom_emoji_id) {
      if (!confirm(`"${c.name}" is enabled but has no premium flag emoji ID — users will see plain unicode (${c.flag}) only. Save anyway?`)) return;
    }
    try { await api.countries.update(c.id, c); toast.success("Saved"); load(); } catch (e: any) { toast.error(e.message); }
  };
  const del = async (id: number) => { if (!confirm("Delete country?")) return; try { await api.countries.remove(id); toast.success("Deleted"); load(); } catch (e: any) { toast.error(e.message); } };
  const patch = (id: number, k: keyof Country, v: any) => setList(list.map((x) => x.id === id ? { ...x, [k]: v } : x));

  return (
    <>
      <PageHeader title="Countries" subtitle="Country list shown to users" />

      <div className="glass-card mb-6 p-5">
        <div className="grid gap-3 sm:grid-cols-[80px_1fr_100px_80px_180px_auto]">
          <Input placeholder="ISO2" value={draft.code} onChange={(e) => setDraft({ ...draft, code: e.target.value.toUpperCase() })} />
          <Input placeholder="Name" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          <Input placeholder="+39" value={draft.dial_code} onChange={(e) => setDraft({ ...draft, dial_code: e.target.value })} />
          <Input placeholder="🇮🇹" value={draft.flag} onChange={(e) => setDraft({ ...draft, flag: e.target.value })} />
          <Input placeholder="premium flag emoji ID" value={draft.custom_emoji_id} onChange={(e) => setDraft({ ...draft, custom_emoji_id: e.target.value })} />
          <Button onClick={create} className="bg-gradient-primary text-primary-foreground"><Plus className="mr-1 h-4 w-4" /> Add</Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          🏳️ <b>Premium flag emoji ID</b>: forward a flag from the <a className="underline" href="https://t.me/addemoji/FlagsByKoylli" target="_blank" rel="noreferrer">FlagsByKoylli</a> pack to <code>@idstickerbot</code> and paste the numeric ID here. The bot will render it as <code>&lt;tg-emoji&gt;</code> for premium users.
        </p>
      </div>

      <div className="glass-card overflow-hidden p-0">
        <table className="data-table">
          <thead><tr><th>ID</th><th>Flag</th><th>Code</th><th>Name</th><th>Dial</th><th>Premium ID</th><th>Enabled</th><th></th></tr></thead>
          <tbody>
            {list.map((c) => (
              <tr key={c.id}>
                <td className="text-muted-foreground">#{c.id}</td>
                <td className="text-2xl">{c.flag}</td>
                <td><Input value={c.code} onChange={(e) => patch(c.id, "code", e.target.value.toUpperCase())} className="h-8 w-20" /></td>
                <td><Input value={c.name} onChange={(e) => patch(c.id, "name", e.target.value)} className="h-8 w-48" /></td>
                <td><Input value={c.dial_code} onChange={(e) => patch(c.id, "dial_code", e.target.value)} className="h-8 w-24" /></td>
                <td>
                  <div className="flex items-center gap-1">
                    <Input value={c.custom_emoji_id ?? ""} onChange={(e) => patch(c.id, "custom_emoji_id", e.target.value)} className="h-8 w-44 font-mono text-xs" placeholder="—" />
                    {c.enabled && !c.custom_emoji_id && (
                      <span title="Missing premium flag ID — users see plain unicode" className="text-amber-400">⚠</span>
                    )}
                  </div>
                </td>
                <td><Switch checked={c.enabled} onCheckedChange={(v) => patch(c.id, "enabled", v)} /></td>
                <td className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="secondary" onClick={() => save(c)}><Save className="h-3.5 w-3.5" /></Button>
                    <Button size="sm" variant="destructive" onClick={() => del(c.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                  </div>
                </td>
              </tr>
            ))}
            {list.length === 0 && (<tr><td colSpan={8} className="py-10 text-center text-muted-foreground">No countries yet.</td></tr>)}
          </tbody>
        </table>
      </div>
    </>
  );
}
