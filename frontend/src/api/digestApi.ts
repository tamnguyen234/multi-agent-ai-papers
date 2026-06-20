import client from './client';
import type { DigestResponse, RunDigestJobResponse } from '../types/digest';

/**
 * Fetch today's digest from the backend.
 * GET /api/v1/digests/today
 */
export async function getTodayDigest(): Promise<DigestResponse> {
  const response = await client.get<DigestResponse>('/digests/today');
  return response.data;
}

/**
 * Fetch a specific digest by ID.
 * GET /api/v1/digests/{digest_id}
 */
export async function getDigestById(digestId: number): Promise<DigestResponse> {
  const response = await client.get<DigestResponse>(`/digests/${digestId}`);
  return response.data;
}

/**
 * Trigger the daily digest job (dev/demo only).
 * POST /api/v1/dev/run-daily-digest-job
 */
export async function runDailyDigestJob(): Promise<RunDigestJobResponse> {
  const response = await client.post<RunDigestJobResponse>('/dev/run-daily-digest-job');
  return response.data;
}
