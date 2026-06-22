/**
 * Build an absolute media URL from a backend-served relative path.
 *
 * Backend serves static files at: http://127.0.0.1:8000/<path>
 * e.g. audio_abstract_path = "static/audio/paper_123.mp3"
 *      → full URL = "http://127.0.0.1:8000/static/audio/paper_123.mp3"
 */
const BACKEND_ORIGIN = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

/**
 * Returns an absolute URL for the given media path.
 * If the path is already an absolute URL (starts with http), return as-is.
 * If the path is null/undefined, return null.
 */
export function buildMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${BACKEND_ORIGIN}${normalized}`;
}

/**
 * Format duration in seconds to mm:ss string.
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Format a score (0–N float/integer) to a percentage-like string or count.
 * Handles scores > 1 as raw upvote counts, formatting integers as integers and floats with decimals.
 */
export function formatScore(score: number | null | undefined): string {
  if (score == null) return '—';
  if (score > 1) {
    return Number.isInteger(score) ? score.toString() : score.toFixed(1);
  }
  return (score * 100).toFixed(1);
}

/**
 * Build URL from external_id
 * If the input is already a full http/https URL, return it directly (with version tag stripped if applicable).
 */
export function externalAbsUrl(external_id: string): string {
  if (external_id.startsWith('http://') || external_id.startsWith('https://')) {
    return external_id.replace(/v\d+$/, '');
  }
  const clean = external_id.replace(/v\d+$/, '');
  // Default to huggingface if no URL protocol was matched
  return `https://huggingface.co/papers/${clean}`;
}
