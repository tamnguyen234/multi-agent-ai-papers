import React, { useRef, useEffect } from 'react';

interface ChatComposerProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  placeholder?: string;
}

const ChatComposer: React.FC<ChatComposerProps> = ({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = 'Nhập câu hỏi về bài báo này…',
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter sends (without shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="chat-composer">
      <textarea
        ref={textareaRef}
        id="chat-input"
        className="chat-composer__textarea"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        aria-label="Nhập câu hỏi"
      />
      <button
        id="chat-send-btn"
        className={`chat-composer__send${disabled ? ' chat-composer__send--disabled' : ''}`}
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
        title="Gửi câu hỏi (Enter)"
        aria-label="Gửi"
      >
        {disabled ? <span className="spinner-small" /> : '➤'}
      </button>
    </div>
  );
};

export default ChatComposer;
