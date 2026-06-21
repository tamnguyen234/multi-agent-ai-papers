import React, { useState } from 'react';
import type { ChatMessage } from '../../types/chat';
import { synthesizeChatMessageAudio } from '../../api/chatApi';
import AudioPlayer from '../AudioPlayer';
import { buildMediaUrl } from '../../utils/mediaUrl';
import { formatDateTime } from '../../utils/formatters';

interface ChatMessageBubbleProps {
  message: ChatMessage;
  /** Callback to update a message's tts_url in parent state */
  onTtsUpdate: (messageId: number, ttsUrl: string) => void;
}

/**
 * Build a playable audio URL from either tts_url or tts_path.
 * - If tts_url is a full http URL  → use as-is
 * - If tts_url is a /static/... path → buildMediaUrl prepends backend origin
 * - Fallback to tts_path if tts_url is null
 */
function resolveAudioUrl(message: ChatMessage): string | null {
  const candidate = message.tts_url ?? message.tts_path;
  return buildMediaUrl(candidate);
}

const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({ message, onTtsUpdate }) => {
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsError, setTtsError] = useState<string | null>(null);

  const isAssistant = message.role === 'assistant';
  const isUser = message.role === 'user';

  // Resolve playable URL using both tts_url and tts_path (prefer tts_url)
  const audioUrl = resolveAudioUrl(message);

  const handleTts = async () => {
    setTtsLoading(true);
    setTtsError(null);
    try {
      const res = await synthesizeChatMessageAudio(message.id);

      // Prefer tts_url from response; fallback to tts_path
      const rawUrl = res.tts_url ?? res.tts_path ?? null;
      if (rawUrl) {
        // buildMediaUrl handles both /static/... paths and full http URLs safely
        const playableUrl = buildMediaUrl(rawUrl);
        if (playableUrl) {
          onTtsUpdate(message.id, playableUrl);
        }
      }
    } catch (err: any) {
      console.error('Error generating audio:', err);
      let errorMsg = 'Không thể tạo audio.';
      if (err && typeof err === 'object') {
        if (err.response?.data?.detail) {
          errorMsg = err.response.data.detail;
        } else if (err.response?.data?.message) {
          errorMsg = err.response.data.message;
        } else if (err.message) {
          errorMsg = err.message;
        }
      }
      setTtsError(errorMsg);
    } finally {
      setTtsLoading(false);
    }
  };

  return (
    <div className={`chat-bubble-row chat-bubble-row--${message.role}`}>
      {/* Avatar */}
      <div className={`chat-avatar chat-avatar--${message.role}`} aria-label={message.role}>
        {isUser ? '👤' : isAssistant ? '🤖' : '⚙️'}
      </div>

      {/* Bubble */}
      <div className={`chat-bubble chat-bubble--${message.role}`}>
        {/* Role label + time */}
        <div className="chat-bubble__meta">
          <span className="chat-bubble__role">
            {isUser ? 'Bạn' : isAssistant ? 'Trợ lý AI' : 'Hệ thống'}
          </span>
          {message.created_at && (
            <span className="chat-bubble__time">{formatDateTime(message.created_at)}</span>
          )}
        </div>

        {/* Content */}
        <div className="chat-bubble__content">{message.content}</div>

        {/* TTS section — only for assistant */}
        {isAssistant && (
          <div className="chat-bubble__tts">
            {audioUrl ? (
              <AudioPlayer
                src={audioUrl}
                title="Nghe câu trả lời"
                className="chat-audio-player"
              />
            ) : (
              <>
                <button
                  className={`btn-tts${ttsLoading ? ' btn-tts--loading' : ''}`}
                  onClick={handleTts}
                  disabled={ttsLoading}
                  title="Chuyển câu trả lời thành giọng nói"
                >
                  {ttsLoading ? (
                    <>
                      <span className="spinner-small" /> Đang tạo audio…
                    </>
                  ) : (
                    '🔊 Nghe câu trả lời'
                  )}
                </button>
                {ttsError && <span className="tts-error">{ttsError}</span>}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessageBubble;
