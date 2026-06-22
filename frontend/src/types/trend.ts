export interface TrendPaper {
  id: number;
  title: string;
  abstract_en: string;
  published?: string | null;
}

export interface Topic {
  id: number;
  name: string;
  description?: string | null;
  keywords?: string[];
  paper_count: number;
  confidence_avg: number;
  papers: TrendPaper[];
}

export interface TrendAnalyzeResponse {
  mode: string;
  total_papers: number;
  topic_count: number;
  topics: Topic[];
}

export interface TrendHealthResponse {
  status: string;
  agent?: {
    status?: string;
    service?: string;
    mode?: string;
    embedding_model_loaded?: boolean;
    bertopic_available?: boolean;
    [key: string]: any;
  };
}
