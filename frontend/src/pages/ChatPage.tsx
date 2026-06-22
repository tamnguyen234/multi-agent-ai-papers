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
import { FileText, Users, Calendar, Hash, Search, ExternalLink, MessageSquare, Bot, AlertCircle } from 'lucide-react';

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
        <FileText size={16} className="chat-context-panel__icon" />
        <span className="chat-context-panel__label">Active Paper Context</span>
      </div>
      <h3 className="chat-context-panel__title">{paper.title}</h3>
      <div className="chat-context-panel__meta">
        {authorsShort && authorsShort !== 'Không rõ tác giả' && (
          <span className="meta-tag"><Users size={14} className="mr-1" /> {authorsShort}</span>
        )}
        <span className="meta-tag"><Calendar size={14} className="mr-1" /> {dateStr}</span>
        <span className="meta-tag meta-tag--external"><Hash size={14} className="mr-1" /> {paper.external_id}</span>
      </div>
      {paper.abstract_vi && (
        <p className="chat-context-panel__summary">{paper.abstract_vi}</p>
      )}
      <div className="chat-context-panel__actions">
        <Link
          to={`/papers/${paper.id}`}
          className="btn-context-action flex items-center justify-center gap-2"
          id="context-paper-detail-link"
        >
          <Search size={14} /> View Details
        </Link>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-context-action flex items-center justify-center gap-2"
          id="context-source-link"
        >
          <ExternalLink size={14} /> Source
        </a>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-context-action flex items-center justify-center gap-2"
            id="context-pdf-link"
          >
            <FileText size={14} /> PDF
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
        const msg = getApiErrorMessage(err, 'Failed to initialize Q&A session.');
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
      const msg = getApiErrorMessage(err, 'Failed to send message.');
        setSendError(msg);
    } finally {
      setSending(false);
    }
  }, [session, question, sending]);


  // ── No paperId → guide page ──
  if (!paperId) {
    return (
      <EmptyState
        title="Select a paper to start Q&A"
        message="To start a Q&A session, open a paper from the list and click 'Ask Q&A Agent'."
        icon={<MessageSquare size={48} className="text-muted" />}
        actionLabel="View All Papers"
        onAction={() => navigate('/papers')}
      />
    );
  }

  // ── Init loading ──
  if (initLoading) {
    return <LoadingState message="Initializing Q&A session..." />;
  }

  // ── Init error ──
  if (initError) {
    return (
      <ErrorState
        title="Initialization Error"
        message={initError}
        onRetry={() => navigate('/papers')}
        retryLabel="Back to Papers"
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
          <h2 className="chat-workspace__title flex items-center gap-2">
            <MessageSquare size={18} /> Q&A Agent
          </h2>
          {session && (
            <span className="chat-session-badge">Session #{session.id}</span>
          )}
          <Link to="/papers" className="btn-back" style={{ marginLeft: 'auto' }}>
            ← Back to List
          </Link>
        </div>

        {/* Messages area */}
        <div className="chat-messages" id="chat-messages-container">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <span className="chat-empty__icon"><MessageSquare size={32} className="text-muted" /></span>
              <p>Ask your first question about this paper.</p>
              <p className="chat-empty__hint">
                Examples: "What is the main contribution of this paper?", "Can you explain the methodology?"
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
              <div className="chat-avatar chat-avatar--assistant"><Bot size={16} /></div>
              <div className="chat-bubble chat-bubble--assistant chat-bubble--thinking">
                <div className="chat-typing">
                  <span /><span /><span />
                </div>
                <span className="chat-bubble__role">AI is thinking...</span>
              </div>
            </div>
          )}

          {/* Send error */}
          {sendError && (
            <div className="chat-send-error flex items-center gap-2">
              <AlertCircle size={16} /> {sendError}
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
                ? 'Ask a question (Enter to send, Shift+Enter for new line)...'
                : 'Initializing session...'
            }
          />
          <p className="chat-composer__hint">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
};
