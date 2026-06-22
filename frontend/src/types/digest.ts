// Types matching backend DigestResponse schema (digest_schema.py)

export interface DigestPaper {
  id: number;
  external_id: string;
  title: string;
  abstract_en: string;
  abstract_vi: string | null;
  score: number;
  published: string | null; // ISO date string "YYYY-MM-DD"
  has_audio: boolean;
  audio_abstract_path: string | null;
  audio_abstract_url: string | null;
  audio_duration_seconds: number | null;
}

export interface DigestEntry {
  rank_position: number;
  paper: DigestPaper;
}

export interface DigestResponse {
  id: number;
  digest_date: string; // ISO date string "YYYY-MM-DD"
  papers: DigestEntry[];
}

export interface RunDigestJobResponse {
  message: string;
  digest_id?: number;
  total_papers?: number;
}
