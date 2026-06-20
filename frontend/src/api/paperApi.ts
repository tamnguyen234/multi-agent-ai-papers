import client from './client';
import type { Paper, PapersListResponse } from '../types/paper';

/**
 * Fetch all papers (with optional search query).
 * GET /api/v1/papers?skip=0&limit=100&search=...
 * Returns Paper[] directly (no wrapper).
 */
export async function getPapers(params?: {
  skip?: number;
  limit?: number;
  search?: string;
}): Promise<PapersListResponse> {
  const response = await client.get<PapersListResponse>('/papers', {
    params: {
      skip: params?.skip ?? 0,
      limit: params?.limit ?? 100,
      ...(params?.search ? { search: params.search } : {}),
    },
  });
  return response.data;
}

/**
 * Fetch a single paper by ID.
 * GET /api/v1/papers/{paperId}
 */
export async function getPaperById(paperId: number | string): Promise<Paper> {
  const response = await client.get<Paper>(`/papers/${paperId}`);
  return response.data;
}

/**
 * Generate audio abstract for a specific paper.
 * POST /api/v1/papers/{paperId}/audio-abstract
 */
export async function generateAudioAbstract(
  paperId: number | string,
  payload?: {
    voice?: string;
    language?: string;
    force?: boolean;
  }
): Promise<{
  mode: 'existing' | 'generated';
  audio_url: string;
  duration_seconds: number | null;
  voice: string | null;
  language: string | null;
  audio_abstract: any;
}> {
  const response = await client.post(`/papers/${paperId}/audio-abstract`, payload || {}, {
    timeout: 300000, // 300 seconds timeout for TTS synthesis
  });
  return response.data;
}

