/**
 * Only http(s) links reach an href. Source URLs come from the database, which a
 * deployment may fetch from elsewhere (DER_DB_URL); a `javascript:` or `data:`
 * URL there must render as plain text, not a clickable link.
 */
export function safeHref(url: string | null | undefined): string | null {
  if (!url) return null;
  const first = url.split(";")[0].trim();
  try {
    const parsed = new URL(first);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : null;
  } catch {
    return null;
  }
}
