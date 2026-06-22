/**
 * Shared formatting utilities for paper data.
 * NOTE: buildMediaUrl, formatDuration, arxivAbsUrl
 * are already defined in utils/mediaUrl.ts — import from there.
 * This file adds text/display formatters only.
 */

/**
 * Format authors field — handles: string[], JSON string, plain string, null.
 * Returns a display string like "Author A, Author B"
 */
export function formatAuthors(authors: string[] | string | null | undefined): string {
  if (!authors) return 'Không rõ tác giả';
  if (Array.isArray(authors)) {
    return authors.length > 0 ? authors.join(', ') : 'Không rõ tác giả';
  }
  // Try parse as JSON
  try {
    const parsed = JSON.parse(authors);
    if (Array.isArray(parsed)) return parsed.join(', ');
  } catch {
    // not JSON, use as plain string
  }
  return authors;
}

/**
 * Format a date string "YYYY-MM-DD" to "DD/MM/YYYY" Vietnamese locale.
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Không rõ';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('vi-VN', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch {
    return dateStr;
  }
}

/**
 * Format a datetime ISO string to readable date + time.
 */
export function formatDateTime(dtStr: string | null | undefined): string {
  if (!dtStr) return 'Không rõ';
  try {
    const d = new Date(dtStr);
    if (isNaN(d.getTime())) return dtStr;
    return d.toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return dtStr;
  }
}

/**
 * Format a score (0–N float) as a percentage-like display, e.g. 0.873 → "87.3"
 * Supports both [0,1] and larger values (passthrough).
 */
export function formatScore(score: number | null | undefined): string {
  if (score == null) return '—';
  // If score looks like it's already a 0-100 value, display as-is
  if (score > 1) return score.toFixed(1);
  return (score * 100).toFixed(1);
}

/**
 * Truncate text to maxLength characters, appending "…"
 */
export function truncateText(text: string | null | undefined, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + '…';
}

/**
 * Build a short author list (first 3 authors, then "+N more")
 */
export function formatAuthorsShort(
  authors: string[] | string | null | undefined,
  max = 3
): string {
  const full = formatAuthors(authors);
  if (full === 'Không rõ tác giả') return full;
  const parts = full.split(', ');
  if (parts.length <= max) return full;
  return `${parts.slice(0, max).join(', ')} +${parts.length - max} khác`;
}
