/**
 * Validate a Telegram premium custom_emoji_id pasted by the admin.
 *
 * Telegram's `custom_emoji_id` is the numeric `id` from a `MessageEntity` of
 * type `custom_emoji`. In the Bot API JSON it's serialized as a STRING of
 * digits (it doesn't fit in a JS number — it's a 64-bit int).
 *
 * Real examples from the user's RawDataBot dump:
 *   "5224511339703056124"
 *   "5323261730283863478"
 *   "5330115548900501467"
 *
 * Rules:
 *   - required (non-empty after trim)
 *   - digits only
 *   - 18–20 chars (every real Telegram ID we've seen is 19; we allow ±1 for safety)
 *   - no `<tg-emoji>` tag, no leading "id:", no quotes — just the bare number
 */
export type EmojiIdValidation =
  | { ok: true; cleaned: string; warning?: string }
  | { ok: false; error: string };

export function validateEmojiId(raw: string | null | undefined): EmojiIdValidation {
  const v = (raw ?? "").trim();
  if (!v) return { ok: false, error: "Empty — paste a custom_emoji_id from @RawDataBot." };

  // Catch common copy-paste mistakes early with helpful messages.
  if (/<tg-emoji/i.test(v)) {
    return { ok: false, error: "Paste only the numeric id, not the <tg-emoji> tag." };
  }
  if (/^["'`]|["'`]$/.test(v)) {
    return { ok: false, error: "Remove surrounding quotes — paste digits only." };
  }
  if (/^https?:\/\//i.test(v)) {
    return { ok: false, error: "That looks like a URL. Paste the numeric custom_emoji_id." };
  }
  if (/[^\d]/.test(v)) {
    return { ok: false, error: "Must be digits only (no spaces, letters, or symbols)." };
  }

  if (v.length < 18) {
    return { ok: false, error: `Too short (${v.length} digits). Real IDs are ~19 digits.` };
  }
  if (v.length > 20) {
    return { ok: false, error: `Too long (${v.length} digits). Real IDs are ~19 digits.` };
  }

  // Soft warning: 19 is the canonical length we've observed.
  if (v.length !== 19) {
    return { ok: true, cleaned: v, warning: `Unusual length (${v.length}). Double-check it works.` };
  }

  return { ok: true, cleaned: v };
}
