import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPaperById } from '../api/paperApi';
import {
  getPaperChatSession,
  createChatSession,
  getChatMessages,
  sendChatMessage,
} from '../api/chatApi';
import { getApiErrorMessage } from '../utils/apiError';
import type { Paper } from '../types/paper';
import type { ChatSession, ChatMessage } from '../types/chat';
import ChatMessageBubble from '../components/chat/ChatMessageBubble';
import ChatComposer from '../components/chat/ChatComposer';
import { formatAuthorsShort, formatDate } from '../utils/formatters';
import { buildMediaUrl, externalAbsUrl } from '../utils/mediaUrl';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';

// ───────────────────────────────────────────────────────────────
// Sub-component: Paper context sidebar/panel
// ───────────────────────────────────────────────────────────────
const PaperContextPanel: React.FC<{ paper: Paper }> = ({ paper }) => {
  const pdfUrl = buildMediaUrl(paper.pdf_url || paper.pdf_path);
  const sourceUrl = paper.source_url || externalAbsUrl(paper.external_id);
  const authorsShort = formatAuthorsShort(paper.authors, 2);
  const dateStr = formatDate(paper.published);

  return (
    <aside className="chat-context-panel">
      <div className="chat-context-panel__header">
        <span className="chat-context-panel__icon">📄</span>
        <span className="chat-context-panel__label">Bài báo đang hỏi đáp</span>
      </div>
      <h3 className="chat-context-panel__title">{paper.title}</h3>
      <div className="chat-context-panel__meta">
        {authorsShort && authorsShort !== 'Không rõ tác giả' && (
          <span className="meta-tag">👤 {authorsShort}</span>
        )}
        <span className="meta-tag">📅 {dateStr}</span>
        <span className="meta-tag meta-tag--external">📑 {paper.external_id}</span>
      </div>
      {paper.summary_vi && (
        <p className="chat-context-panel__summary">{paper.summary_vi}</p>
      )}
      <div className="chat-context-panel__actions">
        <Link
          to={`/papers/${paper.id}`}
          className="btn-context-action"
          id="context-paper-detail-link"
        >
          🔍 Xem chi tiết
        </Link>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-context-action"
          id="context-source-link"
        >
          🔗 Nguồn
        </a>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-context-action"
            id="context-pdf-link"
          >
            📄 PDF
          </a>
        )}
      </div>
    </aside>
  );
};

