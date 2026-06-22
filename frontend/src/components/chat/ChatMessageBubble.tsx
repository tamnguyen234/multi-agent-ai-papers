import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '../../types/chat';
import { formatDateTime } from '../../utils/formatters';

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({ message }) => {

  const isAssistant = message.role === 'assistant';
  const isUser = message.role === 'user';

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
        <div className="chat-bubble__content">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default ChatMessageBubble;
