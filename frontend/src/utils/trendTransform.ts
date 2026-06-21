import type { TrendAnalyzeResponse, Topic, TrendPaper } from '../types/trend';

export interface NormalizedTrendData {
  mode: string;
  total_papers: number;
  topic_count: number;
  topics: Topic[];
  topTopic: Topic | null;
}

/**
 * Normalizes and guards the raw trend response from the backend
 */
export const normalizeTrendData = (rawResponse: TrendAnalyzeResponse | null | undefined | any): NormalizedTrendData => {
  const result: NormalizedTrendData = {
    mode: 'unknown',
    total_papers: 0,
    topic_count: 0,
    topics: [],
    topTopic: null,
  };

  if (!rawResponse) {
    return result;
  }

  result.mode = typeof rawResponse.mode === 'string' ? rawResponse.mode : 'unknown';

  const rawTopics = Array.isArray(rawResponse.topics) ? rawResponse.topics : [];
  const uniquePaperIds = new Set<number>();
  const normalizedTopics: Topic[] = [];

  for (const t of rawTopics) {
    if (!t || typeof t !== 'object') continue;

    // Normalize papers under this topic
    const rawPapers = Array.isArray(t.papers) ? t.papers : [];
    const normalizedPapers: TrendPaper[] = rawPapers.map((p: any) => {
      const paperId = typeof p.id === 'number' ? p.id : 0;
      if (paperId > 0) {
        uniquePaperIds.add(paperId);
      }
      return {
        id: paperId,
        title: typeof p.title === 'string' ? p.title.trim() : 'Bài báo không rõ tiêu đề',
        abstract_en: typeof p.abstract_en === 'string' ? p.abstract_en.trim() : 'Không có tóm tắt.',
        published: typeof p.published === 'string' ? p.published : null
      };
    });

    const confidenceAvg = typeof t.confidence_avg === 'number' ? Number(t.confidence_avg.toFixed(2)) : 0.0;
    const paperCount = typeof t.paper_count === 'number' ? t.paper_count : normalizedPapers.length;

    const normalizedTopic: Topic = {
      id: typeof t.id === 'number' ? t.id : Math.floor(Math.random() * 1000000),
      name: typeof t.name === 'string' ? t.name.trim() : 'Chủ đề chưa đặt tên',
      description: typeof t.description === 'string' ? t.description.trim() : 'Không có mô tả cho chủ đề này.',
      keywords: Array.isArray(t.keywords) ? t.keywords.map((k: any) => String(k).trim()) : [],
      paper_count: paperCount,
      confidence_avg: confidenceAvg,
      papers: normalizedPapers
    };

    normalizedTopics.push(normalizedTopic);
  }

  // Sort topics by paper_count descending to match backend default
  normalizedTopics.sort((a, b) => b.paper_count - a.paper_count);

  result.topics = normalizedTopics;
  result.topic_count = normalizedTopics.length;
  result.total_papers = uniquePaperIds.size || rawResponse.total_papers || 0;

  // Find the top topic (the one with the highest paper_count)
  if (normalizedTopics.length > 0) {
    result.topTopic = normalizedTopics[0]; // Since it is already sorted by paper_count desc
  }

  return result;
};
