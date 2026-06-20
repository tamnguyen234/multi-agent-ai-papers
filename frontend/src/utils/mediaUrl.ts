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
 * Format a score (0–1 float) to a percentage-like string, e.g. "87.3"
 */
export function formatScore(score: number): string {
  return (score * 100).toFixed(1);
}

/**
 * Extract arXiv short ID from full arxiv_id (e.g. "2406.12345v1" → "2406.12345")
 * If the input is already a full http/https URL, return it directly (with version tag stripped if applicable).
 */
export function arxivAbsUrl(arxiv_id: string): string {
  if (arxiv_id.startsWith('http://') || arxiv_id.startsWith('https://')) {
    return arxiv_id.replace(/v\d+$/, '');
  }
  const clean = arxiv_id.replace(/v\d+$/, '');
  return `https://arxiv.org/abs/${clean}`;
}
