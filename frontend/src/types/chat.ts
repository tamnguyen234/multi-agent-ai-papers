// Types matching backend chat schemas (chat_schema.py)

export interface ChatSession {
  id: number;
  user_id: number;
  paper_id: number;
  created_at: string; // ISO datetime
}

export type ChatMessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: number;
  /** Backend ChatMessageResponse uses session_id (mapped from chat_session_id) */
  session_id: number;
  role: ChatMessageRole;
  content: string;
  tts_path: string | null;
  tts_url: string | null;
  tts_timestamps: unknown | null;
  created_at: string; // ISO datetime
}

/** POST /chat/sessions body */
export interface CreateChatSessionRequest {
  paper_id: number;
}

/** POST /chat/messages body */
export interface SendChatMessageRequest {
  session_id: number;
  question: string;
}

/** POST /chat/messages response */
export interface ChatAskResponse {
  session: ChatSession;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  qa_mode: string;
  sources: unknown[];
}

/** POST /tts/chat-message body */
export interface TTSChatMessageRequest {
  message_id: number;
  voice?: string;
  language?: string;
  speed?: number;
}

/** POST /tts/chat-message response */
export interface TTSChatMessageResponse {
  message_id: number;
  tts_path: string | null;
  tts_url: string | null;
  tts_timestamps: unknown | null;
  duration_seconds: number | null;
  mode: string; // "synthesized" | "existing" | "mock" etc.
}