// ───────────────────────────────────────────────────────────────
// Main ChatPage
// ───────────────────────────────────────────────────────────────
export const ChatPage: React.FC = () => {
  const { paperId } = useParams<{ paperId?: string }>();
  const navigate = useNavigate();

  // Data state
  const [paper, setPaper] = useState<Paper | null>(null);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // UI state
  const [initLoading, setInitLoading] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [question, setQuestion] = useState('');

  // Auto-scroll ref
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Scroll when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load paper + session + history
  useEffect(() => {
    if (!paperId) return;

    let cancelled = false;

    const init = async () => {
      setInitLoading(true);
      setInitError(null);
      setPaper(null);
      setSession(null);
      setMessages([]);

      try {
        // 1. Load paper
        const paperData = await getPaperById(paperId);
        if (cancelled) return;
        setPaper(paperData);

        // 2. Get or create chat session
        let chatSession: ChatSession;
        try {
          chatSession = await getPaperChatSession(paperId);
        } catch (err: unknown) {
          const status =
            err && typeof err === 'object' && 'response' in err
              ? (err as { response?: { status?: number } }).response?.status
              : null;
          if (status === 404) {
            // No session yet — create one
            chatSession = await createChatSession(paperId);
          } else {
            throw err;
          }
        }
        if (cancelled) return;
        setSession(chatSession);

        // 3. Load message history
        const history = await getChatMessages(chatSession.id);
        if (cancelled) return;
        setMessages(history);
      } catch (err: unknown) {
        if (cancelled) return;
        const msg = getApiErrorMessage(err, 'Không thể khởi tạo phiên hỏi đáp.');
        setInitError(msg);
      } finally {
        if (!cancelled) setInitLoading(false);
      }
    };

    init();
    return () => { cancelled = true; };
  }, [paperId]);

  // Send message handler
  const handleSend = useCallback(async () => {
    if (!session || !question.trim() || sending) return;

    const q = question.trim();
    setQuestion('');
    setSending(true);
    setSendError(null);

    // Optimistic user message (temp id = -Date.now())
    const tempUserMsg: ChatMessage = {
      id: -Date.now(),
      session_id: session.id,
      role: 'user',
      content: q,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await sendChatMessage({ session_id: session.id, question: q });

      // Replace optimistic + add assistant message
      setMessages((prev) => {
        // Remove the temp message
        const withoutTemp = prev.filter((m) => m.id !== tempUserMsg.id);
        return [...withoutTemp, res.user_message, res.assistant_message];
      });
    } catch (err: unknown) {
      // Remove optimistic message on failure
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
      const msg = getApiErrorMessage(err, 'Gửi câu hỏi thất bại.');
      setSendError(msg);
    } finally {
      setSending(false);
    }
  }, [session, question, sending]);


  // ── No paperId → guide page ──
  if (!paperId) {
    return (
      <EmptyState
        title="Chọn bài báo để hỏi đáp"
        message="Để bắt đầu hỏi đáp, hãy mở danh sách bài báo, xem chi tiết và nhấn nút 'Hỏi đáp với bài báo này'."
        icon="💬"
        actionLabel="📄 Xem danh sách bài báo"
        onAction={() => navigate('/papers')}
      />
    );
  }

  // ── Init loading ──
  if (initLoading) {
    return <LoadingState message="Đang khởi tạo phiên hỏi đáp…" />;
  }

  // ── Init error ──
  if (initError) {
    return (
      <ErrorState
        title="Lỗi khởi tạo"
        message={initError}
        onRetry={() => navigate('/papers')}
        retryLabel="Quay lại danh sách"
      />
    );
  }

  return (
    <div className="chat-page">
      {/* Paper context sidebar */}
      {paper && <PaperContextPanel paper={paper} />}

      {/* Chat workspace */}
      <div className="chat-workspace">
        {/* Chat header */}
        <div className="chat-workspace__header">
          <h2 className="chat-workspace__title">💬 Hỏi đáp</h2>
          {session && (
            <span className="chat-session-badge">Session #{session.id}</span>
          )}
          <Link to="/papers" className="btn-back" style={{ marginLeft: 'auto' }}>
            ← Danh sách
          </Link>
        </div>

        {/* Messages area */}
        <div className="chat-messages" id="chat-messages-container">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <span className="chat-empty__icon">🗨️</span>
              <p>Hãy đặt câu hỏi đầu tiên về bài báo này.</p>
              <p className="chat-empty__hint">
                Ví dụ: "Phương pháp chính của bài báo là gì?", "Kết quả thực nghiệm có gì đáng chú ý?"
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <ChatMessageBubble
                key={msg.id}
                message={msg}
              />
            ))
          )}

          {/* Sending indicator */}
          {sending && (
            <div className="chat-bubble-row chat-bubble-row--assistant">
              <div className="chat-avatar chat-avatar--assistant">🤖</div>
              <div className="chat-bubble chat-bubble--assistant chat-bubble--thinking">
                <div className="chat-typing">
                  <span /><span /><span />
                </div>
                <span className="chat-bubble__role">Trợ lý AI đang xử lý…</span>
              </div>
            </div>
          )}

          {/* Send error */}
          {sendError && (
            <div className="chat-send-error">
              ❌ {sendError}
              <button
                className="chat-send-error__dismiss"
                onClick={() => setSendError(null)}
              >
                ×
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Composer */}
        <div className="chat-composer-wrapper">
          <ChatComposer
            value={question}
            onChange={setQuestion}
            onSubmit={handleSend}
            disabled={sending || !session}
            placeholder={
              session
                ? 'Nhập câu hỏi về bài báo (Enter để gửi, Shift+Enter xuống dòng)…'
                : 'Đang khởi tạo session…'
            }
          />
          <p className="chat-composer__hint">
            Enter gửi · Shift+Enter xuống dòng · Câu trả lời được lưu lại
          </p>
        </div>
      </div>
    </div>
  );
};
