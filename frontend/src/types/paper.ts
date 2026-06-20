// Types matching backend PaperResponse schema (paper_schema.py)

export interface AudioAbstract {
  id: number;
  file_path: string;
  audio_url: string | null;
  duration_seconds: number | null;
  paper_timestamps: unknown | null;
  created_at: string; // ISO datetime string
}

export interface Paper {
  id: number;
  arxiv_id: string;
  title: string;
  abstract: string;
  summary: string | null;
  /** Backend returns List[str] but may also be null */
  authors: string[] | null;
  published: string | null; // ISO date "YYYY-MM-DD"
  pdf_path: string | null;
  pdf_url: string | null;
  score: number;
  has_audio: boolean;
  created_at: string; // ISO datetime string
  audio_abstract: AudioAbstract | null;
  audio_abstract_path: string | null;
  audio_abstract_url: string | null;
  audio_duration_seconds: number | null;
}

/** GET /papers returns Paper[] directly (no wrapper) */
export type PapersListResponse = Paper[];
