import client from './client';
import type {
  ChatSession,
  ChatMessage,
  ChatAskResponse,
  TTSChatMessageResponse,
  SendChatMessageRequest,
} from '../types/chat';

/**
 * Get existing chat session for a user+paper pair.
 * GET /api/v1/chat/papers/{paperId}/session
 * Returns 404 if no session exists yet.
 */
export async function getPaperChatSession(paperId: number | string): Promise<ChatSession> {
  const response = await client.get<ChatSession>(`/chat/papers/${paperId}/session`);
  return response.data;
}

/**
 * Create a new chat session for a paper (or return existing one).
 * POST /api/v1/chat/sessions
 */
export async function createChatSession(paperId: number | string): Promise<ChatSession> {
  const response = await client.post<ChatSession>('/chat/sessions', {
    paper_id: Number(paperId),
  });
  return response.data;
}

/**
 * Get all messages in a session (chronological order).
 * GET /api/v1/chat/sessions/{sessionId}/messages
 */
export async function getChatMessages(sessionId: number | string): Promise<ChatMessage[]> {
  const response = await client.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
  return response.data;
}

/**
 * Send a user question and get assistant answer.
 * POST /api/v1/chat/messages
 * Payload: { session_id, question }
 */
export async function sendChatMessage(payload: SendChatMessageRequest): Promise<ChatAskResponse> {
  const response = await client.post<ChatAskResponse>('/chat/messages', payload, {
    timeout: 620000, // Agent2-style Ollama chat can run for up to ~600s
  });
  return response.data;
}

/**
 * Synthesize TTS audio for an assistant chat message.
 * POST /api/v1/tts/chat-message
 * Payload: { message_id, voice?, language?, speed? }
 */
export async function synthesizeChatMessageAudio(
  messageId: number | string,
  opts?: { voice?: string; language?: string; speed?: number }
): Promise<TTSChatMessageResponse> {
  const response = await client.post<TTSChatMessageResponse>('/tts/chat-message', {
    message_id: Number(messageId),
    voice: opts?.voice ?? 'vi_female',
    language: opts?.language ?? 'vi',
    speed: opts?.speed ?? 1.0,
  }, {
    timeout: 300000, // 300s for TTS synthesis execution
  });
  return response.data;
}
