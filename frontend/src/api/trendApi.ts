import client from './client';
import type { TrendAnalyzeResponse, TrendHealthResponse } from '../types/trend';

/**
 * Retrieve already computed trend clusters from database
 */
export const getTrends = async (limitTopics = 20, limitPapersPerTopic = 10): Promise<TrendAnalyzeResponse> => {
  const response = await client.get<TrendAnalyzeResponse>('/trend', {
    params: {
      limit_topics: limitTopics,
      limit_papers_per_topic: limitPapersPerTopic
    }
  });
  return response.data;
};

/**
 * Trigger the Trend Agent to analyze trends and save results to DB
 * Increased timeout to 60 seconds because BERTopic clustering takes time
 */
export const analyzeTrends = async (limit?: number): Promise<TrendAnalyzeResponse> => {
  const response = await client.post<TrendAnalyzeResponse>('/trend/analyze', null, {
    params: limit ? { limit } : undefined,
    timeout: 60000 // 60 seconds timeout
  });
  return response.data;
};

/**
 * Verify connectivity with the Trend Agent microservice
 */
export const getTrendHealth = async (): Promise<TrendHealthResponse> => {
  const response = await client.get<TrendHealthResponse>('/trend/health');
  return response.data;
};
